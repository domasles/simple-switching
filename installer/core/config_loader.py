import json
import os

from typing import Dict, Any, Optional
from pathlib import Path

from core.models import AppConfig, BrowserDefinition, PlatformBrowserConfig


def expand_platform_path(raw_path: str) -> Path:
    """Expands OS environment variables into an absolute Path object."""

    expanded = os.path.expandvars(raw_path)
    return Path(expanded).expanduser().resolve()


def _parse_platform_config(data: Optional[Dict[str, Any]]) -> Optional[PlatformBrowserConfig]:
    if not data:
        return None

    return PlatformBrowserConfig(
        config_path=data["config_path"],
        executables=data.get("executables", []),
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
            linux=_parse_platform_config(b_data.get("linux")),
        )

    return AppConfig(
        extension_filename=data["extension_filename"],
        browsers=browsers,
        shortcut_map=data.get("shortcut", {}),
        remote_release_vendor=data.get("remote_release_vendor"),
        remote_release_repo=data.get("remote_release_repo"),
        remote_release_tag=data.get("remote_release_tag"),
        remote_download_url=data.get("remote_download_url"),
    )
