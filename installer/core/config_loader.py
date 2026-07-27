import json
import os

from typing import Dict, Any
from pathlib import Path

from installer.core.models import AppConfig,BrowserDefinition, PlatformBrowserConfig


def expand_platform_path(raw_path: str) -> Path:
    """Expands OS environment variables into an absolute Path object."""

    expanded = os.path.expandvars(raw_path)
    return Path(expanded).expanduser().resolve()


def _parse_platform_config(data: Optional[Dict[str, Any]]) -> Optional[PlatformBrowserConfig]:
    if not data:
        return None

    executables = data.get("executables", [])

    if not executables and "exe" in data:
        executables = [data["exe"]]

    return PlatformBrowserConfig(
        base_path=data["base_path"],
        executables=executables,
        policy_key=data.get("policy_key"),
        policy_bundle=data.get("policy_bundle"),
        policy_dir=data.get("policy_dir"),
    )


def load_app_config(config_path: Path) -> AppConfig:
    """Loads and validates installer/config/browsers.json into strongly typed dataclasses."""

    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    browsers: Dict[str, BrowserDefinition] = {}

    for b_key, b_data in data.get("browsers", {}).items():
        browsers[b_key] = BrowserDefinition(
            key=b_key,
            display_name=b_data.get("display_name", b_key),
            windows=_parse_platform_config(b_data.get("windows")),
            macos=_parse_platform_config(b_data.get("macos")),
            linux=_parse_platform_config(b_data.get("linux")),
        )

    return AppConfig(
        extension_id=data["extension_id"],
        default_shortcut=data.get("default_shortcut", "Ctrl+Tab"),
        browsers=browsers,
        shortcut_map=data.get("shortcut", {}),
    )
