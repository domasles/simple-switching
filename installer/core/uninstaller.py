import subprocess
import plistlib
import shutil
import shlex
import json
import sys

from pathlib import Path
from typing import List

from installer.core.models import AppConfig, BrowserProfile


def remove_browser_policies(profiles: List[BrowserProfile], extension_id: str, config: AppConfig) -> List[BrowserProfile]:
    """Removes enterprise force-installation policies."""

    if not profiles:
        return []

    successful_profiles = []

    # Windows
    if sys.platform == "win32":
        import winreg

        for profile in profiles:
            browser_def = config.browsers.get(profile.browser_key)

            if not browser_def:
                continue

            plat_config = browser_def.get_current_platform_config()

            if not plat_config or not plat_config.policy_key:
                continue

            reg_path = f"SOFTWARE\\Policies\\{plat_config.policy_key}\\ExtensionSettings"

            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, extension_id)

                successful_profiles.append(profile)

            except Exception:
                successful_profiles.append(profile)

        return successful_profiles

    # macOS
    elif sys.platform == "darwin":
        plist_dir = Path("/Library/Preferences")

        for profile in profiles:
            browser_def = config.browsers.get(profile.browser_key)

            if not browser_def:
                continue

            plat_config = browser_def.get_current_platform_config()

            if not plat_config or not plat_config.policy_bundle:
                continue

            plist_file = plist_dir / f"{plat_config.policy_bundle}.plist"

            try:
                if plist_file.exists():
                    with open(plist_file, "rb") as f:
                        data = plistlib.load(f)

                    ext_settings = data.get("ExtensionSettings", {})

                    if extension_id in ext_settings:
                        del ext_settings[extension_id]

                        with open(plist_file, "wb") as f:
                            plistlib.dump(data, f)

                successful_profiles.append(profile)

            except Exception:
                pass

        return successful_profiles

    # Linux
    elif sys.platform.startswith("linux"):
        commands = []
        profile_cmd_map = []

        for profile in profiles:
            browser_def = config.browsers.get(profile.browser_key)

            if not browser_def:
                continue

            plat_config = browser_def.get_current_platform_config()

            if not plat_config or not plat_config.policy_dir:
                continue

            policy_file = Path(plat_config.policy_dir) / "custom_extension_installer.json"
            commands.append(f"rm -f {shlex.quote(str(policy_file))}")
            profile_cmd_map.append(profile)

        if not commands:
            return []

        full_script = " && ".join(commands)

        try:
            subprocess.run(
                ["pkexec", "sh", "-c", full_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            return profile_cmd_map

        except Exception:
            return []

    return []


def remove_extension_directory(profile: BrowserProfile, extension_id: str) -> bool:
    """Removes the extension installation folder."""

    profile_path = getattr(profile, "profile_path", None)

    if not profile_path:
        return False

    ext_dir = profile_path / "Extensions" / extension_id

    if ext_dir.exists():
        try:
            shutil.rmtree(ext_dir)
            return True

        except OSError:
            return False

    return True
