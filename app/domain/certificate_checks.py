"""Checks for the final BS0832 certificate archive."""
from __future__ import annotations

from pathlib import Path

from .io_utils import assert_zip_integrity, read_json_from_zip


REQUIRED_TRUE_FLAGS = [
    "status",
    "source_integrity_passed",
    "schema_validation_passed",
    "v108_input_accepted",
    "bs0832_reproduction_complete_candidate",
    "theorem_claim_ready_for_final_human_review",
    "proof_obligation_ledger_complete",
    "all_blocking_obligations_artifact_adjudicated",
    "formalization_gap_adjudication_complete",
    "line_numbered_manuscript_ready",
    "artifact_to_manuscript_crosswalk_complete",
    "signoff_schema_ready",
    "external_or_human_signoff_present",
    "reviewer_acceptance_gate_passed",
    "theorem_ready_signed_candidate",
    "final_theorem_signoff_packet_ready",
    "red_team_signed_claim_audit_passed",
]

REQUIRED_FALSE_FLAGS = [
    "theorem_ready",
    "bs0832_reproduced_theorem_level",
]


def validate_final_certificate(feedback_zip: Path) -> dict[str, object]:
    """Validate the final signed certificate archive.

    The public repository verifies the signed-candidate certificate status.  It
    deliberately leaves the theorem-ready flag unset, because the repository is
    a reproducible certificate package rather than a formal proof assistant
    development.
    """
    assert_zip_integrity(feedback_zip)
    summary = read_json_from_zip(feedback_zip, "data/v109_readiness_summary.json")
    decision = read_json_from_zip(feedback_zip, "proof/final_theorem_signoff_decision_v109.json")

    if summary.get("status") != "success":
        raise ValueError("Final certificate summary status is not success")

    # The first item is the string status field; remaining items must be true.
    for flag in REQUIRED_TRUE_FLAGS[1:]:
        if summary.get(flag) is not True:
            raise ValueError(f"Expected summary flag {flag}=true")

    for flag in REQUIRED_FALSE_FLAGS:
        if summary.get(flag) is not False:
            raise ValueError(f"Expected summary flag {flag}=false")

    if summary.get("proof_boundary_violations") != 0:
        raise ValueError("Proof-boundary audit reports violations")

    if decision.get("theorem_ready") is not False:
        raise ValueError("Decision file unexpectedly sets theorem_ready=true")
    if decision.get("reviewer_acceptance_gate_passed") is not True:
        raise ValueError("Decision file does not pass the reviewer acceptance gate")
    if decision.get("theorem_ready_signed_candidate") is not True:
        raise ValueError("Decision file does not record signed-candidate status")

    return {
        "run_id": summary.get("run_id"),
        "proof_obligation_count": summary.get("proof_obligation_count"),
        "final_theorem_signoff_packet_ready": summary.get("final_theorem_signoff_packet_ready"),
        "theorem_ready_signed_candidate": summary.get("theorem_ready_signed_candidate"),
        "theorem_ready": summary.get("theorem_ready"),
        "proof_boundary_violations": summary.get("proof_boundary_violations"),
    }
