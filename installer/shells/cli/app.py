import argparse
import sys

from pathlib import Path
from typing import List

from textual.app import App

from core.models import AppConfig, BrowserProfile
from core.discovery import scan_browser_profiles
from core.config_loader import load_app_config
from core.local_server import LocalServer

from shells.cli.screens.uninstall_progress import UninstallProgressScreen
from shells.cli.screens.download_progress import DownloadProgressScreen
from shells.cli.screens.install_progress import InstallProgressScreen
from shells.cli.screens.prompt_path import PathPromptScreen
from shells.cli.screens.selector import SelectorScreen
from shells.cli.screens.welcome import WelcomeScreen
from shells.cli.screens.finish import FinishScreen


def get_bundle_dir() -> Path:
    """Returns base directory containing app assets."""

    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    return Path(__file__).resolve().parent.parent.parent


class ExtensionInstaller(App):
    """Main Textual Application Controller."""

    CSS_PATH = "assets/style.css"

    SCREENS = {
        "download_progress": DownloadProgressScreen,
        "welcome": WelcomeScreen,
        "selector": SelectorScreen,
        "prompt_path": PathPromptScreen,
        "progress": InstallProgressScreen,
        "uninstall_progress": UninstallProgressScreen,
        "finish": FinishScreen,
    }

    def __init__(self, config_path: Path, cache_dir: Path, local_crx_path: Path = None, **kwargs):
        super().__init__(**kwargs)

        self.config_path = config_path
        self.cache_dir = cache_dir
        self.local_crx_path = local_crx_path
        self.needs_download = local_crx_path is None

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.app_config: AppConfig = load_app_config(self.config_path)
        self.discovered_profiles: List[BrowserProfile] = []
        self.selected_profiles: List[BrowserProfile] = []
        self.action_mode: str = "install"
        self.installation_results = {"success": [], "skipped": []}

        self.server = LocalServer(serve_dir=self.cache_dir)

    def _prepare_local_extension_if_needed(self):
        """Copy local CRX to cache if --local-path provided."""

        if self.local_crx_path:
            import shutil

            dest = self.cache_dir / self.app_config.extension_filename
            shutil.copy2(self.local_crx_path, dest)

    def on_mount(self) -> None:
        self.discovered_profiles = scan_browser_profiles(self.app_config)

        if self.needs_download and self.app_config.remote_release_vendor:
            self.push_screen("download_progress")

        else:
            self._prepare_local_extension_if_needed()
            self.push_screen("welcome")

    def on_unmount(self) -> None:
        self.server.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extension Installer")

    parser.add_argument(
        "--local-path",
        type=Path,
        help="Path to local .crx file to use instead of downloading"
    )

    args = parser.parse_args()
    config_path = get_bundle_dir() / "config" / "config.json"
    cache_dir = Path.home() / "Downloads" / "cache"

    app = ExtensionInstaller(
        config_path=config_path,
        cache_dir=cache_dir,
        local_crx_path=args.local_path
    )

    app.run()
