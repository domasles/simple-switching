import sys

from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Header, Footer, Static
from textual.app import ComposeResult
from textual.screen import Screen

from core.privileges import is_admin


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
                    "This tool will configure enterprise force-install policies and inject "
                    "custom keyboard shortcuts into your browser profiles.\n"
                )

                yield Static(f"[bold]Detected OS Platform:[/bold] [cyan]{sys.platform}[/cyan]\n")

                has_privileges = is_admin()

                if has_privileges:
                    if sys.platform == "win32":
                        yield Static("[bold]Privilege Status:[/bold] [bold green]Administrator[/bold green]\n")

                    if sys.platform == "darwin":
                        yield Static("[bold]Privilege Status:[/bold] [bold green]Root[/bold green]\n")

                    with Horizontal():
                        yield Button("Begin Setup", variant="primary", id="btn-install")
                        yield Button("Uninstall Extension", variant="warning", id="btn-uninstall")

                else:
                    if sys.platform == "win32":
                        yield Static(
                            "[bold red]Elevation Required:[/bold red]\n"
                            "[yellow]Writing system policies to HKEY_LOCAL_MACHINE requires running this terminal as Administrator.[/yellow]\n"
                            "Please restart your command prompt or PowerShell with 'Run as Administrator'.\n"
                        )

                    elif sys.platform == "darwin":
                        yield Static(
                            "[bold red]Elevation Required:[/bold red]\n"
                            "[yellow]Writing policy plists to /Library/Preferences requires root privileges.[/yellow]\n"
                            "Please relaunch the installer using 'sudo'.\n"
                        )

                    yield Button("Exit Installer", variant="error", id="btn-exit")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-install":
            self.app.action_mode = "install"
            self.app.push_screen("selector")

        elif event.button.id == "btn-uninstall":
            self.app.action_mode = "uninstall"
            self.app.push_screen("selector")

        elif event.button.id == "btn-exit":
            self.app.exit()
