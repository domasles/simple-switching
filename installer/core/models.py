import sys

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class PlatformBrowserConfig:
    """Holds OS-specific metadata for a single browser."""

    config_path: str
    executables: List[str] = field(default_factory=list)
    policy_dir: Optional[str] = None  # Linux managed policy directory


@dataclass
class BrowserDefinition:
    """Holds browser metadata for the current platform."""

    key: str
    display_name: str
    linux: Optional[PlatformBrowserConfig] = None

    def get_current_platform_config(self) -> Optional[PlatformBrowserConfig]:
        """Returns the platform-specific config for the host OS."""

        if sys.platform.startswith("linux"):
            return self.linux
        return None


@dataclass
class AppConfig:
    """Master application configuration parsed from browsers.json."""

    extension_filename: str
    browsers: Dict[str, BrowserDefinition]
    shortcut_map: Dict[str, str]
    remote_release_vendor: Optional[str] = None
    remote_release_repo: Optional[str] = None
    remote_release_tag: Optional[str] = None
    remote_download_url: Optional[str] = None


@dataclass(unsafe_hash=True)
class BrowserProfile:
    """Represents a discovered browser profile on the host filesystem."""

    browser_key: str
    browser_display_name: str
    profile_name: str
    profile_path: Path
    preferences_path: Path
    executables: List[str] = field(hash=False)
    executable_path: Optional[str] = field(default=None, hash=False)

    @property
    def label(self) -> str:
        """User-friendly display label for UI prompts."""
        return f"{self.browser_display_name} - {self.profile_name}"
