import subprocess
import time
import sys

from pathlib import Path

from textual.widgets import Header, Footer, Log, ProgressBar, Static
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen

from core.uninstaller import remove_browser_policies, remove_extension_directory
from core.process_manager import terminate_browser_processes
from core.discovery import check_extension_dir
from core.id_computer import get_extension_id


class UninstallProgressScreen(Screen):
    """Performs uninstallation background tasks while updating progress bars."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container():
            with Vertical():
                yield Static("[bold red]Uninstallation in Progress...[/bold red]\n")
                yield ProgressBar(id="progress-bar", total=100)
                yield Log(id="activity-log", highlight=True)

        yield Footer()

    def on_mount(self) -> None:
        """Triggers worker when screen mounts."""
        self.run_worker(self._run_uninstallation_pipeline, thread=True)

    def _flush_browser_state(self, profile) -> None:
        """Launches browser briefly to force syncing of applied changes."""

        exec_path = getattr(profile, "executable_path", None) or "chromium"

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

            time.sleep(1.5)
            proc.terminate()

            try:
                proc.wait(timeout=3)

            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        except Exception:
            pass

    def _run_uninstallation_pipeline(self) -> None:
        log = self.query_one("#activity-log", Log)
        progress = self.query_one("#progress-bar", ProgressBar)

        app = self.app
        config = app.app_config
        cache_dir = app.cache_dir

        raw_selected = getattr(app, "selected_profiles", [])
        extension_id = get_extension_id(cache_dir, config)

        results = {"success": [], "skipped": []}

        # Pre-uninstall filter
        selected_profiles = []

        for profile in raw_selected:
            profile_path = getattr(profile, "profile_path", None)
            extension_dir = Path(profile_path / "Extensions" / extension_id) if profile_path else None

            if extension_dir and check_extension_dir(extension_dir):
                selected_profiles.append(profile)

            else:
                results["success"].append(profile.label)

        if not selected_profiles:
            app.installation_results = results
            self.app.call_from_thread(self.app.push_screen, "finish")

            return

        log.write_line("Step 1/4: Closing target browser processes...")

        terminate_browser_processes(selected_profiles)
        progress.advance(25)

        if sys.platform.startswith("linux"):
            log.write_line("Step 2/4: Removing enterprise policy files...")
            eligible_profiles = remove_browser_policies(selected_profiles, config)

            eligible_set = set(eligible_profiles)

            for profile in selected_profiles:
                if profile not in eligible_set:
                    log.write_line(f"  Policy removal failed for {profile.label}")
                    results["skipped"].append(profile.label)

            progress.advance(25)

            log.write_line("Step 3/4: Removing extension directory...")

            for profile in eligible_profiles:
                dir_removed = remove_extension_directory(profile, extension_id)

                if dir_removed:
                    log.write_line(f"  Uninstalled for {profile.label}")
                    results["success"].append(profile.label)

                else:
                    log.write_line(f"  Failed to fully clean {profile.label}")
                    results["skipped"].append(profile.label)

            progress.advance(25)

            log.write_line("Step 4/4: Flushing browser policy state...")

            for profile in eligible_profiles:
                self._flush_browser_state(profile)

            progress.advance(25)

        else:
            # Windows/macOS: Just remove extension directory
            log.write_line("Step 2/4: Removing extension directory...")

            for profile in selected_profiles:
                dir_removed = remove_extension_directory(profile, extension_id)

                if dir_removed:
                    log.write_line(f"  Uninstalled for {profile.label}")
                    results["success"].append(profile.label)

                else:
                    log.write_line(f"  Failed to fully clean {profile.label}")
                    results["skipped"].append(profile.label)

            progress.advance(50)

        app.installation_results = results

        self.app.call_from_thread(self.app.push_screen, "finish")
