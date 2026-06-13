"""Replay checks for the witness-construction certificate archive.

This module verifies schema, row counts, terminal-subdomain evidence,
orientation estimates, and shoelace lower bounds from the bundled
witness-construction records. It does not rerun the original geometric search
that produced those records.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

from ucbs.certificate.archive_io import (
    read_csv_member,
    read_json_member,
    relative_label,
    require_members,
    resolve_archive,
)
from ucbs.certificate.validation import (
    CERTIFIED_THRESHOLD,
    ComponentReport,
    check_row,
    require_columns,
    require_exact_count,
    require_unique_keys,
    threshold_cleared,
    truthy,
    write_component_outputs,
)

EXPECTED_WITNESS_DOMAINS = 16
"""Number of witness domains in the bundled finite certificate."""

EXPECTED_ACCEPTED_TERMINAL_SUBDOMAINS = 140
"""Number of accepted terminal subdomains in witness-construction records."""

EXPECTED_ROWS_PER_ACCEPTED_SUBDOMAIN = 8
"""Number of witness-point and orientation rows per accepted subdomain."""

EXPECTED_ACCEPTED_EVIDENCE_ROWS = (
    EXPECTED_ACCEPTED_TERMINAL_SUBDOMAINS
    * EXPECTED_ROWS_PER_ACCEPTED_SUBDOMAIN
)
"""Expected accepted witness-point and orientation rows."""

EXPECTED_POINT_CONTAINMENT_ROWS = 2112
"""Total point-containment rows in the bundled witness-construction archive."""

EXPECTED_ORIENTATION_ROWS = 2112
"""Total orientation rows in the bundled witness-construction archive."""

EXPECTED_SHOELACE_ROWS = 264
"""Total shoelace rows, including intermediate adaptive-refinement rows."""

EXPECTED_SUMMARY_ROWS = 17
"""Global witness summary row plus one row for each witness domain."""

EXPECTED_ROUNDING_ROWS = 128
"""Operation-level rounding rows in the witness-construction archive."""

REQUIRED_MEMBERS = [
    "diagnostics/v135_point_in_source_object_certificate.csv",
    "diagnostics/v135_orientation_determinant_ledger.csv",
    "diagnostics/v135_interval_shoelace_area_certificate.csv",
    "diagnostics/v135_inner_polygon_area_lower_bound_summary.csv",
    "diagnostics/v135_witness_convex_order_audit.csv",
    "diagnostics/v135_operation_level_arb_rounding_ledger.csv",
    "status/v135.status.json",
]

POINT_COLUMNS = {
    "patch_record_id",
    "subbox_id",
    "witness_label",
    "source_object",
    "point_in_source_object_status",
}
ORIENTATION_COLUMNS = {
    "patch_record_id",
    "subbox_id",
    "orientation_index",
    "orientation_interval_lo",
    "orientation_status",
}
SHOELACE_COLUMNS = {
    "patch_record_id",
    "subbox_id",
    "shoelace_area_lower_bound",
    "target_bound",
    "min_orientation_lower",
    "convex_order_certified",
    "inner_polygon_subbox_passed",
    "subbox_status",
}
SUMMARY_COLUMNS = {
    "patch_record_count",
    "inner_polygon_passed_patch_count",
    "inner_polygon_failed_patch_count",
    "inner_polygon_kernel_passed",
    "patch_record_id",
    "accepted_subbox_count",
    "failed_subbox_count",
    "inner_polygon_patch_passed",
    "patch_status",
}
ORDER_COLUMNS = {
    "patch_record_id",
    "accepted_subbox_count",
    "failed_subbox_count",
    "inner_polygon_patch_passed",
    "patch_status",
}
ROUNDING_COLUMNS = {
    "operation_id",
    "patch_record_id",
    "contains_target_bound",
    "arb_status",
    "proof_status",
}


def _accepted_shoelace_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return terminal shoelace rows accepted by the adaptive replay."""
    return [
        row
        for row in rows
        if str(row.get("subbox_status", "")).strip().lower() == "passed"
    ]


def _positive_decimal(value: str) -> bool:
    """Return whether a serialized decimal is strictly positive."""
    try:
        return Decimal(str(value)) > Decimal("0")
    except (InvalidOperation, TypeError, ValueError):
        # Unparsable numeric fields fail positivity checks.
        return False


