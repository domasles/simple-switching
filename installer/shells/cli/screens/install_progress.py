import subprocess
import json
import time

from pathlib import Path

from textual.widgets import Header, Footer, Log, ProgressBar, Static
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen

from installer.core.policy_installer import deploy_browser_policy, generate_update_manifest_xml
from installer.core.preferences_editor import inject_extension_shortcut
from installer.core.process_manager import terminate_browser_processes


class InstallProgressScreen(Screen):
    """Performs background tasks while updating progress bars."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container():
            with Vertical():
                yield Static("[bold green]Installation in Progress...[/bold green]\n")
                yield ProgressBar(id="progress-bar", total=100)
                yield Log(id="activity-log", highlight=True)

        yield Footer()

    def on_mount(self) -> None:
        """Triggers the async background execution worker when screen loads."""
        self.run_worker(self._run_installation_pipeline, thread=True)

    def _wait_for_extension_extraction(self, profile, extension_id: str) -> bool:
        """Launches browser autonomously to force immediate policy extension download & extraction."""

        profile_path = getattr(profile, "profile_path", None)

        if not profile_path:
            return False

        ext_dir = profile_path / "Extensions" / extension_id
        exec_path = getattr(profile, "executable_path", None) or "chromium"

        user_data_dir = profile_path.parent
        profile_directory = profile_path.name

        cmd = [
            exec_path,
            "about:blank"
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except Exception:
            return False

        # Poll until manifest.json is present and completely written to disk
        while True:
            extracted = False

            if ext_dir.exists():
                for manifest_path in ext_dir.glob("**/manifest.json"):
                    if manifest_path.is_file() and manifest_path.stat().st_size > 0:
                        try:
                            with open(manifest_path, "r", encoding="utf-8") as f:
                                json.load(f)

                            extracted = True
                            break

                        except (json.JSONDecodeError, OSError):
                            pass

            if extracted:
                break

            time.sleep(0.2)

        time.sleep(0.5)
        proc.terminate()

        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        return True

    def _run_installation_pipeline(self) -> None:
        log = self.query_one("#activity-log", Log)
        progress = self.query_one("#progress-bar", ProgressBar)

        app = self.app
        config = app.app_config
        selected_profiles = getattr(app, "selected_profiles", [])

        results = {"success": [], "skipped": []}

        log.write_line("Step 1/4: Closing target browser processes...")

        terminate_browser_processes(selected_profiles)
        progress.advance(20)

        log.write_line("Step 2/4: Hosting local CRX server & deploying policies...")
        app.server.start()

        update_xml_url = app.server.get_url("update.xml")
        extension_url = app.server.get_url("extension.crx")

        manifest_content = generate_update_manifest_xml(config.extension_id, extension_url)
        (app.cache_dir / "update.xml").write_text(manifest_content, encoding="utf-8")

        eligible_profiles = deploy_browser_policy(selected_profiles, config, update_xml_url, extension_url)
        eligible_set = set(eligible_profiles)

        for profile in selected_profiles:
            if profile not in eligible_set:
                log.write_line(f"  Policy deployment failed for {profile.label}")
                results["skipped"].append(profile.label)

        progress.advance(25)

        log.write_line("Step 3/4: Triggering background extension extraction...")

        for profile in eligible_profiles:
            extracted = self._wait_for_extension_extraction(profile, config.extension_id)

            if extracted:
                log.write_line(f"  Extracted for {profile.label}")

            else:
                log.write_line(f"  Extraction failed for {profile.label}")

        progress.advance(30)

        log.write_line("Step 4/4: Injecting shortcut keys into profile Preferences...")

        for profile in eligible_profiles:
            success = inject_extension_shortcut(profile, config)

            if success:
                log.write_line(f"  Configured {profile.label}")
                results["success"].append(profile.label)

            else:
                log.write_line(f"  Failed to modify {profile.label}")
                results["skipped"].append(profile.label)

        progress.advance(25)
        app.installation_results = results

        self.app.call_from_thread(self.app.push_screen, "finish")
