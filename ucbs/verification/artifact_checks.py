"""Artifact resolution and checksum checks for the public certificate repository."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

DEFAULT_ARTIFACT_ROOT = Path("certificate") / "final_chain"
DEFAULT_PER_RECORD_EVIDENCE = "per_record_evidence_feedback.zip"
DEFAULT_CONSTRUCTION_AUDIT = "construction_audit_feedback.zip"
DEFAULT_WITNESS_CONSTRUCTION = "witness_construction_feedback.zip"
DEFAULT_FINAL_ADJUDICATION = "final_adjudication_feedback.zip"
DEFAULT_MANIFEST = Path("certificate") / "manifest" / "key_artifacts_sha256.txt"


@dataclass(frozen=True)
class CertificateInputs:
    """Resolved paths for the final certificate-chain archives."""

    artifact_root: Path
    per_record_evidence: Path
    construction_audit: Path
    witness_construction: Path
    final_adjudication: Path

    def as_jsonable(self) -> dict[str, str]:
        """Return a JSON-serializable dictionary of repository-relative paths."""
        return {key: str(value).replace("\\", "/") for key, value in asdict(self).items()}


def sha256_file(path: Path) -> str:
    """Compute the SHA256 digest of a file using streaming reads."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_inputs(
    root: Path,
    artifact_root: Optional[str] = None,
    per_record_evidence_zip: Optional[str] = None,
    construction_audit_zip: Optional[str] = None,
    witness_construction_zip: Optional[str] = None,
    final_adjudication_zip: Optional[str] = None,
) -> CertificateInputs:
    """Resolve explicit or default certificate-chain input paths."""
    del root
    base = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT

    def choose(explicit: Optional[str], default_name: str) -> Path:
        """Resolve one explicit archive path or fall back to the default name."""
        return Path(explicit) if explicit else base / default_name

    return CertificateInputs(
        artifact_root=base,
        per_record_evidence=choose(per_record_evidence_zip, DEFAULT_PER_RECORD_EVIDENCE),
        construction_audit=choose(construction_audit_zip, DEFAULT_CONSTRUCTION_AUDIT),
        witness_construction=choose(witness_construction_zip, DEFAULT_WITNESS_CONSTRUCTION),
        final_adjudication=choose(final_adjudication_zip, DEFAULT_FINAL_ADJUDICATION),
    )


def full_path(root: Path, path: Path) -> Path:
    """Resolve a path relative to the repository root if necessary."""
    return path if path.is_absolute() else root / path


def check_required_inputs(root: Path, inputs: CertificateInputs) -> list[dict[str, object]]:
    """Check that the four final-chain feedback archives exist."""
    rows: list[dict[str, object]] = []
    for label, path in [
        ("per_record_evidence", inputs.per_record_evidence),
        ("construction_audit", inputs.construction_audit),
        ("witness_construction", inputs.witness_construction),
        ("final_adjudication", inputs.final_adjudication),
    ]:
        full = full_path(root, path)
        exists = full.exists()
        rows.append({
            "label": label,
            "path": str(path).replace("\\", "/"),
            "exists": exists,
            "sha256": sha256_file(full) if exists else "",
            "passed": exists,
        })
    return rows


def load_key_artifact_manifest(root: Path) -> dict[str, str]:
    """Load the optional SHA256 list for certificate-chain artifacts."""
    manifest = root / DEFAULT_MANIFEST
    if not manifest.exists():
        return {}
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(maxsplit=1)
        entries[rel.strip()] = digest.strip().lower()
    return entries


def verify_key_artifact_hashes(root: Path) -> list[dict[str, object]]:
    """Verify certificate-chain artifact digests listed by the manifest."""
    expected = load_key_artifact_manifest(root)
    rows: list[dict[str, object]] = []
    for rel, expected_digest in sorted(expected.items()):
        path = root / rel
        exists = path.exists()
        actual_digest = sha256_file(path) if exists else ""
        rows.append({
            "path": rel,
            "exists": exists,
            "expected_sha256": expected_digest,
            "actual_sha256": actual_digest,
            "passed": exists and actual_digest == expected_digest,
        })
    return rows
