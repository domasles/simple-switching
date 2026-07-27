from pathlib import Path
from typing import List

from installer.core.config_loader import expand_platform_path
from installer.core.models import AppConfig, BrowserProfile


def scan_browser_profiles(config: AppConfig) -> List[BrowserProfile]:
    """
    Scans host filesystem for installed browsers defined in AppConfig.
    Checks target base paths for profile subdirectories and validates the presence of a 'Preferences' JSON file.
    """

    discovered_profiles: List[BrowserProfile] = []

    for browser_key, browser_def in config.browsers.items():
        plat_config = browser_def.get_current_platform_config()

        if not plat_config:
            continue

        base_path = expand_platform_path(plat_config.base_path)

        if not base_path.exists() or not base_path.is_dir():
            continue

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
                        )
                    )

    return discovered_profiles
