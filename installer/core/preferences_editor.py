import tempfile
import json
import sys
import os

from typing import Dict, Any
from pathlib import Path

from installer.core.models import AppConfig, BrowserProfile


def get_platform_shortcut_key(shortcut_map: Dict[str, str]) -> str:
    """Determines platform-specific shortcut key."""

    if sys.platform == "win32":
        return shortcut_map.get("windows", "win:Ctrl+Tab")
    elif sys.platform == "darwin":
        return shortcut_map.get("macos", "mac:Ctrl+Tab")
    else:
        return shortcut_map.get("linux", "linux:Ctrl+Tab")


def inject_extension_shortcut(profile: BrowserProfile, config: AppConfig, command_name: str = "switch-tab") -> bool:
    """
    Safely injects keybinding shortcuts directly into target profile's Preferences JSON.
    Uses atomic tempfile writing to protect against JSON file corruption.
    """

    pref_path = profile.preferences_path

    if not pref_path.is_file():
        return False

    try:
        with open(pref_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    # Ensure nested dictionary structure exists
    extensions_node = data.setdefault("extensions", {})
    commands_node = extensions_node.setdefault("commands", {})

    platform_key = get_platform_shortcut_key(config.shortcut_map)
    shortcut_entry = commands_node.setdefault(platform_key, {})

    # Inject command mapping
    shortcut_entry[command_name] = {
        "command_name": command_name,
        "extension": config.extension_id,
        "global": False
    }

    # Atomic Write: Write to temporary file in same directory first, then replace
    temp_file = pref_path.with_suffix(".tmp")

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        os.replace(temp_file, pref_path)
        return True

    except Exception:
        if temp_file.exists():
            temp_file.unlink()

        return False
