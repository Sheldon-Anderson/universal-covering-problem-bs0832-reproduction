"""Shared validation helpers for certificate-chain replay modules."""
from __future__ import annotations

import csv
import json
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

DiagnosticRow = dict[str, Any]
"""One diagnostic row written to a CSV file."""

CsvRow = dict[str, str]
"""One row read from a certificate CSV file."""

CERTIFIED_THRESHOLD = Decimal("0.83201")
CERTIFIED_THRESHOLD_TEXT = "0.83201"


@dataclass
class ComponentReport:
    """Structured outcome for one certificate-chain component."""

    name: str
    passed: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def now_utc() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def truthy(value: Any) -> bool:
    """Interpret common serialized Boolean and status values."""
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "passed",
        "pass",
        "ok",
        "closed",
        "discharged",
        "present",
        "present_locked",
    }


def status_passed(value: Any) -> bool:
    """Return whether a serialized status value is a passing status."""
    return str(value).strip().lower() in {
        "passed",
        "pass",
        "ok",
        "closed",
        "discharged",
        "present",
        "present_locked",
        "empty",
        "clean",
        "success",
        "success_gate_passed_for_final_adjudication",
    }


def to_decimal(value: Any) -> Decimal | None:
    """Parse a decimal value, returning None on empty or invalid input."""
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def threshold_cleared(value: Any, threshold: Decimal = CERTIFIED_THRESHOLD) -> bool:
    """Return whether a serialized decimal is at least the certified threshold."""
    parsed = to_decimal(value)
    return parsed is not None and parsed >= threshold


def check_row(
    check: str,
    passed: bool,
    value: Any = "",
    summary: str = "",
    **extra: Any,
) -> DiagnosticRow:
    """Build one diagnostic row for a replay or repository-check table."""
    row = {"check": check, "passed": bool(passed), "value": value, "summary": summary}
    row.update(extra)
    return row


