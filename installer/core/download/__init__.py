import zipfile
import json
import sys

from pathlib import Path

from core.id_computer import get_extension_pubkey
from core.download.factory import get_vendor
from core.models import AppConfig


def download_extension(config: AppConfig, cache_dir: Path, progress_callback=None) -> Path:
    """Download extension if vendor configured, otherwise return local path."""

    if not config.remote_release_vendor:
        return cache_dir / config.extension_filename

    vendor = get_vendor(config.remote_release_vendor)
    dest = cache_dir / config.extension_filename

    return vendor.download(config, dest, progress_callback=progress_callback)


def extract_extension(crx_path: Path, cache_dir: Path, config: AppConfig) -> Path:
    """Extract CRX file to extracted folder and append pubkey to manifest."""
    if sys.platform.startswith("linux"):
        return None

    extracted_dir = cache_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(crx_path, 'r') as zf:
            zf.extractall(extracted_dir)

        manifest_path = extracted_dir / "manifest.json"

        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            pubkey = get_extension_pubkey(cache_dir, config)
            manifest['key'] = pubkey

            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)

        return extracted_dir

    except Exception:
        return None
