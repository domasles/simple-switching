from pathlib import Path

from installer.core.download.factory import get_vendor
from installer.core.models import AppConfig


def download_extension(config: AppConfig, cache_dir: Path, progress_callback=None) -> Path:
    """Download extension if vendor configured, otherwise return local path."""

    if not config.remote_release_vendor:
        return cache_dir / config.extension_filename

    vendor = get_vendor(config.remote_release_vendor)
    dest = cache_dir / config.extension_filename

    return vendor.download(config, dest, progress_callback=progress_callback)
