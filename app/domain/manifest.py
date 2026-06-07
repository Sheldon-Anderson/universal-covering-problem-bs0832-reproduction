"""Manifest utilities for the public BS0832 repository."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping, Any

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


def read_manifest(path: Path) -> dict[str, Any]:
    """Read a structured certificate-artifact manifest from JSON."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object")
    return data


def validate_manifest_against_checked_hashes(
    manifest_path: Path,
    checked_hashes: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Ensure MANIFEST.json and SHA256SUMS.txt describe the same artifacts.

    The public verifier treats SHA256SUMS.txt as the byte-level checksum gate and
    MANIFEST.json as the structured inventory for the same certificate artifacts.
    Documentation, source comments, figures, the paper PDF, and CI files are not
    part of this artifact-level gate.
    """
    manifest = read_manifest(manifest_path)
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("Manifest is missing a list-valued 'files' field")

    checked_by_path = {str(row["path"]): row for row in checked_hashes}
    manifest_by_path: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Every manifest entry must be a JSON object")
        rel_path = str(entry.get("path", ""))
        if not rel_path:
            raise ValueError("Manifest entry is missing a nonempty path")
        if rel_path in manifest_by_path:
            raise ValueError(f"Duplicate manifest entry: {rel_path}")
        manifest_by_path[rel_path] = entry

    if set(manifest_by_path) != set(checked_by_path):
        missing_from_manifest = sorted(set(checked_by_path) - set(manifest_by_path))
        missing_from_checksums = sorted(set(manifest_by_path) - set(checked_by_path))
        raise ValueError(
            "Manifest/checksum path mismatch: "
            f"missing_from_manifest={missing_from_manifest}, "
            f"missing_from_checksums={missing_from_checksums}"
        )

    for rel_path, entry in manifest_by_path.items():
        checked = checked_by_path[rel_path]
        if entry.get("sha256") != checked.get("sha256"):
            raise ValueError(f"Manifest SHA256 mismatch for {rel_path}")
        if int(entry.get("size_bytes", -1)) != int(checked.get("size_bytes", -2)):
            raise ValueError(f"Manifest size mismatch for {rel_path}")

    if int(manifest.get("file_count", -1)) != len(entries):
        raise ValueError("Manifest file_count does not match the number of entries")

    return {
        "schema_version": manifest.get("schema_version"),
        "artifact_scope": manifest.get("artifact_scope"),
        "file_count": len(entries),
    }
