"""Manifest utilities for the public BS0832 repository."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .io_utils import sha256_file


@dataclass(frozen=True)
class ManifestEntry:
    """A single file entry recorded in the repository manifest."""

    path: str
    size_bytes: int
    sha256: str


def collect_manifest(root: Path, paths: Iterable[Path]) -> list[ManifestEntry]:
    """Collect size and SHA256 entries for *paths* relative to *root*."""
    entries: list[ManifestEntry] = []
    for path in sorted(paths):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(
            ManifestEntry(
                path=rel,
                size_bytes=path.stat().st_size,
                sha256=sha256_file(path),
            )
        )
    return entries


def parse_sha256sums(path: Path) -> dict[str, str]:
    """Parse a SHA256SUMS file using the standard '<hash>  <path>' format."""
    expected: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, rel_path = line.split(None, 1)
            expected[rel_path.strip()] = digest
    return expected
