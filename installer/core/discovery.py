import shutil
import json
import sys
import os

from typing import List, Optional
from pathlib import Path

from installer.core.config_loader import expand_platform_path
from installer.core.models import AppConfig, BrowserProfile


def resolve_default_executable_path(executables: List[str]) -> Optional[str]:
    """Resolves standard executable paths when a browser is not running."""

    for exe_candidate in executables:
        # Expand environment variables
        expanded_str = os.path.expandvars(exe_candidate)
        expanded_path = Path(expanded_str)

        # Check if full path exists directly
        if expanded_path.is_absolute() and expanded_path.exists():
            return str(expanded_path)

        # Check system PATH
        found_in_path = shutil.which(exe_candidate)

        if found_in_path:
            return found_in_path

    return None


def check_extension_dir(extention_dir: Path) -> bool:
    if extention_dir.exists():
        for manifest_path in extention_dir.glob("**/manifest.json"):
            if manifest_path.is_file() and manifest_path.stat().st_size > 0:
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        json.load(f)

                    return True

                except (json.JSONDecodeError, OSError):
                    pass

    return False


def scan_browser_profiles(config: AppConfig) -> List[BrowserProfile]:
    """
    Scans host filesystem for installed browsers defined in AppConfig.
    Checks target config paths for profile subdirectories and validates the presence of a 'Preferences' JSON file.
    """

    discovered_profiles: List[BrowserProfile] = []

    for browser_key, browser_def in config.browsers.items():
        plat_config = browser_def.get_current_platform_config()

        if not plat_config:
            continue

        base_path = expand_platform_path(plat_config.config_path)

        if not base_path.exists() or not base_path.is_dir():
            continue

        resolved_exe = resolve_default_executable_path(plat_config.executables)

        # Look for 'Default' or 'Profile *' directories
        for item in base_path.iterdir():
            if not item.is_dir():
                continue

            folder_name = item.name

            if folder_name == "Default" or folder_name.startswith("Profile "):
                pref_file = item / "Preferences"

                # Verify validity of Preferences file
                if pref_file.is_file():
                    discovered_profiles.append(
                        BrowserProfile(
                            browser_key=browser_key,
                            browser_display_name=browser_def.display_name,
                            profile_name=folder_name,
                            profile_path=item,
                            preferences_path=pref_file,
                            executables=plat_config.executables,
                            executable_path=resolved_exe,
                        )
                    )

    return discovered_profiles
