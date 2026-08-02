from core.download.github import GitHubVendor
from core.download.url import UrlVendor
from core.download.base import Vendor

VENDORS = {
    "github": GitHubVendor,
    "url": UrlVendor  # Used for testing or custom download URLs with no interface/vendor coded yet
}


def get_vendor(name: str) -> Vendor:
    """Get vendor instance by name."""

    if name not in VENDORS:
        raise ValueError(f"Unknown vendor: {name}. Available: {list(VENDORS.keys())}")

    return VENDORS[name]()
