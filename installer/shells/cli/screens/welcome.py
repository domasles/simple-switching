import sys

from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Header, Footer, Static
from textual.app import ComposeResult
from textual.screen import Screen


class WelcomeScreen(Screen):
    """Displays tool information and system details."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="welcome-container"):
            with Vertical():
                yield Static(
                    "[bold green]Simple Switching Installer[/bold green]",
                    classes="title"
                )

                yield Static(
                    "This tool will install the extension and inject "
                    "custom keyboard shortcuts into your browser profiles.\n"
                )

                yield Static(f"[bold]Detected OS Platform:[/bold] [cyan]{sys.platform}[/cyan]\n")

                with Horizontal():
                    yield Button("Begin Setup", variant="primary", id="btn-install")
                    yield Button("Uninstall Extension", variant="warning", id="btn-uninstall")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-install":
            self.app.action_mode = "install"
            self.app.push_screen("selector")

        elif event.button.id == "btn-uninstall":
            self.app.action_mode = "uninstall"
            self.app.push_screen("selector")
