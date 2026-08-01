import requests

from pathlib import Path

from installer.core.download.base import Vendor
from installer.core.models import AppConfig


class GitHubVendor(Vendor):
    """Downloads extension from GitHub Releases."""

    def download(self, config: AppConfig, dest_path: Path, progress_callback=None) -> Path:
        headers = {"Accept": "application/vnd.github+json"}
        api_url = f"https://api.github.com/repos/{config.remote_release_repo}/releases/tags/{config.remote_release_tag}"

        # Fetch release info
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        release = response.json()

        # Find matching asset
        asset_url = None
        asset_size = None

        for asset in release.get("assets", []):
            if asset["name"] == config.extension_filename:
                asset_url = asset["browser_download_url"]
                asset_size = asset["size"]

                break

        if not asset_url:
            raise ValueError(
                f"Asset '{config.extension_filename}' not found in release "
                f"{release.get('tag_name', 'unknown')}"
            )

        # Download with progress
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with requests.get(asset_url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = asset_size or int(r.headers.get("Content-Length", 0))
            downloaded = 0

            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total > 0:
                            progress_callback(downloaded, total)

        if progress_callback and total > 0:
            progress_callback(total, total)

        return dest_path
