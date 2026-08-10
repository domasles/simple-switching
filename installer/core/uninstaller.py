import shutil
import sys

from pathlib import Path
from typing import List

from core.models import AppConfig, BrowserProfile


def remove_browser_policies(profiles: List[BrowserProfile], config: AppConfig) -> List[BrowserProfile]:
    """Removes enterprise force-installation policies."""

    if not profiles:
        return []

    # Only Linux uses policy-based installation
    if not sys.platform.startswith("linux"):
        return profiles

    import subprocess
    import shlex

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
