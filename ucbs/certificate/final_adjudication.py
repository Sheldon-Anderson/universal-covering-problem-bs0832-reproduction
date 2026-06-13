"""Replay checks for final-adjudication certificate records.

This module verifies final proof-obligation rows, witness-status consistency,
claim-boundary records, artifact integrity rows, and scope flags. It maps raw
archive status fields into stable public certificate-verification status.
"""
from __future__ import annotations

from pathlib import Path

from ucbs.certificate.archive_io import (
    read_csv_member,
    read_json_member,
    relative_label,
    require_members,
    resolve_archive,
)
from ucbs.certificate.validation import (
    ComponentReport,
    check_row,
    require_columns,
    require_exact_count,
    require_min_count,
    require_unique_keys,
    truthy,
    write_component_outputs,
)

REQUIRED_MEMBERS = [
    "status/v136.status.json",
    "diagnostics/v136_final_theorem_ready_gate.csv",
    "diagnostics/v136_final_proof_obligation_discharge.csv",
    "diagnostics/v136_final_kernel_certificate_audit.csv",
    "diagnostics/v136_final_claim_boundary_lint.csv",
    "diagnostics/v136_theorem_critical_artifact_integrity.csv",
    "diagnostics/v136_v135_status_consistency_audit.csv",
]

EXPECTED_OBLIGATIONS = {
    "O-INPUT",
    "O-KERNEL",
    "O-EVIDENCE",
    "O-GLOBAL",
    "O-ROUNDING",
    "O-PATCH-FINAL-REPLAY",
    "O-CLAIM-BOUNDARY",
    "O-MANIFEST-LOCK-PRECHECK",
    "O-FINAL-THEOREM-READY",
}
EXPECTED_WITNESS_AUDITS = {
    "W-AGGREGATE-PRESENT",
    "W-PATCH-COUNT",
    "W-PATCH-PASSED-16",
    "W-PATCH-FAILED-0",
    "W-TERMINAL-FAILED-SUBBOXES-0",
    "W-MIN-AREA-LOWER-GT-TARGET",
    "W-MIN-AREA-MARGIN-POSITIVE",
    "W-MIN-TERMINAL-ORIENTATION-POSITIVE",
    "W-PROVENANCE-ALL-PASSED",
    "W-ORIENTATION-ROWS-PRESENT",
}
EXPECTED_STATUS_AUDITS = {
    "S-STATUS",
    "S-EXPLICIT-CERT",
    "S-INNER-PASSED-16",
    "S-INNER-FAILED-0",
    "S-PROOF-GRADE-KERNEL",
    "S-ROUNDING-FINAL",
    "S-PATCH-REPLAY-16",
    "S-ROW-EVIDENCE",
    "S-GLOBAL",
    "S-PROOF-OBLIGATION",
    "S-GATE",
    "S-BLOCKERS-ZERO",
}

GATE_COLUMNS = {"gate_id", "independent_v135_replay_passed", "final_claim_boundary_violation_count", "final_obligation_blocker_count", "theorem_critical_hash_mismatch_count", "target_083201_proved"}
OBLIGATION_COLUMNS = {"obligation_id", "obligation_status", "obligation_passed"}
AUDIT_COLUMNS = {"check_id", "check_status", "observed_value"}
CLAIM_COLUMNS = {"check_type", "file_path", "pattern", "hit", "lint_status"}
INTEGRITY_COLUMNS = {"artifact_path", "size_bytes", "sha256", "artifact_integrity_status"}


def _all_status(rows: list[dict[str, str]], field: str, passing: set[str]) -> bool:
    if not rows:
        return False
    return all(str(row.get(field, "")).strip().lower() in passing for row in rows)


def _ids(rows: list[dict[str, str]], field: str) -> set[str]:
    return {row.get(field, "") for row in rows if row.get(field, "")}


