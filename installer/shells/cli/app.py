from pathlib import Path
from typing import List

from textual.app import App

from installer.core.models import AppConfig, BrowserProfile
from installer.core.discovery import scan_browser_profiles
from installer.core.config_loader import load_app_config
from installer.core.local_server import LocalServer

from installer.shells.cli.screens.uninstall_progress import UninstallProgressScreen
from installer.shells.cli.screens.install_progress import InstallProgressScreen
from installer.shells.cli.screens.prompt_path import PathPromptScreen
from installer.shells.cli.screens.selector import SelectorScreen
from installer.shells.cli.screens.welcome import WelcomeScreen
from installer.shells.cli.screens.finish import FinishScreen


class ExtensionInstaller(App):
    """Main Textual Application Controller."""

    CSS = """
    Container {
        padding: 1 2;
    }
    .title {
        margin-bottom: 1;
    }
    Button {
        margin-top: 1;
        margin-right: 1;
    }
    Button:focus {
        text-style: bold;
        outline: hkey white;
    }
    """

    SCREENS = {
        "welcome": WelcomeScreen,
        "selector": SelectorScreen,
        "prompt_path": PathPromptScreen,
        "progress": InstallProgressScreen,
        "uninstall_progress": UninstallProgressScreen,
        "finish": FinishScreen,
    }

    def __init__(self, config_path: Path, cache_dir: Path, **kwargs):
        super().__init__(**kwargs)

        self.config_path = config_path
        self.cache_dir = cache_dir

        self.app_config: AppConfig = load_app_config(self.config_path)
        self.discovered_profiles: List[BrowserProfile] = []
        self.selected_profiles: List[BrowserProfile] = []
        self.action_mode: str = "install"
        self.installation_results = {"success": [], "skipped": []}

        self.server = LocalServer(serve_dir=self.cache_dir)

    def on_mount(self) -> None:
        self.discovered_profiles = scan_browser_profiles(self.app_config)
        self.push_screen("welcome")

    def on_unmount(self) -> None:
        self.server.stop()


if __name__ == "__main__":
    app = ExtensionInstaller(
        config_path=Path("installer/config/browsers.json"),
        cache_dir=Path("installer/cache")
    )

    app.run()
