from textual.widgets import Header, Footer, Log, ProgressBar, Static
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen

from installer.core.uninstaller import remove_browser_policies, remove_extension_directory
from installer.core.process_manager import terminate_browser_processes


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

    def _run_uninstallation_pipeline(self) -> None:
        log = self.query_one("#activity-log", Log)
        progress = self.query_one("#progress-bar", ProgressBar)

        app = self.app
        config = app.app_config
        selected_profiles = getattr(app, "selected_profiles", [])

        results = {"success": [], "skipped": []}

        log.write_line("Step 1/3: Closing target browser processes...")

        terminate_browser_processes(selected_profiles)
        progress.advance(33)

        log.write_line("Step 2/3: Removing enterprise policy files...")
        eligible_profiles = remove_browser_policies(selected_profiles, config)

        eligible_set = set(eligible_profiles)

        for profile in selected_profiles:
            if profile not in eligible_set:
                log.write_line(f"  Policy removal failed for {profile.label}")
                results["skipped"].append(profile.label)

        progress.advance(33)

        log.write_line("Step 3/3: Removing extension files and preference shortcuts...")

        for profile in eligible_profiles:
            dir_removed = remove_extension_directory(profile, config)

            if dir_removed:
                log.write_line(f"  Uninstalled for {profile.label}")
                results["success"].append(profile.label)

            else:
                log.write_line(f"  Failed to fully clean {profile.label}")
                results["skipped"].append(profile.label)

        progress.advance(34)
        app.installation_results = results

        self.app.call_from_thread(self.app.push_screen, "finish")
