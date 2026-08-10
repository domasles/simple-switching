import base64
import struct

from pathlib import Path

from core.config_loader import AppConfig


def _read_header(cache_dir: Path, config: AppConfig) -> bytes:
    with open(cache_dir / config.extension_filename, "rb") as f:
        f.seek(12)
        return f.read(struct.unpack("<I", f.read(4))[0] if f.seek(8) else 0)


def get_extension_id(cache_dir: Path, config: AppConfig) -> str:
    header = _read_header(cache_dir, config)

    idx = header.find(b"\x82\xf1\x04") + 3
    idx = header.find(b"\x0a\x10", idx) + 2

    return "".join(chr(97 + int(c, 16)) for c in header[idx : idx + 16].hex())