def failed_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect rows whose passed field is false-like."""
    failed: list[dict[str, Any]] = []
    for row in rows:
        if "passed" in row and not truthy(row["passed"]):
            failed.append(row)
    return failed


def summary_row(
    name: str,
    rows: Iterable[DiagnosticRow],
    ok: str,
    bad: str,
) -> DiagnosticRow:
    """Return a standard summary row for a diagnostic table."""
    failures = failed_rows(rows)
    return {
        "check": f"{name}_summary",
        "issue_count": len(failures),
        "passed": len(failures) == 0,
        "summary": ok if not failures else bad,
    }


def with_summary(name: str, rows: list[dict[str, Any]], ok: str, bad: str) -> list[dict[str, Any]]:
    """Append a standard summary row to diagnostic rows."""
    return [*rows, summary_row(name, rows, ok, bad)]


def write_csv(
    path: Path,
    rows: Iterable[DiagnosticRow],
    fieldnames: list[str] | None = None,
) -> None:
    """Write rows to CSV with a deterministic header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fields: list[str] = list(fieldnames or [])
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ["check", "issue_count", "passed", "summary"]
        rows = [{"check": "empty_summary", "issue_count": 0, "passed": True, "summary": "no rows produced"}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def append_log(path: Path, message: str) -> None:
    """Append one timestamped line to a log file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now_utc()}] {message}\n")


def clean_run_dir(root: Path, run_id: str, subdirs: Iterable[str]) -> Path:
    """Create a clean run directory under runs/."""
    run_dir = root / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    for subdir in subdirs:
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)
    return run_dir


def make_feedback_zip(run_dir: Path, name: str) -> Path:
    """Create a feedback ZIP containing all files in a run directory."""
    feedback = run_dir / name
    with zipfile.ZipFile(feedback, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(run_dir.rglob("*")):
            if path.is_file() and path != feedback:
                archive.write(path, path.relative_to(run_dir).as_posix())
    return feedback



def require_columns(
    rows: list[dict[str, Any]],
    columns: set[str],
    table: str,
) -> list[DiagnosticRow]:
    """Return schema diagnostic rows for a required certificate CSV table."""
    if not rows:
        return [check_row(f"{table}_nonempty", False, 0, f"{table} must not be empty")]
    observed = set().union(*(row.keys() for row in rows)) if rows else set()
    missing = sorted(columns - observed)
    rows_out = [check_row(f"{table}_nonempty", True, len(rows), f"{table} has rows")]
    rows_out.append(
        check_row(
            f"{table}_schema",
            not missing,
            ";".join(missing),
            f"{table} contains required columns"
            if not missing
            else f"{table} is missing required columns",
        )
    )
    return rows_out


def require_exact_count(rows: list[dict[str, Any]], expected: int, table: str) -> dict[str, Any]:
    """Return a diagnostic row for an exact row-count invariant."""
    return check_row(f"{table}_expected_count", len(rows) == expected, len(rows), f"{table} has expected row count {expected}")


def require_min_count(rows: list[dict[str, Any]], minimum: int, table: str) -> dict[str, Any]:
    """Return a diagnostic row for a minimum row-count invariant."""
    return check_row(f"{table}_minimum_count", len(rows) >= minimum, len(rows), f"{table} has at least {minimum} rows")


def duplicate_key_values(rows: list[dict[str, Any]], keys: list[str]) -> list[str]:
    """Return duplicate composite-key values from a CSV table."""
    seen: set[str] = set()
    duplicates: list[str] = []
    for row in rows:
        value = "|".join(str(row.get(key, "")) for key in keys)
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def require_unique_keys(rows: list[dict[str, Any]], keys: list[str], table: str) -> dict[str, Any]:
    """Return a diagnostic row requiring a unique composite key."""
    duplicates = duplicate_key_values(rows, keys)
    return check_row(
        f"{table}_unique_key",
        not duplicates,
        len(duplicates),
        f"{table} has unique key {','.join(keys)}",
        duplicate_keys=";".join(duplicates[:10]),
    )


def require_expected_values(rows: list[dict[str, Any]], field: str, expected: set[str], table: str) -> dict[str, Any]:
    """Return a diagnostic row requiring all values in a field to match an expected set."""
    bad = sorted({str(row.get(field, "")) for row in rows if str(row.get(field, "")) not in expected})
    return check_row(
        f"{table}_{field}_expected_values",
        not bad,
        ";".join(bad),
        f"{table}.{field} values are expected",
    )


def write_component_outputs(
    *,
    root: Path,
    run_id: str,
    log_name: str,
    status_name: str,
    feedback_name: str,
    report: ComponentReport,
    archive_label: str,
    log_level: str,
) -> Path:
    """Write a standard component replay run directory.

    Args:
        root: Repository root.
        run_id: Name of the output directory under ``runs``.
        log_name: Name of the component log file.
        status_name: Name of the component status JSON file.
        feedback_name: Name of the feedback ZIP to create.
        report: Component verification result.
        archive_label: Repository-relative archive label for logs and status files.
        log_level: Logging-level label stored in the component log.

    Returns:
        Path to the generated feedback ZIP.
    """
    run_dir = clean_run_dir(root, run_id, ["diagnostics", "status", "log", "report"])
    log_path = run_dir / "log" / log_name
    log_path.write_text(
        f"component replay started {now_utc()}\n"
        "root=<repository-root>\n"
        f"run_id={run_id}\n"
        f"component={report.name}\n"
        f"archive={archive_label}\n"
        f"log_level={log_level}\n",
        encoding="utf-8",
    )
    append_log(log_path, f"component checks collected: {len(report.checks)}")
    checks = with_summary(report.name, report.checks, f"{report.name} checks passed", f"{report.name} check failed")
    write_csv(run_dir / "diagnostics" / f"{report.name}_checks.csv", checks)
    failed = failed_rows(checks)
    write_csv(
        run_dir / "diagnostics" / f"{report.name}_failed_checks.csv",
        failed if failed else [{"check": f"{report.name}_failed_checks_summary", "issue_count": 0, "passed": True, "summary": "no failed component check found"}],
    )
    status = {
        "schema": f"ucbs-{report.name}-replay-v1",
        "status": "passed" if report.passed else "failed",
        "component": report.name,
        "run_id": run_id,
        "timestamp_utc": now_utc(),
        "archive": archive_label,
        "certified_threshold": CERTIFIED_THRESHOLD_TEXT,
        **report.details,
    }
    write_json(run_dir / "status" / status_name, status)
    (run_dir / "report" / f"{report.name}_replay.md").write_text(
        f"# {report.name.replace('_', ' ').title()} replay\n\n"
        f"Status: `{'passed' if report.passed else 'failed'}`.\n\n"
        f"Archive: `{archive_label}`.\n",
        encoding="utf-8",
    )
    append_log(log_path, f"component status={'passed' if report.passed else 'failed'}")
    return make_feedback_zip(run_dir, feedback_name)
