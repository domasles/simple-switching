from typing import List

from textual.widgets import Button, Header, Footer, SelectionList, Static
from textual.widgets.selection_list import Selection
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen

from core.models import BrowserProfile


class SelectorScreen(Screen):
    """Allows the user to multi-select detected browser profiles."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container():
            with Vertical():
                yield Static("[bold green]Select Target Profiles[/bold green]\n")
                yield Static("Choose which browser profiles to target:\n", id="selector-description")
                yield SelectionList[BrowserProfile](id="profile-list")
                yield Button("Proceed", variant="primary", id="btn-submit")

        yield Footer()

    def on_screen_resume(self) -> None:
        """Populates the selection list dynamically whenever screen gains focus."""

        action_mode = getattr(self.app, "action_mode", "install")
        btn = self.query_one("#btn-submit", Button)

        if action_mode == "uninstall":
            btn.label = "Proceed to Uninstallation"
            btn.variant = "warning"

        else:
            btn.label = "Proceed to Installation"
            btn.variant = "primary"

        selection_list = self.query_one("#profile-list", SelectionList)
        selection_list.clear_options()
        profiles: List[BrowserProfile] = getattr(self.app, "discovered_profiles", [])

        options = [
            Selection(profile.label, profile, initial_state=True)
            for profile in profiles
        ]

        selection_list.add_options(options)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            selection_list = self.query_one("#profile-list", SelectionList)
            selected_profiles = selection_list.selected

            if not selected_profiles:
                self.notify("Please select at least one browser profile.", severity="warning")
                return

            self.app.selected_profiles = selected_profiles
            action_mode = getattr(self.app, "action_mode", "install")

            if action_mode == "uninstall":
                self.app.push_screen("uninstall_progress")

            else:
                missing_paths = [p for p in selected_profiles if not getattr(p, "executable_path", None)]

                if missing_paths:
                    self.app.push_screen("prompt_path")

                else:
                    self.app.push_screen("install_progress")
