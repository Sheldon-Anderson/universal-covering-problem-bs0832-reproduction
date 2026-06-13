"""Full certificate-chain replay for the public lower-bound package."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ucbs.certificate.construction_audit import check_construction_audit
from ucbs.certificate.final_adjudication import check_final_adjudication
from ucbs.certificate.per_record_evidence import check_per_record_evidence
from ucbs.certificate.validation import (
    CERTIFIED_THRESHOLD_TEXT,
    ComponentReport,
    append_log,
    check_row,
    clean_run_dir,
    failed_rows,
    make_feedback_zip,
    now_utc,
    with_summary,
    write_csv,
    write_json,
)
from ucbs.certificate.witness_construction import check_witness_construction
from ucbs.verification.artifact_checks import CertificateInputs, check_required_inputs, resolve_inputs


@dataclass(frozen=True)
class CertificateVerificationResult:
    """Outcome of the public certificate verification."""

    status: str
    certificate_verified: bool
    threshold_proved: bool
    failed_component_count: int
    output_feedback: Path


def _component_row(report: ComponentReport) -> dict[str, object]:
    return {
        "check": report.name,
        "component": report.name,
        "passed": report.passed,
        "status": "passed" if report.passed else "failed",
        "summary": f"{report.name} passed" if report.passed else f"{report.name} failed",
    }


def run_chain_checks(root: Path, inputs: CertificateInputs) -> list[ComponentReport]:
    """Run all theorem-critical component checks and return reports."""
    return [
        check_per_record_evidence(root, inputs.per_record_evidence),
        check_construction_audit(root, inputs.construction_audit),
        check_witness_construction(root, inputs.witness_construction),
        check_final_adjudication(root, inputs.final_adjudication),
    ]


def write_chain_replay(
    *,
    root: Path,
    inputs: CertificateInputs,
    run_id: str = "certificate_chain_replay",
    log_level: str = "INFO",
    feedback_name: str = "certificate_chain_replay_feedback.zip",
) -> Path:
    """Write a full certificate-chain replay run directory."""
    root = Path(root).resolve()
    run_dir = clean_run_dir(root, run_id, ["diagnostics", "status", "log", "report"])
    log = run_dir / "log" / "certificate_chain_replay.log"
    log.write_text(
        f"certificate-chain replay started {now_utc()}\n"
        "root=<repository-root>\n"
        f"run_id={run_id}\n"
        f"log_level={log_level}\n"
        f"inputs={inputs.as_jsonable()}\n",
        encoding="utf-8",
    )

    input_rows = check_required_inputs(root, inputs)
    write_csv(run_dir / "diagnostics" / "input_artifact_audit.csv", with_summary("input_artifact_audit", input_rows, "input archives are present", "input archive issue found"))
    if failed_rows(input_rows):
        reports: list[ComponentReport] = []
        component_rows = [check_row("input_artifacts", False, len(failed_rows(input_rows)), "required input archive is missing")]
    else:
        append_log(log, "running component checks")
        reports = run_chain_checks(root, inputs)
        component_rows = [_component_row(report) for report in reports]
        for report in reports:
            write_csv(run_dir / "diagnostics" / f"{report.name}_checks.csv", with_summary(report.name, report.checks, f"{report.name} checks passed", f"{report.name} check failed"))

    component_rows = with_summary("component_checks", component_rows, "all certificate-chain components passed", "certificate-chain component failed")
    write_csv(run_dir / "diagnostics" / "component_checks.csv", component_rows)
    failed = failed_rows(component_rows)
    write_csv(
        run_dir / "diagnostics" / "failed_component_checks.csv",
        failed if failed else [{"check": "failed_component_checks_summary", "issue_count": 0, "passed": True, "summary": "no failed component check found"}],
    )

    failed_component_count = sum(1 for row in component_rows if not str(row.get("check", "")).endswith("_summary") and not bool(row.get("passed")))
    passed = failed_component_count == 0 and not failed_rows(input_rows)
    status_payload = {
        "schema": "ucbs-certificate-chain-replay-v1",
        "status": "passed" if passed else "failed",
        "certificate_verified": passed,
        "threshold_proved": passed,
        "certified_threshold": CERTIFIED_THRESHOLD_TEXT,
        "run_id": run_id,
        "timestamp_utc": now_utc(),
        "component_count": 4,
        "failed_component_count": failed_component_count,
        "per_record_evidence_passed": any(report.name == "per_record_evidence" and report.passed for report in reports),
        "construction_audit_passed": any(report.name == "construction_audit" and report.passed for report in reports),
        "witness_construction_passed": any(report.name == "witness_construction" and report.passed for report in reports),
        "final_adjudication_passed": any(report.name == "final_adjudication" and report.passed for report in reports),
        "input_archives": inputs.as_jsonable(),
    }
    write_json(run_dir / "status" / "certificate_chain_replay.status.json", status_payload)
    write_json(run_dir / "summary.json", status_payload)
    (run_dir / "report" / "certificate_chain_replay.md").write_text(
        "# Certificate-chain replay\n\n"
        f"Status: `{'passed' if passed else 'failed'}`.\n\n"
        f"Certified threshold: `{CERTIFIED_THRESHOLD_TEXT}`.\n",
        encoding="utf-8",
    )
    append_log(log, f"certificate-chain replay status={'passed' if passed else 'failed'}")
    return make_feedback_zip(run_dir, feedback_name)


def verify_certificate(
    root: Path,
    artifact_root: str | None = None,
    per_record_evidence_zip: str | None = None,
    construction_audit_zip: str | None = None,
    witness_construction_zip: str | None = None,
    final_adjudication_zip: str | None = None,
    run_id: str = "certificate_verification",
    log_level: str = "INFO",
) -> CertificateVerificationResult:
    """Run the public certificate verification and write feedback."""
    root = Path(root).resolve()
    inputs = resolve_inputs(
        root,
        artifact_root,
        per_record_evidence_zip=per_record_evidence_zip,
        construction_audit_zip=construction_audit_zip,
        witness_construction_zip=witness_construction_zip,
        final_adjudication_zip=final_adjudication_zip,
    )
    run_dir = clean_run_dir(root, run_id, ["diagnostics", "status", "log", "report"])
    log = run_dir / "log" / "certificate_verification.log"
    log.write_text(
        f"certificate verification started {now_utc()}\n"
        "root=<repository-root>\n"
        f"run_id={run_id}\n"
        f"log_level={log_level}\n"
        f"inputs={inputs.as_jsonable()}\n",
        encoding="utf-8",
    )

    input_rows = check_required_inputs(root, inputs)
    write_csv(run_dir / "diagnostics" / "input_artifact_audit.csv", with_summary("input_artifact_audit", input_rows, "input archives are present", "input archive issue found"))
    reports = [] if failed_rows(input_rows) else run_chain_checks(root, inputs)
    component_rows = [_component_row(report) for report in reports] if reports else [check_row("input_artifacts", False, len(failed_rows(input_rows)), "required input archive is missing")]
    component_rows = with_summary("component_checks", component_rows, "all certificate-chain components passed", "certificate-chain component failed")
    write_csv(run_dir / "diagnostics" / "component_checks.csv", component_rows)
    for report in reports:
        write_csv(run_dir / "diagnostics" / f"{report.name}_checks.csv", with_summary(report.name, report.checks, f"{report.name} checks passed", f"{report.name} check failed"))
    failed = failed_rows(component_rows)
    write_csv(
        run_dir / "diagnostics" / "failed_component_checks.csv",
        failed if failed else [{"check": "failed_component_checks_summary", "issue_count": 0, "passed": True, "summary": "no failed component check found"}],
    )
    failed_component_count = sum(1 for row in component_rows if not str(row.get("check", "")).endswith("_summary") and not bool(row.get("passed")))
    passed = failed_component_count == 0 and not failed_rows(input_rows)
    status_payload = {
        "schema": "ucbs-certificate-verification-v1",
        "status": "passed" if passed else "failed",
        "certificate_verified": passed,
        "threshold_proved": passed,
        "certified_threshold": CERTIFIED_THRESHOLD_TEXT,
        "run_id": run_id,
        "timestamp_utc": now_utc(),
        "component_count": 4,
        "failed_component_count": failed_component_count,
        "per_record_evidence_passed": any(report.name == "per_record_evidence" and report.passed for report in reports),
        "construction_audit_passed": any(report.name == "construction_audit" and report.passed for report in reports),
        "witness_construction_passed": any(report.name == "witness_construction" and report.passed for report in reports),
        "final_adjudication_passed": any(report.name == "final_adjudication" and report.passed for report in reports),
        "input_archives": inputs.as_jsonable(),
    }
    write_json(run_dir / "status" / "certificate_verification.status.json", status_payload)
    write_json(run_dir / "summary.json", status_payload)
    (run_dir / "report" / "certificate_verification.md").write_text(
        "# Certificate verification\n\n"
        f"Status: `{'passed' if passed else 'failed'}`.\n\n"
        f"Certified threshold: `{CERTIFIED_THRESHOLD_TEXT}`.\n",
        encoding="utf-8",
    )
    append_log(log, f"certificate verification status={'passed' if passed else 'failed'}")
    feedback = make_feedback_zip(run_dir, "certificate_verification_feedback.zip")
    return CertificateVerificationResult("passed" if passed else "failed", passed, passed, failed_component_count, feedback)


def resolve_default_inputs(root: Path, artifact_root: str | None = None, **kwargs: str | None) -> CertificateInputs:
    """Convenience wrapper around the public artifact resolver."""
    return resolve_inputs(root, artifact_root, **kwargs)