def _ids(rows: list[dict[str, str]], field: str) -> set[str]:
    """Return nonempty identifiers appearing in a CSV field."""
    return {row.get(field, "") for row in rows if row.get(field, "")}


def _rows_for_subbox(
    rows: list[dict[str, str]],
    subbox_id: str,
) -> list[dict[str, str]]:
    """Return rows attached to one accepted terminal subdomain."""
    return [row for row in rows if row.get("subbox_id") == subbox_id]


def _accepted_evidence_counts_match(
    accepted_points: list[dict[str, str]],
    accepted_orientation: list[dict[str, str]],
    accepted_subboxes: set[str],
) -> bool:
    """Check the expected witness and orientation row counts per subdomain."""
    for subbox_id in accepted_subboxes:
        if len(_rows_for_subbox(accepted_points, subbox_id)) != EXPECTED_ROWS_PER_ACCEPTED_SUBDOMAIN:
            return False
        if len(_rows_for_subbox(accepted_orientation, subbox_id)) != EXPECTED_ROWS_PER_ACCEPTED_SUBDOMAIN:
            return False
    return True


def check_witness_construction(root: Path, archive: str | Path) -> ComponentReport:
    """Check witness-construction records from one bundled archive.

    The checks enforce expected schemas, exact row counts, unique keys, and the
    terminal-subdomain evidence needed by the certified lower bound. Intermediate
    adaptive-refinement rows are allowed but do not count as final failures.
    """
    path = resolve_archive(root, archive)
    checks: list[dict[str, object]] = []
    if not path.exists():
        checks.append(
            check_row(
                "archive_exists",
                False,
                relative_label(root, path),
                "archive is missing",
            )
        )
        return ComponentReport(
            "witness_construction",
            False,
            checks,
            {"witness_construction_passed": False},
        )

    checks.append(
        check_row(
            "archive_exists",
            True,
            relative_label(root, path),
            "archive is present",
        )
    )
    member_rows = require_members(path, REQUIRED_MEMBERS)
    checks.extend(member_rows)
    if not all(truthy(row.get("passed")) for row in member_rows):
        return ComponentReport(
            "witness_construction",
            False,
            checks,
            {"witness_construction_passed": False},
        )

    status = read_json_member(path, "status/v135.status.json")
    point_rows = read_csv_member(
        path,
        "diagnostics/v135_point_in_source_object_certificate.csv",
    )
    orientation_rows = read_csv_member(
        path,
        "diagnostics/v135_orientation_determinant_ledger.csv",
    )
    shoelace_rows = read_csv_member(
        path,
        "diagnostics/v135_interval_shoelace_area_certificate.csv",
    )
    summary_rows = read_csv_member(
        path,
        "diagnostics/v135_inner_polygon_area_lower_bound_summary.csv",
    )
    order_rows = read_csv_member(
        path,
        "diagnostics/v135_witness_convex_order_audit.csv",
    )
    rounding_rows = read_csv_member(
        path,
        "diagnostics/v135_operation_level_arb_rounding_ledger.csv",
    )

    checks.extend(require_columns(point_rows, POINT_COLUMNS, "point_containment_rows"))
    checks.extend(require_columns(orientation_rows, ORIENTATION_COLUMNS, "orientation_rows"))
    checks.extend(require_columns(shoelace_rows, SHOELACE_COLUMNS, "shoelace_rows"))
    checks.extend(require_columns(summary_rows, SUMMARY_COLUMNS, "witness_summary_rows"))
    checks.extend(require_columns(order_rows, ORDER_COLUMNS, "convex_order_audit_rows"))
    checks.extend(require_columns(rounding_rows, ROUNDING_COLUMNS, "witness_rounding_rows"))

    checks.extend(
        [
            require_exact_count(
                point_rows,
                EXPECTED_POINT_CONTAINMENT_ROWS,
                "point_containment_rows",
            ),
            require_exact_count(
                orientation_rows,
                EXPECTED_ORIENTATION_ROWS,
                "orientation_rows",
            ),
            require_exact_count(shoelace_rows, EXPECTED_SHOELACE_ROWS, "shoelace_rows"),
            require_exact_count(summary_rows, EXPECTED_SUMMARY_ROWS, "witness_summary_rows"),
            require_exact_count(order_rows, EXPECTED_WITNESS_DOMAINS, "convex_order_audit_rows"),
            require_exact_count(rounding_rows, EXPECTED_ROUNDING_ROWS, "witness_rounding_rows"),
            require_unique_keys(
                point_rows,
                ["subbox_id", "witness_label"],
                "point_containment_rows",
            ),
            require_unique_keys(
                orientation_rows,
                ["subbox_id", "orientation_index"],
                "orientation_rows",
            ),
            require_unique_keys(shoelace_rows, ["subbox_id"], "shoelace_rows"),
            require_unique_keys(order_rows, ["patch_record_id"], "convex_order_audit_rows"),
            require_unique_keys(rounding_rows, ["operation_id"], "witness_rounding_rows"),
        ]
    )

    summary_global = summary_rows[0] if summary_rows else {}
    patch_rows = [row for row in summary_rows[1:] if row.get("patch_record_id")]
    accepted_rows = _accepted_shoelace_rows(shoelace_rows)
    accepted_subboxes = _ids(accepted_rows, "subbox_id")
    accepted_orientation = [
        row for row in orientation_rows if row.get("subbox_id") in accepted_subboxes
    ]
    accepted_points = [
        row for row in point_rows if row.get("subbox_id") in accepted_subboxes
    ]
    point_subboxes = _ids(accepted_points, "subbox_id")
    orientation_subboxes = _ids(accepted_orientation, "subbox_id")

    final_failed_subdomains = sum(
        int(row.get("failed_subbox_count", "0") or 0) for row in patch_rows
    )
    checks.extend(
        [
            check_row(
                "summary_global_passed",
                truthy(summary_global.get("inner_polygon_kernel_passed")),
                summary_global.get("inner_polygon_kernel_status"),
                "global witness summary is passed",
            ),
            check_row(
                "witness_domain_count",
                len(patch_rows) == EXPECTED_WITNESS_DOMAINS,
                len(patch_rows),
                "sixteen witness domains are summarized",
            ),
            check_row(
                "witness_domains_passed",
                all(
                    truthy(row.get("inner_polygon_patch_passed"))
                    and str(row.get("patch_status", "")).lower() == "passed"
                    for row in patch_rows
                ),
                len(patch_rows),
                "all witness-domain summaries pass",
            ),
            check_row(
                "witness_domain_failed_counts_zero",
                final_failed_subdomains == 0,
                final_failed_subdomains,
                "witness-domain summaries record zero final unresolved subdomains",
            ),
            check_row(
                "accepted_terminal_subdomains_present",
                len(accepted_rows) == EXPECTED_ACCEPTED_TERMINAL_SUBDOMAINS,
                len(accepted_rows),
                "accepted terminal subdomains match the certificate summary",
            ),
            check_row(
                "accepted_subbox_ids_unique",
                len(accepted_subboxes) == len(accepted_rows),
                len(accepted_subboxes),
                "accepted terminal subdomain IDs are unique",
            ),
            check_row(
                "accepted_point_rows_match",
                len(accepted_points) == EXPECTED_ACCEPTED_EVIDENCE_ROWS
                and point_subboxes == accepted_subboxes,
                len(accepted_points),
                "each accepted terminal subdomain has point-containment rows",
            ),
            check_row(
                "accepted_orientation_rows_match",
                len(accepted_orientation) == EXPECTED_ACCEPTED_EVIDENCE_ROWS
                and orientation_subboxes == accepted_subboxes,
                len(accepted_orientation),
                "each accepted terminal subdomain has orientation rows",
            ),
            check_row(
                "accepted_evidence_row_count_per_subbox",
                _accepted_evidence_counts_match(
                    accepted_points,
                    accepted_orientation,
                    accepted_subboxes,
                ),
                len(accepted_subboxes),
                "each accepted terminal subdomain has eight witness and orientation rows",
            ),
            check_row(
                "accepted_shoelace_bounds_clear_threshold",
                all(
                    threshold_cleared(row.get("shoelace_area_lower_bound"), CERTIFIED_THRESHOLD)
                    for row in accepted_rows
                ),
                len(accepted_rows),
                "all accepted shoelace lower bounds clear the threshold",
            ),
            check_row(
                "accepted_orientation_positive",
                all(_positive_decimal(row.get("min_orientation_lower", "")) for row in accepted_rows),
                len(accepted_rows),
                "all accepted terminal subdomains have positive orientation lower bounds",
            ),
            check_row(
                "accepted_convex_order_certified",
                all(truthy(row.get("convex_order_certified")) for row in accepted_rows),
                len(accepted_rows),
                "all accepted terminal subdomains have a certified cyclic order",
            ),
            check_row(
                "accepted_subbox_flags_passed",
                all(truthy(row.get("inner_polygon_subbox_passed")) for row in accepted_rows),
                len(accepted_rows),
                "all accepted terminal subdomain flags pass",
            ),
            check_row(
                "accepted_orientation_rows_passed",
                all(
                    str(row.get("orientation_status", "")).lower() == "passed"
                    for row in accepted_orientation
                ),
                len(accepted_orientation),
                "orientation rows for accepted terminal subdomains pass",
            ),
            check_row(
                "point_containment_passed",
                all(
                    str(row.get("point_in_source_object_status", "")).startswith("passed")
                    for row in accepted_points
                ),
                len(accepted_points),
                "point-containment rows for accepted terminal subdomains pass",
            ),
            check_row(
                "order_audit_rows_passed",
                all(
                    truthy(row.get("inner_polygon_patch_passed"))
                    and str(row.get("patch_status", "")).lower() == "passed"
                    for row in order_rows
                ),
                len(order_rows),
                "witness cyclic-order audit rows pass",
            ),
            check_row(
                "rounding_rows_certified",
                all(
                    str(row.get("arb_status", "")).lower() == "available"
                    and str(row.get("proof_status", "")).lower()
                    == "proof_grade_operation_row"
                    and truthy(row.get("contains_target_bound"))
                    for row in rounding_rows
                ),
                len(rounding_rows),
                "operation-level rounding rows are proof-grade rows",
            ),
            check_row(
                "status_success",
                str(status.get("status", "")).strip().lower()
                == "success_gate_passed_for_final_adjudication",
                status.get("status"),
                "status records success for final adjudication",
            ),
            check_row(
                "status_witness_certificate_passed",
                truthy(status.get("explicit_inner_witness_certificate_passed")),
                status.get("explicit_inner_witness_certificate_passed"),
                "status records accepted witness certificate",
            ),
        ]
    )

    status_failed_value = status.get(
        "terminal_failed_subbox_count",
        status.get("inner_polygon_failed_patch_count", ""),
    )
    checks.append(
        check_row(
            "status_terminal_failed_zero",
            str(status_failed_value) == "0",
            status_failed_value,
            "status records zero final failed witness domains or terminal subdomains",
        )
    )

    passed = not any(not truthy(row.get("passed")) for row in checks)
    details = {
        "witness_construction_passed": passed,
        "witness_domains": len(patch_rows),
        "accepted_terminal_subdomains": len(accepted_rows),
        "failed_terminal_subdomains": final_failed_subdomains,
        "point_containment_passed": all(
            str(row.get("point_in_source_object_status", "")).startswith("passed")
            for row in accepted_points
        ),
        "orientation_certificates_passed": all(
            str(row.get("orientation_status", "")).lower() == "passed"
            for row in accepted_orientation
        ),
        "shoelace_lower_bounds_passed": all(
            threshold_cleared(row.get("shoelace_area_lower_bound"), CERTIFIED_THRESHOLD)
            for row in accepted_rows
        ),
        "intermediate_split_rows_ignored_as_nonterminal": len(shoelace_rows)
        - len(accepted_rows),
    }
    return ComponentReport("witness_construction", passed, checks, details)


def run_witness_construction_replay(
    root: Path,
    archive: str | Path,
    run_id: str = "witness_construction_replay",
    log_level: str = "INFO",
) -> Path:
    """Run witness-construction replay and write a feedback archive."""
    report = check_witness_construction(root, archive)
    return write_component_outputs(
        root=root,
        run_id=run_id,
        log_name="witness_construction_replay.log",
        status_name="witness_construction_replay.status.json",
        feedback_name="witness_construction_replay_feedback.zip",
        report=report,
        archive_label=relative_label(root, resolve_archive(root, archive)),
        log_level=log_level,
    )
