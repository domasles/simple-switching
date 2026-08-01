from textual.widgets import Header, Footer, Log, ProgressBar, Static
from textual.containers import Container, Vertical
from textual.app import ComposeResult
from textual.screen import Screen

from installer.core.download import download_extension


class DownloadProgressScreen(Screen):
    """Shows download progress for remote CRX."""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container():
            with Vertical():
                yield Static("[bold blue]Downloading Extension...[/bold blue]\n")
                yield ProgressBar(id="dl-progress", total=100, show_eta=False)
                yield Log(id="dl-log", highlight=True)

        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._download_worker, thread=True)

    def _download_worker(self) -> None:
        log = self.query_one("#dl-log", Log)
        progress = self.query_one("#dl-progress", ProgressBar)

        def progress_cb(downloaded: int, total: int):
            if total > 0:
                pct = int((downloaded / total) * 100)
                self.app.call_from_thread(progress.update, progress=pct)

            self.app.call_from_thread(log.write_line, f"Downloaded {downloaded}/{total} bytes")

        try:
            log.write_line(f"Fetching {self.app.app_config.extension_filename} from GitHub...")

            crx_path = download_extension(
                self.app.app_config,
                self.app.cache_dir,
                progress_callback=progress_cb
            )

            log.write_line(f"Saved to {crx_path}")
            self.app.call_from_thread(self._on_complete)

        except Exception as e:
            log.write_line(f"Download failed: {e}")
            self.app.call_from_thread(self._on_failure, str(e))

    def _on_complete(self) -> None:
        self.app.push_screen("welcome")

    def _on_failure(self, error_msg: str) -> None:
        """Set failure results and show finish screen."""

        self.app.installation_results = {
            "success": [],
            "skipped": [f"Download failed: {error_msg}"]
        }

        self.app.action_mode = "install"
        self.app.push_screen("finish")
