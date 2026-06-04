"""Validation of the author/reviewer signoff file."""
from __future__ import annotations

from pathlib import Path

from .io_utils import read_json, sha256_file

# Blocking proof obligations expected in the public author self-review file.
EXPECTED_OBLIGATIONS = [
    "OB-A-001",
    "OB-A-002",
    "OB-A-003",
    "OB-B-001",
    "OB-B-002",
    "OB-B-003",
    "OB-B-004",
    "OB-B-005",
    "OB-C-001",
    "OB-C-002",
    "OB-C-003",
    "OB-D-001",
    "OB-E-001",
    "OB-E-002",
    "OB-E-003",
    "OB-F-001",
    "OB-F-002",
    "OB-F-003",
    "OB-F-004",
]

# Remaining formalization-gap identifiers accepted by the signoff record.
EXPECTED_GAPS = ["FG1", "FG2", "FG3", "FG4"]
# Global decisions that count as accepting the final signoff packet.
ACCEPTED_GLOBAL_DECISIONS = {"accepted", "accepted_with_minor_notes"}


def validate_signoff(signoff_path: Path, reviewed_feedback_zip: Path) -> dict[str, object]:
    """Validate the signoff JSON against the expected BS0832 obligations.

    The signoff is intentionally treated as a structured declaration, not as an
    informal note.  It must accept every blocking obligation, must not reject or
    defer any obligation, and must reference the exact v108 feedback archive by
    SHA256 digest.
    """
    signoff = read_json(signoff_path)

    # These fields make the signoff machine-checkable rather than free-form prose.
    required_fields = [
        "schema_version",
        "reviewer_name_or_handle",
        "review_date",
        "review_scope",
        "reviewed_feedback_zip_sha256",
        "global_decision",
        "accepted_obligations",
        "rejected_obligations",
        "needs_revision_obligations",
        "accepted_gaps",
        "notes",
    ]
    missing = [field for field in required_fields if field not in signoff]
    if missing:
        raise ValueError(f"Missing required signoff fields: {missing}")

    if signoff["schema_version"] != "v109-reviewer-signoff-v1":
        raise ValueError("Unsupported signoff schema version")

    if signoff["global_decision"] not in ACCEPTED_GLOBAL_DECISIONS:
        raise ValueError("Global decision does not accept the signoff packet")

    # The signoff must accept exactly the public obligation set: no missing and no extras.
    accepted = set(signoff["accepted_obligations"])
    expected = set(EXPECTED_OBLIGATIONS)
    if accepted != expected:
        missing_obligations = sorted(expected - accepted)
        extra_obligations = sorted(accepted - expected)
        raise ValueError(
            "Accepted obligations do not match expected list: "
            f"missing={missing_obligations}, extra={extra_obligations}"
        )

    if signoff["rejected_obligations"]:
        raise ValueError("Signoff contains rejected obligations")
    if signoff["needs_revision_obligations"]:
        raise ValueError("Signoff contains obligations needing revision")

    accepted_gaps = set(signoff["accepted_gaps"])
    if accepted_gaps != set(EXPECTED_GAPS):
        raise ValueError("Accepted formalization gaps do not match expected list")

    # Bind the signoff to the reviewed reference archive. A regenerated ZIP needs its own signoff.
    reviewed_digest = sha256_file(reviewed_feedback_zip)
    if signoff["reviewed_feedback_zip_sha256"] != reviewed_digest:
        raise ValueError("Signoff SHA256 does not match the reviewed feedback archive")

    return {
        "reviewer": signoff["reviewer_name_or_handle"],
        "review_date": signoff["review_date"],
        "global_decision": signoff["global_decision"],
        "accepted_obligations": len(accepted),
        "accepted_gaps": len(accepted_gaps),
        "reviewed_feedback_zip_sha256": reviewed_digest,
    }
