import subprocess
import time
import sys

from pathlib import Path

from textual.widgets import Header, Footer, Log, ProgressBar, Static
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen

from core.policy_installer import deploy_browser_policy, generate_update_manifest_xml
from core.preferences_editor import inject_extension_shortcut
from core.process_manager import terminate_browser_processes
from core.discovery import check_extension_dir
from core.id_computer import get_extension_id


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

    def _wait_for_extension_extraction(self, profile, extension_id: str, profile_path: Path, extension_dir: Path) -> bool:
        """Launches browser autonomously to force immediate policy extension download & extraction."""

        if not profile_path:
            return False

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
            if check_extension_dir(extension_dir):
                break

            time.sleep(0.2)

        proc.terminate()

        try:
            proc.wait(timeout=3)

        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        return True

    def _show_manual_install_instructions(self, extracted_dir: Path) -> None:
        """Shows instructions for manual installation."""
        log = self.query_one("#activity-log", Log)
        
        instructions = f"""
[bold]Manual Installation Required[/bold]

For Windows/macOS, the extension must be installed manually:

1. Open Chrome/Chromium/Edge/Brave
2. Navigate to chrome://extensions
3. Enable "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Select the extracted folder: {extracted_dir}
6. Click "Allow" if prompted

Once installed, the extension will appear in your browser.
"""
        log.write_line(instructions)

    def _run_installation_pipeline(self) -> None:
        log = self.query_one("#activity-log", Log)
        progress = self.query_one("#progress-bar", ProgressBar)

        app = self.app
        config = app.app_config
        cache_dir = app.cache_dir

        raw_selected = getattr(app, "selected_profiles", [])
        extension_id = get_extension_id(cache_dir, config)

        results = {"success": [], "skipped": []}

        # Pre-install filter
        selected_profiles = []

        for profile in raw_selected:
            profile_path = getattr(profile, "profile_path", None)
            extension_dir = Path(profile_path / "Extensions" / extension_id) if profile_path else None

            if extension_dir and check_extension_dir(extension_dir):
                results["success"].append(profile.label)

            else:
                selected_profiles.append(profile)

        if not selected_profiles:
            app.installation_results = results
            self.app.call_from_thread(self.app.push_screen, "finish")

            return

        log.write_line("Step 1/4: Closing target browser processes...")

        terminate_browser_processes(selected_profiles)
        progress.advance(20)

        if sys.platform.startswith("linux"):
            log.write_line("Step 2/4: Hosting local CRX server & deploying policies...")
            app.server.start()

            update_xml_url = app.server.get_url("update.xml")
            extension_url = app.server.get_url(config.extension_filename)

            manifest_content = generate_update_manifest_xml(extension_id, extension_url)
            (app.cache_dir / "update.xml").write_text(manifest_content, encoding="utf-8")

            eligible_profiles = deploy_browser_policy(selected_profiles, extension_id, config, update_xml_url)
            eligible_set = set(eligible_profiles)

            for profile in selected_profiles:
                if profile not in eligible_set:
                    log.write_line(f"  Policy deployment failed for {profile.label}")
                    results["skipped"].append(profile.label)

            progress.advance(25)

            log.write_line("Step 3/4: Triggering background extension extraction...")

            for profile in eligible_profiles:
                profile_path = Path(getattr(profile, "profile_path", None))
                extension_dir = Path(profile_path / "Extensions" / extension_id)

                extracted = self._wait_for_extension_extraction(profile, extension_id, profile_path, extension_dir)

                if extracted:
                    log.write_line(f"  Extracted for {profile.label}")

                else:
                    log.write_line(f"  Extraction failed for {profile.label}")

            progress.advance(30)

            log.write_line("Step 4/4: Injecting shortcut keys into profile Preferences...")

            for profile in eligible_profiles:
                success = inject_extension_shortcut(profile, extension_id, config)

                if success:
                    log.write_line(f"  Configured {profile.label}")
                    results["success"].append(profile.label)

                else:
                    log.write_line(f"  Failed to modify {profile.label}")
                    results["skipped"].append(profile.label)

        else:
            # Windows/macOS: Manual installation flow
            log.write_line("Step 2/4: Preparing for manual installation...")

            # Show instructions for manual installation
            extracted_dir = cache_dir / "extracted"
            self._show_manual_install_instructions(extracted_dir)
            progress.advance(25)

            log.write_line("Step 3/4: Launching browser to chrome://extensions...")

            # Launch browser to chrome://extensions
            for profile in selected_profiles:
                exec_path = getattr(profile, "executable_path", None) or "chromium"

                try:
                    subprocess.Popen(
                        [exec_path, "chrome://extensions"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                except Exception:
                    pass

            progress.advance(20)

            log.write_line("Step 4/4: Monitoring for extension installation...")

            # Monitor for extension directory creation
            for profile in selected_profiles:
                profile_path = Path(getattr(profile, "profile_path", None))
                extension_dir = Path(profile_path / "Extensions" / extension_id)

                # Wait for extension to be installed
                for _ in range(60):
                    if check_extension_dir(extension_dir):
                        log.write_line(f"  Extension detected for {profile.label}")
                        break

                    time.sleep(1)

                else:
                    log.write_line(f"  Extension not detected for {profile.label}")
                    results["skipped"].append(profile.label)
                    continue

                # Close browser before modifying Preferences
                terminate_browser_processes([profile])
                time.sleep(1)

                success = inject_extension_shortcut(profile, extension_id, config)

                if success:
                    log.write_line(f"  Configured {profile.label}")
                    results["success"].append(profile.label)

                else:
                    log.write_line(f"  Failed to modify {profile.label}")
                    results["skipped"].append(profile.label)

            progress.advance(35)

        app.installation_results = results

        self.app.call_from_thread(self.app.push_screen, "finish")
