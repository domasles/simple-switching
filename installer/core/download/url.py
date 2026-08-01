import requests

from urllib.parse import urlparse
from pathlib import Path

from installer.core.download.base import Vendor
from installer.core.models import AppConfig


class UrlVendor(Vendor):
    """Downloads extension directly from a specified URL."""

    def download(self, config: AppConfig, dest_path: Path, progress_callback=None) -> Path:
        # Resolve local destination file path
        if dest_path.is_dir() or dest_path.name != config.extension_filename:
            target_path = dest_path / config.extension_filename if dest_path.is_dir() else dest_path

        else:
            target_path = dest_path

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Resolve remote URL
        download_url = config.remote_download_url.rstrip("/")
        parsed_url = urlparse(download_url)

        # If the URL path doesn't end with the filename, append it
        if not parsed_url.path.endswith(config.extension_filename):
            download_url = f"{download_url}/{config.extension_filename}"

        # Download
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0

            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total > 0:
                            progress_callback(downloaded, total)

        if progress_callback and total > 0:
            progress_callback(total, total)

        return target_path
