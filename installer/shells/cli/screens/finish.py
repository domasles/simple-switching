from textual.widgets import Button, Header, Footer, Static, DataTable
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen


class FinishScreen(Screen):
    """Displays completion summary."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container():
            with Vertical():
                yield Static("", id="finish-title")
                yield DataTable(id="summary-table")
                yield Button("Exit Installer", variant="success", id="btn-exit")

        yield Footer()

    def on_screen_resume(self) -> None:
        title_widget = self.query_one("#finish-title", Static)
        table = self.query_one("#summary-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Target Profile", "Status")

        results = getattr(self.app, "installation_results", {"success": [], "skipped": []})
        action_mode = getattr(self.app, "action_mode", "install")

        if action_mode == "uninstall":
            if not results.get("skipped"):
                title_widget.update("[bold green]Uninstallation Complete![/bold green]\n")

            elif not results.get("success"):
                title_widget.update("[bold red]Uninstallation Failed![/bold red]\n")

            else:
                title_widget.update("[bold yellow]Uninstallation Completed with Warnings![/bold yellow]\n")

            for label in results.get("success", []):
                table.add_row(label, "[green]Uninstalled[/green]")

            for label in results.get("skipped", []):
                table.add_row(label, "[red]Skipped or Failed[/red]")

        else:
            if not results.get("skipped"):
                title_widget.update("[bold green]Installation Complete![/bold green]\n")

            elif not results.get("success"):
                title_widget.update("[bold red]Installation Failed![/bold red]\n")

            else:
                title_widget.update("[bold yellow]Installation Completed with Warnings![/bold yellow]\n")

            for label in results.get("success", []):
                table.add_row(label, "[green]Installed and Configured[/green]")

            for label in results.get("skipped", []):
                table.add_row(label, "[red]Skipped or Failed[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-exit":
            self.app.exit()
