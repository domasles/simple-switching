import subprocess
import shlex
import json
import sys

from pathlib import Path
from typing import List

from core.models import AppConfig, BrowserProfile


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
            }
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
