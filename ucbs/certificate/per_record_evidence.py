"""Replay checks for the per-record evidence certificate archive.

This module verifies schema, row counts, component closure, and source-row
blocking status from the bundled per-record evidence records. It does not
rerun the original geometric search that produced those records.
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
    require_unique_keys,
    status_passed,
    truthy,
    write_component_outputs,
)

REQUIRED_MEMBERS = [
    "diagnostics/v133_row_level_evidence_closure_summary.csv",
    "diagnostics/v133_directed_interval_row_closure.csv",
    "diagnostics/v133_local_tensor_row_closure.csv",
    "diagnostics/v133_h004_bridge_row_closure.csv",
    "diagnostics/v133_missing_row_source_blockers.csv",
    "status/v133.status.json",
]

EXPECTED_COMPONENTS = {
    "directed_interval_component",
    "local_tensor_component",
    "h004_bridge_component",
}

SUMMARY_COLUMNS = {"component_id", "row_level_closure_passed", "closure_status", "selected_row_count"}
ROW_CLOSURE_COLUMNS = {"component_id", "row_level_closure_passed", "closure_status"}


def _closure_rows_pass(rows: list[dict[str, str]], expected_components: set[str]) -> bool:
    found = {row.get("component_id", "") for row in rows if row}
    return expected_components.issubset(found) and all(
        truthy(row.get("row_level_closure_passed")) and str(row.get("closure_status", "")).strip().lower() == "closed"
        for row in rows if row
    )


def _selected_count(rows: list[dict[str, str]]) -> int:
    total = 0
    for row in rows:
        try:
            total += int(row.get("selected_row_count", "0") or 0)
        except ValueError:
            return 0
    return total


def check_per_record_evidence(root: Path, archive: str | Path) -> ComponentReport:
    """Check the per-record evidence archive."""
    path = resolve_archive(root, archive)
    checks = []
    if not path.exists():
        checks.append(check_row("archive_exists", False, relative_label(root, path), "archive is missing"))
        return ComponentReport("per_record_evidence", False, checks, {"per_record_evidence_passed": False})

    checks.append(check_row("archive_exists", True, relative_label(root, path), "archive is present"))
    member_rows = require_members(path, REQUIRED_MEMBERS)
    checks.extend(member_rows)
    if not all(truthy(row.get("passed")) for row in member_rows):
        return ComponentReport("per_record_evidence", False, checks, {"per_record_evidence_passed": False})

    status = read_json_member(path, "status/v133.status.json")
    summary = read_csv_member(path, "diagnostics/v133_row_level_evidence_closure_summary.csv")
    directed = read_csv_member(path, "diagnostics/v133_directed_interval_row_closure.csv")
    tensor = read_csv_member(path, "diagnostics/v133_local_tensor_row_closure.csv")
    bridge = read_csv_member(path, "diagnostics/v133_h004_bridge_row_closure.csv")
    missing = read_csv_member(path, "diagnostics/v133_missing_row_source_blockers.csv")

    checks.extend(require_columns(summary, SUMMARY_COLUMNS, "per_record_summary"))
    checks.extend(require_columns(directed, ROW_CLOSURE_COLUMNS, "directed_interval_rows"))
    checks.extend(require_columns(tensor, ROW_CLOSURE_COLUMNS, "tensor_rows"))
    checks.extend(require_columns(bridge, ROW_CLOSURE_COLUMNS, "bridge_rows"))
    checks.append(require_exact_count(summary, 3, "per_record_summary"))
    checks.append(require_exact_count(directed, 1, "directed_interval_rows"))
    checks.append(require_exact_count(tensor, 1, "tensor_rows"))
    checks.append(require_exact_count(bridge, 1, "bridge_rows"))
    checks.append(require_unique_keys(summary, ["component_id"], "per_record_summary"))

    found_components = {row.get("component_id", "") for row in summary}
    checks.append(check_row("expected_component_set", found_components == EXPECTED_COMPONENTS, ";".join(sorted(found_components)), "expected per-record evidence component set is present"))
    checks.append(check_row("summary_components_closed", _closure_rows_pass(summary, EXPECTED_COMPONENTS), len(summary), "all required closure summary components are closed"))
    checks.append(check_row("directed_interval_closed", _closure_rows_pass(directed, {"directed_interval_component"}), len(directed), "directed interval rows are closed"))
    checks.append(check_row("local_tensor_closed", _closure_rows_pass(tensor, {"local_tensor_component"}), len(tensor), "local tensor rows are closed"))
    checks.append(check_row("bridge_closed", _closure_rows_pass(bridge, {"h004_bridge_component"}), len(bridge), "bridge rows are closed"))
    checks.append(check_row("missing_row_source_blockers_empty", len(missing) == 0, len(missing), "no missing row-source blockers remain"))
    checks.append(check_row("selected_rows_positive", _selected_count(summary) > 0, _selected_count(summary), "selected evidence row count is positive"))
    checks.append(check_row("status_row_level_evidence_closed", truthy(status.get("row_level_evidence_closed")), status.get("row_level_evidence_closed"), "status records closed individual evidence"))
    checks.append(check_row("status_evidence_blockers_zero", str(status.get("evidence_blocker_count", "")) == "0", status.get("evidence_blocker_count"), "status records zero evidence blockers"))
    checks.append(check_row("status_value_accepted", status_passed(status.get("status")) or str(status.get("status", "")).startswith("success"), status.get("status"), "status records a successful evidence-closure run"))

    passed = not any(not truthy(row.get("passed")) for row in checks)
    report_details = {
        "per_record_evidence_passed": passed,
        "closure_rows": len(summary),
        "failed_rows": 0 if len(missing) == 0 else len(missing),
        "selected_row_count_total": _selected_count(summary),
    }
    return ComponentReport("per_record_evidence", passed, checks, report_details)


def run_per_record_evidence_replay(
    root: Path,
    archive: str | Path,
    run_id: str = "per_record_evidence_replay",
    log_level: str = "INFO",
) -> Path:
    """Run the per-record evidence replay and write a feedback archive."""
    report = check_per_record_evidence(root, archive)
    return write_component_outputs(
        root=root,
        run_id=run_id,
        log_name="per_record_evidence_replay.log",
        status_name="per_record_evidence_replay.status.json",
        feedback_name="per_record_evidence_replay_feedback.zip",
        report=report,
        archive_label=relative_label(root, resolve_archive(root, archive)),
        log_level=log_level,
    )
