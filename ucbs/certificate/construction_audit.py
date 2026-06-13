"""Replay checks for construction-audit certificate records.

This module verifies artifact presence, support-to-area rows, candidate
polygon rows, rounding records, and construction-stage integrity checks from
the bundled construction-audit archive. It does not regenerate the certificate
records from geometric search data.
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
    status_passed,
    truthy,
    write_component_outputs,
)

REQUIRED_MEMBERS = [
    "diagnostics/v134_final_kernel_closure_artifact_audit.csv",
    "diagnostics/v134_support_to_area_final_lemma_certificate.csv",
    "diagnostics/v134_inner_polygon_area_certificate.csv",
    "diagnostics/v134_operation_level_arb_rounding_ledger.csv",
    "diagnostics/v134_theorem_critical_artifact_integrity.csv",
    "diagnostics/v134_conditional_theorem_ready_gate.csv",
    "status/v134.status.json",
]

ARTIFACT_COLUMNS = {"artifact_path", "size_bytes", "sha256", "artifact_audit_status"}
SUPPORT_COLUMNS = {"patch_record_id", "support_area_policy", "support_to_area_final_passed", "support_to_area_final_status"}
POLYGON_COLUMNS = {"patch_record_id", "area_certificate_route", "candidate_margin_vs_083201", "inner_polygon_kernel_passed", "inner_polygon_status"}
ROUNDING_COLUMNS = {"operation_id", "patch_record_id", "operation_name", "contains_target_bound", "arb_status", "proof_status"}
INTEGRITY_COLUMNS = {"zip_basename", "theorem_critical_hash_mismatch_count", "theorem_critical_integrity_status"}
GATE_COLUMNS = {"gate_id", "input_integrity_passed", "row_level_evidence_closed", "global_replay_hardened"}


def _all_status(rows: list[dict[str, str]], field: str, passing: set[str]) -> bool:
    if not rows:
        return False
    return all(str(row.get(field, "")).strip().lower() in passing for row in rows)


def check_construction_audit(root: Path, archive: str | Path) -> ComponentReport:
    """Check construction-audit records from the archive."""
    path = resolve_archive(root, archive)
    checks = []
    if not path.exists():
        checks.append(check_row("archive_exists", False, relative_label(root, path), "archive is missing"))
        return ComponentReport("construction_audit", False, checks, {"construction_audit_passed": False})

    checks.append(check_row("archive_exists", True, relative_label(root, path), "archive is present"))
    member_rows = require_members(path, REQUIRED_MEMBERS)
    checks.extend(member_rows)
    if not all(truthy(row.get("passed")) for row in member_rows):
        return ComponentReport("construction_audit", False, checks, {"construction_audit_passed": False})

    status = read_json_member(path, "status/v134.status.json")
    artifact_audit = read_csv_member(path, "diagnostics/v134_final_kernel_closure_artifact_audit.csv")
    support_area = read_csv_member(path, "diagnostics/v134_support_to_area_final_lemma_certificate.csv")
    polygon_area = read_csv_member(path, "diagnostics/v134_inner_polygon_area_certificate.csv")
    rounding = read_csv_member(path, "diagnostics/v134_operation_level_arb_rounding_ledger.csv")
    integrity = read_csv_member(path, "diagnostics/v134_theorem_critical_artifact_integrity.csv")
    gate = read_csv_member(path, "diagnostics/v134_conditional_theorem_ready_gate.csv")

    checks.extend(require_columns(artifact_audit, ARTIFACT_COLUMNS, "construction_artifact_audit"))
    checks.extend(require_columns(support_area, SUPPORT_COLUMNS, "support_to_area_rows"))
    checks.extend(require_columns(polygon_area, POLYGON_COLUMNS, "candidate_polygon_rows"))
    checks.extend(require_columns(rounding, ROUNDING_COLUMNS, "construction_rounding_rows"))
    checks.extend(require_columns(integrity, INTEGRITY_COLUMNS, "construction_integrity_rows"))
    checks.extend(require_columns(gate, GATE_COLUMNS, "construction_gate_rows"))
    checks.append(require_exact_count(artifact_audit, 47, "construction_artifact_audit"))
    checks.append(require_exact_count(support_area, 16, "support_to_area_rows"))
    checks.append(require_exact_count(polygon_area, 16, "candidate_polygon_rows"))
    checks.append(require_exact_count(rounding, 96, "construction_rounding_rows"))
    checks.append(require_min_count(integrity, 1, "construction_integrity_rows"))
    checks.append(require_exact_count(gate, 1, "construction_gate_rows"))
    checks.append(require_unique_keys(artifact_audit, ["artifact_path"], "construction_artifact_audit"))
    checks.append(require_unique_keys(support_area, ["patch_record_id"], "support_to_area_rows"))
    checks.append(require_unique_keys(polygon_area, ["patch_record_id"], "candidate_polygon_rows"))
    checks.append(require_unique_keys(rounding, ["operation_id"], "construction_rounding_rows"))

    checks.append(check_row("artifact_audit_present", _all_status(artifact_audit, "artifact_audit_status", {"present"}), len(artifact_audit), "construction archive artifacts are present"))
    checks.append(check_row("rounding_arb_available", all(str(row.get("arb_status", "")).strip().lower() == "available" for row in rounding), len(rounding), "arb rounding backend is available in recorded operation rows"))
    checks.append(check_row("rounding_contains_threshold", all(truthy(row.get("contains_target_bound")) for row in rounding), len(rounding), "rounding rows retain threshold containment"))
    checks.append(check_row("critical_integrity_passed", _all_status(integrity, "theorem_critical_integrity_status", {"passed"}), len(integrity), "critical artifact integrity rows pass"))
    gate_row = gate[0] if gate else {}
    gate_passed = truthy(gate_row.get("input_integrity_passed")) and truthy(gate_row.get("row_level_evidence_closed")) and truthy(gate_row.get("global_replay_hardened"))
    checks.append(check_row("conditional_gate_preconditions", gate_passed, gate_row.get("gate_id", ""), "construction-stage preconditions are recorded"))
    checks.append(check_row("status_input_integrity", truthy(status.get("input_integrity_passed")), status.get("input_integrity_passed"), "status records input integrity"))
    checks.append(check_row("status_global_replay_hardened", truthy(status.get("global_replay_hardened")), status.get("global_replay_hardened"), "status records hardened global replay"))
    checks.append(check_row("status_value_accepted", status_passed(status.get("status")) or str(status.get("status", "")).startswith("success"), status.get("status"), "status records a successful construction-audit run"))

    passed = not any(not truthy(row.get("passed")) for row in checks)
    details = {
        "construction_audit_passed": passed,
        "artifact_rows": len(artifact_audit),
        "operation_rows": len(rounding),
        "support_to_area_rows": len(support_area),
        "candidate_polygon_rows": len(polygon_area),
    }
    return ComponentReport("construction_audit", passed, checks, details)


def run_construction_audit_replay(
    root: Path,
    archive: str | Path,
    run_id: str = "construction_audit_replay",
    log_level: str = "INFO",
) -> Path:
    """Run construction-audit replay and write a feedback archive."""
    report = check_construction_audit(root, archive)
    return write_component_outputs(
        root=root,
        run_id=run_id,
        log_name="construction_audit_replay.log",
        status_name="construction_audit_replay.status.json",
        feedback_name="construction_audit_replay_feedback.zip",
        report=report,
        archive_label=relative_label(root, resolve_archive(root, archive)),
        log_level=log_level,
    )
