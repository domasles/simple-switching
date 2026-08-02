import subprocess
import plistlib
import shlex
import json
import sys
import os

from typing import Optional, List
from pathlib import Path

from core.models import AppConfig, BrowserDefinition, BrowserProfile


def generate_update_manifest_xml(extension_id: str, crx_url: str, version: str = "1.0.0") -> str:
    """Generates update XML manifest content."""

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<gupdate xmlns='http://www.google.com/update2/response' protocol='2.0'>
  <app appid='{extension_id}'>
    <updatecheck codebase='{crx_url}' version='{version}' />
  </app>
</gupdate>
"""


def deploy_browser_policy(profiles: List[BrowserProfile], extension_id: str, config: AppConfig, update_xml_url: str) -> List[BrowserProfile]:
    """Deploys force-installation enterprise policies."""

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

            policy_base = f"SOFTWARE\\Policies\\{plat_config.policy_key}"
            reg_path_settings = f"{policy_base}\\ExtensionSettings"
            reg_path_forcelist = f"{policy_base}\\ExtensionInstallForcelist"

            try:
                with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, reg_path_settings, 0, winreg.KEY_SET_VALUE) as key:
                    setting_payload = json.dumps({
                        extension_id: {
                            "installation_mode": "force_installed",
                            "update_url": update_xml_url
                        }
                    })

                    winreg.SetValueEx(key, extension_id, 0, winreg.REG_SZ, setting_payload)

                with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, reg_path_forcelist, 0, winreg.KEY_ALL_ACCESS) as key:
                    index = 1

                    while True:
                        try:
                            winreg.EnumValue(key, index - 1)
                            index += 1

                        except OSError:
                            break

                    force_entry = f"{extension_id};{update_xml_url}"
                    winreg.SetValueEx(key, str(index), 0, winreg.REG_SZ, force_entry)

                successful_profiles.append(profile)

            except Exception:
                pass

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
            data = {}

            try:
                if plist_file.exists():
                    with open(plist_file, "rb") as f:
                        data = plistlib.load(f)

                ext_settings = data.setdefault("ExtensionSettings", {})

                ext_settings[extension_id] = {
                    "installation_mode": "force_installed",
                    "update_url": update_xml_url
                }

                ext_forcelist = data.setdefault("ExtensionInstallForcelist", [])
                force_entry = f"{extension_id};{update_xml_url}"

                if force_entry not in ext_forcelist:
                    ext_forcelist.append(force_entry)

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

            policy_dir = Path(plat_config.policy_dir)
            policy_file = policy_dir / "custom_extension_installer.json"

            policy_data = {
                "ExtensionSettings": {
                    extension_id: {
                        "installation_mode": "force_installed",
                        "update_url": update_xml_url
                    }
                },
                "ExtensionInstallForcelist": [
                    f"{extension_id};{update_xml_url}"
                ]
            }

            json_str = json.dumps(policy_data, indent=2)
            cmd_snippet = f"mkdir -p {shlex.quote(str(policy_dir))} && cat << 'EOF' > {shlex.quote(str(policy_file))}\n{json_str}\nEOF\n"
            commands.append(cmd_snippet)
            profile_cmd_map.append(profile)

        if not commands:
            return []

        full_script = " && ".join(cmd.strip() for cmd in commands)

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