def check_final_adjudication(root: Path, archive: str | Path) -> ComponentReport:
    """Check final-adjudication records from the archive."""
    path = resolve_archive(root, archive)
    checks = []
    if not path.exists():
        checks.append(check_row("archive_exists", False, relative_label(root, path), "archive is missing"))
        return ComponentReport("final_adjudication", False, checks, {"final_adjudication_passed": False})

    checks.append(check_row("archive_exists", True, relative_label(root, path), "archive is present"))
    member_rows = require_members(path, REQUIRED_MEMBERS)
    checks.extend(member_rows)
    if not all(truthy(row.get("passed")) for row in member_rows):
        return ComponentReport("final_adjudication", False, checks, {"final_adjudication_passed": False})

    status = read_json_member(path, "status/v136.status.json")
    gate = read_csv_member(path, "diagnostics/v136_final_theorem_ready_gate.csv")
    obligations = read_csv_member(path, "diagnostics/v136_final_proof_obligation_discharge.csv")
    certificate_audit = read_csv_member(path, "diagnostics/v136_final_kernel_certificate_audit.csv")
    claim_lint = read_csv_member(path, "diagnostics/v136_final_claim_boundary_lint.csv")
    integrity = read_csv_member(path, "diagnostics/v136_theorem_critical_artifact_integrity.csv")
    status_consistency = read_csv_member(path, "diagnostics/v136_v135_status_consistency_audit.csv")

    checks.extend(require_columns(gate, GATE_COLUMNS, "final_gate_rows"))
    checks.extend(require_columns(obligations, OBLIGATION_COLUMNS, "proof_obligation_rows"))
    checks.extend(require_columns(certificate_audit, AUDIT_COLUMNS, "witness_audit_rows"))
    checks.extend(require_columns(claim_lint, CLAIM_COLUMNS, "claim_lint_rows"))
    checks.extend(require_columns(integrity, INTEGRITY_COLUMNS, "final_integrity_rows"))
    checks.extend(require_columns(status_consistency, AUDIT_COLUMNS, "source_status_consistency_rows"))
    checks.append(require_exact_count(gate, 1, "final_gate_rows"))
    checks.append(require_exact_count(obligations, 9, "proof_obligation_rows"))
    checks.append(require_exact_count(certificate_audit, 10, "witness_audit_rows"))
    checks.append(require_min_count(claim_lint, 1, "claim_lint_rows"))
    checks.append(require_min_count(integrity, 1, "final_integrity_rows"))
    checks.append(require_exact_count(status_consistency, 12, "source_status_consistency_rows"))
    checks.append(require_unique_keys(obligations, ["obligation_id"], "proof_obligation_rows"))
    checks.append(require_unique_keys(certificate_audit, ["check_id"], "witness_audit_rows"))
    checks.append(require_unique_keys(status_consistency, ["check_id"], "source_status_consistency_rows"))

    obligation_ids = _ids(obligations, "obligation_id")
    witness_audit_ids = _ids(certificate_audit, "check_id")
    source_audit_ids = _ids(status_consistency, "check_id")
    checks.append(check_row("proof_obligation_id_set", obligation_ids == EXPECTED_OBLIGATIONS, ";".join(sorted(obligation_ids)), "proof obligation ID set matches the certificate contract"))
    checks.append(check_row("witness_audit_id_set", witness_audit_ids == EXPECTED_WITNESS_AUDITS, ";".join(sorted(witness_audit_ids)), "witness audit ID set matches the certificate contract"))
    checks.append(check_row("source_status_audit_id_set", source_audit_ids == EXPECTED_STATUS_AUDITS, ";".join(sorted(source_audit_ids)), "source status audit ID set matches the certificate contract"))

    gate_row = gate[0] if gate else {}
    checks.append(check_row("final_gate_independent_replay", truthy(gate_row.get("independent_v135_replay_passed")), gate_row.get("independent_v135_replay_passed"), "final gate records independent witness replay"))
    checks.append(check_row("final_gate_claim_boundary", str(gate_row.get("final_claim_boundary_violation_count", "")) == "0", gate_row.get("final_claim_boundary_violation_count"), "final gate records zero claim-boundary violations"))
    checks.append(check_row("final_gate_obligation_blockers", str(gate_row.get("final_obligation_blocker_count", "")) == "0", gate_row.get("final_obligation_blocker_count"), "final gate records zero obligation blockers"))
    checks.append(check_row("final_gate_hash_mismatches", str(gate_row.get("theorem_critical_hash_mismatch_count", "")) == "0", gate_row.get("theorem_critical_hash_mismatch_count"), "final gate records zero critical hash mismatches"))
    checks.append(check_row("final_gate_threshold_proved", truthy(gate_row.get("target_083201_proved")), gate_row.get("target_083201_proved"), "final gate records the certified threshold"))
    checks.append(check_row("obligations_discharged", all(str(row.get("obligation_status", "")).lower() == "discharged" and truthy(row.get("obligation_passed")) for row in obligations), len(obligations), "all final proof obligations are discharged"))
    checks.append(check_row("certificate_audit_passed", _all_status(certificate_audit, "check_status", {"passed"}), len(certificate_audit), "final certificate audit rows pass"))
    claim_types = {row.get("check_type", "") for row in claim_lint}
    checks.append(check_row("claim_lint_required_types", {"forbidden_overreach", "required_boundary_token"}.issubset(claim_types), ";".join(sorted(claim_types)), "claim lint covers forbidden overreach and required boundary tokens"))
    claim_lint_ok = all(
        str(row.get("lint_status", "")).lower() == "passed"
        and (not truthy(row.get("hit")) or str(row.get("check_type", "")).lower() == "required_boundary_token")
        for row in claim_lint
    )
    checks.append(check_row("claim_lint_passed", claim_lint_ok, len(claim_lint), "final claim-boundary lint rows pass"))
    checks.append(check_row("critical_integrity_present", _all_status(integrity, "artifact_integrity_status", {"present_locked"}), len(integrity), "critical artifacts are present and locked"))
    checks.append(check_row("status_consistency_passed", _all_status(status_consistency, "check_status", {"passed"}), len(status_consistency), "source status consistency audit rows pass"))
    checks.append(check_row("status_threshold_proved", truthy(status.get("target_083201_proved")), status.get("target_083201_proved"), "status records the certified threshold"))
    checks.append(check_row("status_proof_obligations", truthy(status.get("proof_obligations_discharged")), status.get("proof_obligations_discharged"), "status records discharged proof obligations"))
    checks.append(check_row("status_nonconvex_not_claimed", not truthy(status.get("nonconvex_lower_bound_claimed")), status.get("nonconvex_lower_bound_claimed"), "status does not claim a nonconvex result"))
    checks.append(check_row("status_proof_assistant_not_claimed", not truthy(status.get("proof_assistant_formalization_completed")), status.get("proof_assistant_formalization_completed"), "status does not claim proof-assistant formalization"))
    checks.append(check_row("status_external_not_claimed", not truthy(status.get("independent_external_verification_completed")), status.get("independent_external_verification_completed"), "status does not claim independent external verification"))

    passed = not any(not truthy(row.get("passed")) for row in checks)
    details = {
        "final_adjudication_passed": passed,
        "certificate_verified": passed,
        "threshold_proved": truthy(status.get("target_083201_proved")) and passed,
        "proof_obligations_discharged": truthy(status.get("proof_obligations_discharged")) and passed,
        "nonconvex_lower_bound_claimed": False,
        "proof_assistant_formalization_completed": False,
        "independent_external_verification_completed": False,
    }
    return ComponentReport("final_adjudication", passed, checks, details)


def run_final_adjudication_replay(
    root: Path,
    archive: str | Path,
    run_id: str = "final_adjudication_replay",
    log_level: str = "INFO",
) -> Path:
    """Run final-adjudication replay and write a feedback archive."""
    report = check_final_adjudication(root, archive)
    return write_component_outputs(
        root=root,
        run_id=run_id,
        log_name="final_adjudication_replay.log",
        status_name="final_adjudication_replay.status.json",
        feedback_name="final_adjudication_replay_feedback.zip",
        report=report,
        archive_label=relative_label(root, resolve_archive(root, archive)),
        log_level=log_level,
    )
