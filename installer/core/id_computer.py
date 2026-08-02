import struct

from pathlib import Path

from core.config_loader import AppConfig


def get_extension_id(cache_dir: Path, config: AppConfig):
    with open(f"{cache_dir}/{config.extension_filename}", "rb") as f:
        f.seek(12)
        header = f.read(struct.unpack("<I", f.read(4))[0] if f.seek(8) else 0)

    idx = header.find(b"\x82\xf1\x04") + 3
    idx = header.find(b"\x0a\x10", idx) + 2
    raw_id = header[idx : idx + 16]

    ext_id = "".join(chr(97 + int(c, 16)) for c in raw_id.hex())

    return ext_id
