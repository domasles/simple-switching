from abc import ABC, abstractmethod
from pathlib import Path

from core.models import AppConfig


class Vendor(ABC):
    """Abstract base class for CRX download vendors."""

    @abstractmethod
    def download(self, config: AppConfig, dest_path: Path, progress_callback=None) -> Path:
        """Download CRX to dest_path."""
        pass
