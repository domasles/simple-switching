import sys

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class PlatformBrowserConfig:
    """Holds OS-specific metadata for a single browser."""

    base_path: str
    executables: List[str] = field(default_factory=list)
    policy_key: Optional[str] = None     # Windows Registry path
    policy_bundle: Optional[str] = None  # macOS plist bundle ID
    policy_dir: Optional[str] = None     # Linux managed policy directory


@dataclass
class BrowserDefinition:
    """Holds browser metadata across all supported operating systems."""

    key: str
    display_name: str
    windows: Optional[PlatformBrowserConfig] = None
    macos: Optional[PlatformBrowserConfig] = None
    linux: Optional[PlatformBrowserConfig] = None

    def get_current_platform_config(self) -> Optional[PlatformBrowserConfig]:
        """Returns the platform-specific config for the host OS."""

        if sys.platform == "win32":
            return self.windows
        elif sys.platform == "darwin":
            return self.macos
        elif sys.platform.startswith("linux"):
            return self.linux
        return None


@dataclass
class AppConfig:
    """Master application configuration parsed from browsers.json."""

    extension_id: str
    default_shortcut: str
    browsers: Dict[str, BrowserDefinition]
    shortcut_map: Dict[str, str]


@dataclass
class BrowserProfile:
    """Represents a discovered browser profile on the host filesystem."""

    browser_key: str
    browser_display_name: str
    profile_name: str
    profile_path: Path
    preferences_path: Path
    executables: List[str]

    @property
    def label(self) -> str:
        """User-friendly display label for UI prompts."""
        return f"{self.browser_display_name} - {self.profile_name}"
