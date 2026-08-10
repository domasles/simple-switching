import os

from pathlib import Path

from textual.widgets import Button, Header, Footer, Input, Static
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen


class PathPromptScreen(Screen):
    """Prompts the user for executable paths when auto-discovery fails."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container():
            with Vertical():
                yield Static("[bold yellow]Missing Browser Executable[/bold yellow]\n")
                yield Static("Enter executable path for selected browser:", id="prompt-label")
                yield Input(placeholder="/usr/bin/chromium", id="input-exec-path")
                yield Button("Submit", variant="primary", id="btn-submit-path")

        yield Footer()

    def on_screen_resume(self) -> None:
        selected_profiles = getattr(self.app, "selected_profiles", [])
        missing_paths = [p for p in selected_profiles if not getattr(p, "executable_path", None)]

        if missing_paths:
            profile = missing_paths[0]
            label_widget = self.query_one("#prompt-label", Static)
            label_widget.update(f"Enter executable path for [bold cyan]{profile.label}[/bold cyan]:")

        else:
            action_mode = getattr(self.app, "action_mode", "install")

            if action_mode == "uninstall":
                self.app.push_screen("uninstall_progress")

            else:
                self.app.push_screen("install_progress")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit-path":
            input_widget = self.query_one("#input-exec-path", Input)
            entered_path = input_widget.value.strip()

            if not entered_path:
                self.notify("Please specify a valid path.", severity="warning")
                return

            path_obj = Path(entered_path)

            if not path_obj.is_file() or not os.access(path_obj, os.X_OK):
                self.notify("Executable path does not exist or is not executable.", severity="error")
                return

            selected_profiles = getattr(self.app, "selected_profiles", [])
            missing_paths = [p for p in selected_profiles if not getattr(p, "executable_path", None)]

            if missing_paths:
                missing_paths[0].executable_path = entered_path
                input_widget.value = ""

            remaining = [p for p in selected_profiles if not getattr(p, "executable_path", None)]

            if remaining:
                label_widget = self.query_one("#prompt-label", Static)
                label_widget.update(f"Enter executable path for [bold cyan]{remaining[0].label}[/bold cyan]:")

            else:
                action_mode = getattr(self.app, "action_mode", "install")

                if action_mode == "uninstall":
                    self.app.push_screen("uninstall_progress")

                else:
                    self.app.push_screen("install_progress")
