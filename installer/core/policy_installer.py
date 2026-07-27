import plistlib
import json
import sys
import os

from typing import Optional
from pathlib import Path

from installer.core.models import AppConfig, BrowserDefinition


def generate_update_manifest_xml(extension_id: str, crx_url: str, version: str = "1.0.0") -> str:
    """Generates update XML manifest content."""

    return f"""<?xml '1.0' encoding='UTF-8'?>
<gupdate xmlns='http://www.google.com/update2/response' protocol='2.0'>
  <app appid='{extension_id}'>
    <updatecheck codebase='{crx_url}' version='{version}' />
  </app>
</gupdate>"""


def deploy_browser_policy(browser_def: BrowserDefinition, config: AppConfig, update_xml_url: str) -> bool:
    """Deploys force-installation enterprise policies."""

    plat_config = browser_def.get_current_platform_config()

    if not plat_config:
        return False

    try:
        # Windows
        if sys.platform == "win32" and plat_config.policy_key:
            import winreg
            reg_path = f"SOFTWARE\\Policies\\{plat_config.policy_key}\\ExtensionSettings"

            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                setting_payload = json.dumps({
                    config.extension_id: {
                        "installation_mode": "force_installed",
                        "update_url": update_xml_url
                    }
                })

                winreg.SetValueEx(key, config.extension_id, 0, winreg.REG_SZ, setting_payload)

            return True

        # MacOS
        elif sys.platform == "darwin" and plat_config.policy_bundle:
            plist_dir = Path("/Library/Preferences")
            plist_file = plist_dir / f"{plat_config.policy_bundle}.plist"

            data = {}

            if plist_file.exists():
                with open(plist_file, "rb") as f:
                    data = plistlib.load(f)

            ext_settings = data.setdefault("ExtensionSettings", {})

            ext_settings[config.extension_id] = {
                "installation_mode": "force_installed",
                "update_url": update_xml_url
            }

            with open(plist_file, "wb") as f:
                plistlib.dump(data, f)

            return True

        # Linux
        elif sys.platform.startswith("linux") and plat_config.policy_dir:
            policy_dir = Path(plat_config.policy_dir)
            policy_dir.mkdir(parents=True, exist_ok=True)
            policy_file = policy_dir / "custom_extension_installer.json"

            policy_data = {
                "ExtensionSettings": {
                    config.extension_id: {
                        "installation_mode": "force_installed",
                        "update_url": update_xml_url
                    }
                }
            }

            with open(policy_file, "w", encoding="utf-8") as f:
                json.dump(policy_data, f, indent=2)

            return True

    except Exception:
        return False

    return False
