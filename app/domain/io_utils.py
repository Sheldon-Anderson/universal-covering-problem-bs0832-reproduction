"""Input/output helpers for the BS0832 verification scripts.

The functions in this module are intentionally small and dependency-light.  They
are shared by the command-line entry point and the final verifier.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA256 digest of *path* using streaming reads.

    Streaming avoids loading large feedback archives into memory.  The default
    chunk size is large enough for good throughput on common laptops while still
    being conservative on memory use.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    """Read a UTF-8 JSON file into a dictionary."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    """Write *data* as pretty-printed UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def read_json_from_zip(zip_path: Path, member_name: str) -> dict[str, Any]:
    """Read a JSON member from a ZIP archive."""
    with zipfile.ZipFile(zip_path, "r") as archive:
        with archive.open(member_name, "r") as handle:
            data = json.loads(handle.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {zip_path}:{member_name}")
    return data


def assert_zip_integrity(zip_path: Path) -> None:
    """Run the built-in ZIP CRC check and raise if any member is corrupt."""
    with zipfile.ZipFile(zip_path, "r") as archive:
        bad_member = archive.testzip()
    if bad_member is not None:
        raise ValueError(f"ZIP integrity check failed for {zip_path}: {bad_member}")
