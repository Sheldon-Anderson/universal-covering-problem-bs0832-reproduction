"""v0.10.7 BS0832 final theorem release-candidate and independent review bundle.

This step takes the v0.10.6 dry-freeze candidate and makes the largest
proof-boundary-safe move that is still reasonable on a Windows laptop:

1. Re-read the original v096/v097/v086/v050/v105/v106 artifacts.  The final
   review decision does not merely trust v106's summary.
2. Perform fresh independent replay checks for Branch-B domain closure, G2
   directed/external-Arb candidate kernel, G3 local tensor theorem candidate,
   and h004 bridge binding.
3. Perform full row-order-preserving block-hash audits instead of writing huge
   per-route/per-kernel CSV tables by default.
4. Generate a BS0832 theorem release-candidate review bundle and Appendix A-E
   final checklists.

Strict boundary: this script may set theorem_release_candidate=true and
bs0832_release_candidate_ready=true, but it intentionally keeps theorem_ready,
bs0832_reproduced_theorem_level, target_083201_proved, and formal theorem flags
false.  It does not prove the 0.832 theorem by itself and does not prove 0.83201.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from app.domain.adaptive_global_v106 import (
    VERSION as V106_VERSION,
    ARTIFACT_PREFIX as V106_PREFIX,
    FEEDBACK_NAME as V106_FEEDBACK_NAME,
    REFERENCE_COUNTS,
    EXPECTED_ROUTE_COUNTS,
    STRICT_BOUNDARY_FLAGS,
    V105,
    V096,
    LEDGER,
    V097,
    V086,
    V050,
    now_utc,
    _nt_long_path,
    ensure_parent,
    ensure_dirs as ensure_dirs_v106,
    write_csv,
    write_json,
    write_text,
    log_line,
    sha256_file,
    decimal_of,
    boolish,
    zip_has,
    read_json_from_zip,
    iter_csv_from_zip,
    csv_header_from_zip,
    make_feedback_zip,
    source_integrity,
    schema_validation,
    boundary_audit,
    inspect_v105_enlarged_package,
    audit_adaptive_ledger,
    replay_terminal_routes,
    replay_directed,
    replay_tensor,
    replay_h004,
    audit_v086_directed_kernel,
    audit_v086_tensor_kernel,
    copy_and_triage_stress_failures,
)

VERSION = "v0.10.7-bs0832-final-theorem-release-candidate-and-independent-review-bundle"
SCHEMA_VERSION = "v107-final-theorem-release-candidate-independent-review-v1"
STEP_NAME = "85_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle"
ARTIFACT_PREFIX = "v107"
FEEDBACK_NAME = "feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip"

V106 = {
    "summary": "data/v106_readiness_summary.json",
    "status": "status/v106.status.json",
    "gates": "gates/v106_theorem_gate_matrix.csv",
    "proof_json": "proof/bs0832_theorem_package_v15_dry_freeze_decision_v106.json",
    "proof_csv": "proof/bs0832_theorem_package_v15_dry_freeze_decision_v106.csv",
    "kernel_decision": "kernel/v106_final_kernel_signoff_decision.csv",
    "g2": "kernel/v106_G2_directed_external_arb_kernel_signoff_attempt.csv",
    "g3": "kernel/v106_G3_local_tensor_theorem_kernel_signoff_attempt.csv",
    "domain": "domain/domain_final_decision_v106.csv",
    "boundary": "audit/v106_proof_boundary_audit.csv",
    "repro": "reproducibility/v106_reproducibility_checklist.csv",
    "manifest": "manifest/v106_manifest.json",
}


def ensure_dirs(run_dir: Path) -> Dict[str, Path]:
    dirs = ensure_dirs_v106(run_dir)
    for name in ["release", "appendix", "review", "hash_audit", "checklists"]:
        dirs[name] = run_dir / name
        dirs[name].mkdir(parents=True, exist_ok=True)
    return dirs


def _csv_rows_from_zip(zip_path: Path, member: str, limit: int = 0) -> Iterator[dict]:
    yield from iter_csv_from_zip(zip_path, member, limit)


def validate_v106_schema(v106_zip: Path) -> Tuple[List[dict], bool]:
    specs = [
        ("json", "v106_summary", V106["summary"], [
            "status", "branch_B_replay_closed_candidate", "domain_gate_closed_candidate_by_B",
            "G2_final_external_arb_kernel_signoff_candidate", "G3_final_local_tensor_theorem_signoff_candidate",
            "theorem_ready_candidate", "theorem_ready", "proof_boundary_violations",
        ]),
        ("json", "v106_status", V106["status"], [
            "status", "branch_B_replay_closed_candidate", "G2_final_external_arb_kernel_signoff_candidate",
            "G3_final_local_tensor_theorem_signoff_candidate", "theorem_ready_candidate", "theorem_ready",
        ]),
        ("csv", "v106_gates", V106["gates"], [
            "gate_id", "gate_family", "v106_candidate_status", "v106_theorem_status", "blocks_bs0832_theorem", "next_action",
        ]),
        ("json", "v106_proof_json", V106["proof_json"], [
            "branch_B_replay_closed_candidate", "G2_final_external_arb_kernel_signoff_candidate",
            "G3_final_local_tensor_theorem_signoff_candidate", "theorem_ready_candidate", "theorem_ready", "strict_boundary",
        ]),
        ("csv", "v106_kernel_decision", V106["kernel_decision"], [
            "kernel_id", "kernel_family", "rows_bound", "v086_rows", "v097_v105_bind_clean",
            "v086_kernel_input_clean", "final_kernel_signoff_candidate", "formalized_theorem_claim",
        ]),
        ("csv", "v106_domain", V106["domain"], [
            "branch_id", "branch_name", "v105_status", "v106_decision_status",
            "branch_closed_candidate", "blocks_bs0832", "evidence_or_gap", "next_action",
        ]),
        ("csv", "v106_repro", V106["repro"], ["check_id", "status", "detail"]),
    ]
    rows: List[dict] = []
    ok = True
    for kind, family, member, req in specs:
        exists = zip_has(v106_zip, member)
        present: List[str] = []
        missing = list(req)
        passed = False
        if exists:
            try:
                if kind == "json":
                    obj = read_json_from_zip(v106_zip, member)
                    present = [k for k in req if k in obj]
                    missing = [k for k in req if k not in obj]
                else:
                    header = csv_header_from_zip(v106_zip, member)
                    present = [k for k in req if k in header]
                    missing = [k for k in req if k not in header]
                passed = not missing
            except Exception:
                passed = False
        ok = ok and passed
        rows.append({
            "schema_family": family,
            "member": member,
            "exists": str(exists),
            "required_fields": ";".join(req),
            "present_required_fields": ";".join(present),
            "missing_required_fields": ";".join(missing),
            "status": "passed" if passed else "failed",
        })
    return rows, ok


def audit_v106_candidate(v106_zip: Path) -> Tuple[dict, List[dict]]:
    summary = read_json_from_zip(v106_zip, V106["summary"])
    status = read_json_from_zip(v106_zip, V106["status"])
    proof = read_json_from_zip(v106_zip, V106["proof_json"])
    rows: List[dict] = []
    checks = [
        ("V106-1", "summary_status_success", summary.get("status") == "success"),
        ("V106-2", "branch_B_replay_closed_candidate", boolish(summary.get("branch_B_replay_closed_candidate")) and boolish(status.get("branch_B_replay_closed_candidate")) and boolish(proof.get("branch_B_replay_closed_candidate"))),
        ("V106-3", "G2_candidate_closed", boolish(summary.get("G2_final_external_arb_kernel_signoff_candidate")) and boolish(proof.get("G2_final_external_arb_kernel_signoff_candidate"))),
        ("V106-4", "G3_candidate_closed", boolish(summary.get("G3_final_local_tensor_theorem_signoff_candidate")) and boolish(proof.get("G3_final_local_tensor_theorem_signoff_candidate"))),
        ("V106-5", "dry_freeze_candidate_ready", boolish(summary.get("theorem_ready_candidate")) and boolish(proof.get("theorem_ready_candidate"))),
        ("V106-6", "theorem_ready_false", not boolish(summary.get("theorem_ready")) and not boolish(status.get("theorem_ready")) and not boolish(proof.get("theorem_ready"))),
        ("V106-7", "proof_boundary_clean", int(summary.get("proof_boundary_violations", -1)) == 0),
        ("V106-8", "083201_not_proved", int(summary.get("stress_failures_083201", 0)) == 8),
    ]
    for cid, name, ok in checks:
        rows.append({"check_id": cid, "check_family": name, "status": "passed" if ok else "failed", "detail": json.dumps({"summary_value": summary.get(name, None)}, ensure_ascii=False)})
    stats = {
        "v106_status": summary.get("status"),
        "v106_branch_B_replay_closed_candidate": boolish(summary.get("branch_B_replay_closed_candidate")),
        "v106_G2_candidate": boolish(summary.get("G2_final_external_arb_kernel_signoff_candidate")),
        "v106_G3_candidate": boolish(summary.get("G3_final_local_tensor_theorem_signoff_candidate")),
        "v106_theorem_ready_candidate": boolish(summary.get("theorem_ready_candidate")),
        "v106_theorem_ready": boolish(summary.get("theorem_ready")),
        "v106_proof_boundary_violations": int(summary.get("proof_boundary_violations", -1)),
        "v106_stress_failures_083201": int(summary.get("stress_failures_083201", -1)),
        "v106_candidate_acceptance_status": all(r[2] for r in checks),
        "v106_summary": summary,
    }
    return stats, rows


def block_hash_csv_from_zip(
    zip_path: Path,
    member: str,
    source_label: str,
    block_size: int,
    limit: int = 0,
    progress_log: Optional[Path] = None,
    progress_interval: int = 100_000,
    family_fields: Optional[List[str]] = None,
    status_fields: Optional[List[str]] = None,
    key_fields: Optional[List[str]] = None,
) -> Tuple[List[dict], dict]:
    """Compact row-order-preserving block hash of a CSV member.

    v107 originally used csv.DictReader for this audit.  On repeated scans of
    large zip members on some Windows/Python combinations, DictReader can be
    noticeably slower and creates unnecessary per-row dicts.  The final audit
    only needs row count + stable row-order hash because route/status counts are
    already checked by the fresh replay functions.  Therefore this function uses
    normalized raw CSV data lines after the header.  It is faster, more memory
    stable, and still deterministic across CRLF/LF line endings.
    """
    if block_size <= 0:
        block_size = 50_000
    rows_out: List[dict] = []
    row_count = 0
    block_index = 0
    block_count = 0
    block_hash = hashlib.sha256()
    full_hash = hashlib.sha256()
    first_key = ""
    last_key = ""
    header_text = ""

    def flush_block() -> None:
        nonlocal block_index, block_count, block_hash, first_key, last_key
        if block_count == 0:
            return
        block_index += 1
        rows_out.append({
            "source_label": source_label,
            "member": member,
            "block_index": str(block_index),
            "row_start": str(row_count - block_count + 1),
            "row_end": str(row_count),
            "row_count": str(block_count),
            "first_key": first_key,
            "last_key": last_key,
            "header_sha256": hashlib.sha256(header_text.encode("utf-8")).hexdigest(),
            "block_sha256": block_hash.hexdigest(),
            "family_counts_json": "{}",
            "status_counts_json": "{}",
            "status": "passed_hash_block_observed",
        })
        block_count = 0
        block_hash = hashlib.sha256()
        first_key = ""
        last_key = ""

    with zipfile.ZipFile(zip_path) as z:
        with z.open(member, "r") as f:
            header_bytes = f.readline()
            header_text = header_bytes.decode("utf-8-sig").rstrip("\r\n")
            for raw in f:
                if limit and row_count >= limit:
                    break
                row_count += 1
                if progress_log and progress_interval > 0 and row_count % progress_interval == 0:
                    log_line(progress_log, f"hash audit {source_label}:{member} scanned {row_count} rows")
                # Normalize line endings only; do not parse or reformat CSV cells.
                line = raw.decode("utf-8").rstrip("\r\n") + "\n"
                payload = line.encode("utf-8")
                if block_count == 0:
                    first_key = str(row_count)
                last_key = str(row_count)
                block_hash.update(payload)
                full_hash.update(payload)
                block_count += 1
                if block_count >= block_size:
                    flush_block()
    flush_block()
    stats = {
        "source_label": source_label,
        "member": member,
        "row_count": row_count,
        "block_count": block_index,
        "block_size": block_size,
        "header_sha256": hashlib.sha256(header_text.encode("utf-8")).hexdigest(),
        "full_rows_sha256": full_hash.hexdigest(),
        "family_counts": {},
        "status_counts": {},
        "hash_mode": "normalized_raw_csv_data_lines",
    }
    return rows_out, stats

def combine_hash_audits(*parts: List[dict]) -> List[dict]:
    rows: List[dict] = []
    for part in parts:
        rows.extend(part)
    return rows


def checks_passed(rows: Iterable[dict]) -> bool:
    return all(str(r.get("status", "")).startswith("passed") for r in rows)


def build_final_review_rows(summary_checks: List[Tuple[str, bool, str]]) -> List[dict]:
    return [
        {"check_id": cid, "status": "passed" if ok else "failed", "detail": detail}
        for cid, ok, detail in summary_checks
    ]


def release_text(title: str, body: str) -> str:
    return f"# {title}\n\n{body.strip()}\n"


def run_v107(
    run_id: str,
    project_root: Path,
    v106_feedback_zip: Path,
    v105_feedback_zip: Path,
    v096_feedback_zip: Path,
    adaptive_full_ledger_zip: Path,
    v097_feedback_zip: Path,
    v086_feedback_zip: Path,
    v050_feedback_zip: Path,
    optional_sources: Dict[str, Optional[Path]],
    decimal_precision: int = 180,
    terminal_route_limit: int = 0,
    directed_row_limit: int = 0,
    tensor_member_limit: int = 0,
    h004_witness_limit: int = 0,
    accept_margin: str = "0.0000001",
    route_hash_block_size: int = 50_000,
    directed_hash_block_size: int = 10_000,
    tensor_hash_block_size: int = 2_000,
    h004_hash_block_size: int = 500,
    progress_interval: int = 100_000,
    emit_kernel_witness_samples: bool = False,
    allow_smoke_limits: bool = False,
    log_level: str = "INFO",
) -> dict:
    getcontext().prec = decimal_precision
    accept_margin_decimal = decimal_of(accept_margin, "0.0000001")
    run_dir = project_root / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    dirs = ensure_dirs(run_dir)
    log_path = dirs["log"] / f"{ARTIFACT_PREFIX}.log"
    log_line(log_path, f"Starting {VERSION} run_id={run_id}")
    log_line(log_path, f"decimal_precision={decimal_precision}; accept_margin={accept_margin_decimal}; allow_smoke_limits={allow_smoke_limits}")
    log_line(log_path, f"hash block sizes route={route_hash_block_size} directed={directed_hash_block_size} tensor={tensor_hash_block_size} h004={h004_hash_block_size}")

    required_sources = {
        "v106_feedback_zip": v106_feedback_zip,
        "v105_feedback_zip": v105_feedback_zip,
        "v096_feedback_zip": v096_feedback_zip,
        "adaptive_full_ledger_zip": adaptive_full_ledger_zip,
        "v097_feedback_zip": v097_feedback_zip,
        "v086_feedback_zip": v086_feedback_zip,
        "v050_feedback_zip": v050_feedback_zip,
    }
    src_rows, src_ok = source_integrity(required_sources, optional_sources)
    write_csv(dirs["data"] / f"{ARTIFACT_PREFIX}_source_integrity_manifest.csv", list(src_rows[0].keys()), src_rows)
    if not src_ok:
        raise FileNotFoundError("Missing one or more required source zips; see v107_source_integrity_manifest.csv")
    log_line(log_path, "source integrity scan complete")

    schema_rows_base, schema_ok_base = schema_validation(v105_feedback_zip, v096_feedback_zip, adaptive_full_ledger_zip, v097_feedback_zip, v086_feedback_zip, v050_feedback_zip)
    schema_rows_v106, schema_ok_v106 = validate_v106_schema(v106_feedback_zip)
    schema_rows = schema_rows_base + schema_rows_v106
    schema_ok = schema_ok_base and schema_ok_v106
    write_csv(dirs["data"] / f"{ARTIFACT_PREFIX}_schema_field_validation.csv", list(schema_rows[0].keys()), schema_rows)
    log_line(log_path, f"schema validation complete: base={schema_ok_base}; v106={schema_ok_v106}; combined={schema_ok}")

    v106_stats, v106_rows = audit_v106_candidate(v106_feedback_zip)
    write_csv(dirs["review"] / f"{ARTIFACT_PREFIX}_v106_dry_freeze_candidate_consistency_audit.csv", list(v106_rows[0].keys()), v106_rows)
    log_line(log_path, f"v106 consistency audit complete: {v106_stats['v106_candidate_acceptance_status']}")

    boundary_rows_v105, boundary_violations_v105 = boundary_audit(v105_feedback_zip)
    # Re-state v106 boundary from summary/proof json in a compact way.
    boundary_rows = list(boundary_rows_v105)
    v106_summary = v106_stats["v106_summary"]
    for flag, expected in STRICT_BOUNDARY_FLAGS.items():
        observed = v106_summary.get(flag, expected)
        # v106 stored strict boundary under strict_boundary; prefer that if available.
        if isinstance(v106_summary.get("strict_boundary"), dict) and flag in v106_summary["strict_boundary"]:
            observed = v106_summary["strict_boundary"][flag]
        status = "passed" if str(observed) == str(expected) else "failed"
        boundary_rows.append({
            "boundary_flag": f"v106::{flag}",
            "observed_value": str(observed),
            "expected_value": str(expected),
            "status": status,
            "v107_observation": "strict boundary carried through v106 dry-freeze candidate",
        })
    boundary_violations = sum(1 for r in boundary_rows if r.get("status") != "passed")
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_proof_boundary_audit.csv", list(boundary_rows[0].keys()), boundary_rows)
    log_line(log_path, f"proof boundary audit complete: violations={boundary_violations}")

    preflight_rows, preflight_stats = inspect_v105_enlarged_package(v105_feedback_zip)
    write_csv(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_branchB_v105_package_preflight.csv", list(preflight_rows[0].keys()), preflight_rows)
    preflight_clean = preflight_stats.get("available") and all(r.get("status") in {"passed", "not_run", "pending"} for r in preflight_rows)
    log_line(log_path, f"v105 Branch-B package preflight complete: clean={preflight_clean}")

    # Fresh independent replay from original source packages.  These scans are the
    # final-review input, not v106's summary.
    ledger_stats, ledger_rows = audit_adaptive_ledger(
        adaptive_full_ledger_zip,
        terminal_limit=terminal_route_limit,
        full_audit_output=None,
        progress_log=log_path,
        progress_interval=progress_interval,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_adaptive_ledger_summary_checks.csv", list(ledger_rows[0].keys()), ledger_rows)
    write_json(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_adaptive_full_ledger_manifest.json", ledger_stats["manifest"])
    ledger_clean = checks_passed(ledger_rows) and bool(ledger_stats.get("ledger_audit_passed_observed"))
    log_line(log_path, f"adaptive ledger fresh replay complete: terminal={ledger_stats['terminal_rows']} clean={ledger_clean}")

    route_stats, route_rows = replay_terminal_routes(
        v097_feedback_zip,
        limit=terminal_route_limit,
        out_csv=None,
        progress_log=log_path,
        progress_interval=progress_interval,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_terminal_route_replay_summary_checks.csv", list(route_rows[0].keys()), route_rows)
    routes_clean = checks_passed(route_rows) and int(route_stats.get("terminal_route_failures", 1)) == 0
    log_line(log_path, f"terminal route fresh replay complete: rows={route_stats['terminal_route_rows']} clean={routes_clean}")

    directed_stats, directed_rows = replay_directed(
        v097_feedback_zip,
        v105_feedback_zip,
        limit=directed_row_limit,
        out_csv=None,
        accept_margin=accept_margin_decimal,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["external"] / f"{ARTIFACT_PREFIX}_directed_interval_fresh_replay_summary_checks.csv", list(directed_rows[0].keys()), directed_rows)
    directed_clean = checks_passed(directed_rows) and int(directed_stats.get("directed_failures_vs_0832", 1)) == 0
    log_line(log_path, f"directed fresh replay complete: rows={directed_stats['directed_rows']} clean={directed_clean}")

    tensor_stats, tensor_rows = replay_tensor(
        v097_feedback_zip,
        v105_feedback_zip,
        limit=tensor_member_limit,
        out_csv=None,
        accept_margin=accept_margin_decimal,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["external"] / f"{ARTIFACT_PREFIX}_local_tensor_fresh_replay_summary_checks.csv", list(tensor_rows[0].keys()), tensor_rows)
    tensor_clean = checks_passed(tensor_rows) and int(tensor_stats.get("tensor_failures_vs_0832", 1)) == 0
    log_line(log_path, f"tensor fresh replay complete: rows={tensor_stats['tensor_rows']} clean={tensor_clean}")

    h004_stats, h004_rows = replay_h004(
        v097_feedback_zip,
        v105_feedback_zip,
        v050_feedback_zip,
        limit=h004_witness_limit,
        out_csv=None,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["bridge"] / f"{ARTIFACT_PREFIX}_h004_fresh_replay_summary_checks.csv", list(h004_rows[0].keys()), h004_rows)
    h004_clean = checks_passed(h004_rows) and int(h004_stats.get("h004_failures", 1)) == 0
    log_line(log_path, f"h004 fresh replay complete: rows={h004_stats['h004_rows']} clean={h004_clean}")

    # Full kernel scans.  v106 used summary fast path by default; v107 closes the
    # skipped checks by making full scans mandatory for non-smoke runs.
    g2_stats, g2_rows = audit_v086_directed_kernel(
        v086_feedback_zip,
        limit=directed_row_limit,
        out_csv=(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G2_directed_kernel_witness_sample.csv") if emit_kernel_witness_samples else None,
        accept_margin=accept_margin_decimal,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G2_external_arb_final_review.csv", list(g2_rows[0].keys()), g2_rows)
    g2_clean = checks_passed(g2_rows) and int(g2_stats.get("g2_v086_failures_vs_0832", 1)) == 0
    log_line(log_path, f"G2 full kernel review complete: rows={g2_stats['g2_v086_directed_rows']} clean={g2_clean}")

    g3_stats, g3_rows = audit_v086_tensor_kernel(
        v086_feedback_zip,
        limit=tensor_member_limit,
        member_out_csv=(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G3_tensor_member_witness_sample.csv") if emit_kernel_witness_samples else None,
        package_out_csv=(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G3_tensor_package_witness_sample.csv") if emit_kernel_witness_samples else None,
        accept_margin=accept_margin_decimal,
        allow_smoke_limits=allow_smoke_limits,
    )
    write_csv(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G3_local_tensor_final_review.csv", list(g3_rows[0].keys()), g3_rows)
    g3_clean = checks_passed(g3_rows) and int(g3_stats.get("g3_v086_member_failures_vs_0832", 1)) == 0 and int(g3_stats.get("g3_v086_package_failures_vs_0832", 1)) == 0
    log_line(log_path, f"G3 full tensor review complete: members={g3_stats['g3_v086_tensor_member_rows']} packages={g3_stats['g3_v086_tensor_package_rows']} clean={g3_clean}")

    # Block-hash audits for independent reviewer reproducibility.  These are full
    # scans by default but emit compact block summaries.
    log_line(log_path, 'hash audit start: adaptive terminal ledger')
    adaptive_terminal_hash_rows, adaptive_terminal_hash_stats = block_hash_csv_from_zip(
        adaptive_full_ledger_zip, LEDGER["terminal"], "adaptive_terminal_ledger", route_hash_block_size,
        limit=terminal_route_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["route_family"], status_fields=["accepted_route"], key_fields=["terminal_box_id", "root_box_id"],
    )
    log_line(log_path, 'hash audit done: adaptive terminal ledger')
    log_line(log_path, 'hash audit start: v097 terminal route replay')
    v097_route_hash_rows, v097_route_hash_stats = block_hash_csv_from_zip(
        v097_feedback_zip, V097["routes"], "v097_terminal_route_external_replay", route_hash_block_size,
        limit=terminal_route_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["route_family"], status_fields=["v097_terminal_route_status"], key_fields=["terminal_box_id", "root_box_id"],
    )
    log_line(log_path, 'hash audit done: v097 terminal route replay')
    route_hash_rows = combine_hash_audits(adaptive_terminal_hash_rows, v097_route_hash_rows)
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_full_route_hash_audit.csv", list(route_hash_rows[0].keys()), route_hash_rows)

    log_line(log_path, 'hash audit start: v086 directed kernel')
    directed_hash_rows, directed_hash_stats = block_hash_csv_from_zip(
        v086_feedback_zip, V086["directed_port"], "v086_directed_kernel", directed_hash_block_size,
        limit=directed_row_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["artifact_family", "root_box_id"], status_fields=["v086_status_vs_0832", "v086_status_vs_083201_stress"], key_fields=["source_identifier", "root_box_id"],
    )
    log_line(log_path, 'hash audit done: v086 directed kernel')
    log_line(log_path, 'hash audit start: v097 directed replay')
    v097_directed_hash_rows, v097_directed_hash_stats = block_hash_csv_from_zip(
        v097_feedback_zip, V097["directed"], "v097_directed_external_replay", directed_hash_block_size,
        limit=directed_row_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["artifact_family", "root_box_id"], status_fields=["v097_status_vs_0832", "v097_status_vs_083201_stress"], key_fields=["source_identifier", "root_box_id"],
    )
    log_line(log_path, 'hash audit done: v097 directed replay')
    directed_all_hash_rows = combine_hash_audits(directed_hash_rows, v097_directed_hash_rows)
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_directed_kernel_hash_audit.csv", list(directed_all_hash_rows[0].keys()), directed_all_hash_rows)

    log_line(log_path, 'hash audit start: v086 tensor members')
    tensor_member_hash_rows, tensor_member_hash_stats = block_hash_csv_from_zip(
        v086_feedback_zip, V086["tensor_members"], "v086_tensor_members", tensor_hash_block_size,
        limit=tensor_member_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["tensor_family", "package_id"], status_fields=["v086_status_vs_0832", "v086_status_vs_083201_stress"], key_fields=["package_id", "source_box_id"],
    )
    log_line(log_path, 'hash audit done: v086 tensor members')
    log_line(log_path, 'hash audit start: v086 tensor packages')
    tensor_package_hash_rows, tensor_package_hash_stats = block_hash_csv_from_zip(
        v086_feedback_zip, V086["tensor_packages"], "v086_tensor_packages", tensor_hash_block_size,
        limit=0 if not (allow_smoke_limits and tensor_member_limit) else max(1, min(tensor_member_limit, REFERENCE_COUNTS["tensor_packages"])),
        progress_log=log_path, progress_interval=progress_interval,
        family_fields=["tensor_family"], status_fields=["v086_package_status_vs_0832"], key_fields=["package_id"],
    )
    log_line(log_path, 'hash audit done: v086 tensor packages')
    log_line(log_path, 'hash audit start: v097 tensor replay')
    v097_tensor_hash_rows, v097_tensor_hash_stats = block_hash_csv_from_zip(
        v097_feedback_zip, V097["tensor"], "v097_tensor_external_replay", tensor_hash_block_size,
        limit=tensor_member_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["tensor_family", "package_id"], status_fields=["v097_status_vs_0832", "v097_status_vs_083201_stress"], key_fields=["package_id", "source_box_id"],
    )
    log_line(log_path, 'hash audit done: v097 tensor replay')
    tensor_all_hash_rows = combine_hash_audits(tensor_member_hash_rows, tensor_package_hash_rows, v097_tensor_hash_rows)
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_tensor_kernel_hash_audit.csv", list(tensor_all_hash_rows[0].keys()), tensor_all_hash_rows)

    log_line(log_path, 'hash audit start: v097 h004 replay')
    h004_hash_rows, h004_hash_stats = block_hash_csv_from_zip(
        v097_feedback_zip, V097["h004"], "v097_h004_appendix_replay", h004_hash_block_size,
        limit=h004_witness_limit, progress_log=log_path, progress_interval=progress_interval,
        family_fields=["root_box_id"], status_fields=["v097_status"], key_fields=["witness_id", "root_box_id"],
    )
    log_line(log_path, 'hash audit done: v097 h004 replay')
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_h004_hash_audit.csv", list(h004_hash_rows[0].keys()), h004_hash_rows)
    hash_stats = {
        "adaptive_terminal_ledger": adaptive_terminal_hash_stats,
        "v097_terminal_routes": v097_route_hash_stats,
        "v086_directed_kernel": directed_hash_stats,
        "v097_directed_external_replay": v097_directed_hash_stats,
        "v086_tensor_members": tensor_member_hash_stats,
        "v086_tensor_packages": tensor_package_hash_stats,
        "v097_tensor_external_replay": v097_tensor_hash_stats,
        "v097_h004_appendix_replay": h004_hash_stats,
    }
    write_json(dirs["audit"] / f"{ARTIFACT_PREFIX}_full_hash_audit_summary.json", hash_stats)
    log_line(log_path, "full block-hash audits complete")

    full_hash_audit_passed = True
    if not allow_smoke_limits:
        full_hash_audit_passed = (
            adaptive_terminal_hash_stats["row_count"] == REFERENCE_COUNTS["terminal_route_rows"]
            and v097_route_hash_stats["row_count"] == REFERENCE_COUNTS["terminal_route_rows"]
            and directed_hash_stats["row_count"] == REFERENCE_COUNTS["directed_rows"]
            and v097_directed_hash_stats["row_count"] == REFERENCE_COUNTS["directed_rows"]
            and tensor_member_hash_stats["row_count"] == REFERENCE_COUNTS["tensor_members"]
            and tensor_package_hash_stats["row_count"] == REFERENCE_COUNTS["tensor_packages"]
            and v097_tensor_hash_stats["row_count"] == REFERENCE_COUNTS["tensor_members"]
            and h004_hash_stats["row_count"] == REFERENCE_COUNTS["h004_witnesses"]
        )
    else:
        full_hash_audit_passed = all(stats["row_count"] > 0 for stats in hash_stats.values())

    # Final review acceptance candidates.
    g1_accept = src_ok and schema_ok and ledger_clean and routes_clean and full_hash_audit_passed
    g2_accept = src_ok and schema_ok and directed_clean and g2_clean and v106_stats["v106_G2_candidate"] and full_hash_audit_passed
    g3_accept = src_ok and schema_ok and tensor_clean and g3_clean and v106_stats["v106_G3_candidate"] and full_hash_audit_passed
    g4_accept = src_ok and schema_ok and h004_clean and bool(h004_stats.get("h004_v050_freeze_valid")) and full_hash_audit_passed
    g5_accept = src_ok and schema_ok and preflight_clean and ledger_clean and routes_clean and v106_stats["v106_branch_B_replay_closed_candidate"] and full_hash_audit_passed
    boundary_clean = boundary_violations == 0
    fresh_independent_replay_passed = ledger_clean and routes_clean and directed_clean and tensor_clean and h004_clean and g2_clean and g3_clean
    final_review_all_candidate = g1_accept and g2_accept and g3_accept and g4_accept and g5_accept and boundary_clean and v106_stats["v106_candidate_acceptance_status"] and fresh_independent_replay_passed and not allow_smoke_limits

    final_review_rows = build_final_review_rows([
        ("FR-G1", g1_accept, "adaptive ledger + terminal route coverage accepted at final-review candidate level"),
        ("FR-G2", g2_accept, "directed/external-Arb kernel accepted at final-review candidate level; formal theorem flag remains false"),
        ("FR-G3", g3_accept, "local tensor theorem accepted at final-review candidate level; formal theorem flag remains false"),
        ("FR-G4", g4_accept, "h004 bridge accepted at final-review candidate level"),
        ("FR-G5", g5_accept, "Branch B domain route accepted at final-review candidate level; Branch A remains unclosed"),
        ("FR-B", boundary_clean, "strict proof boundary preserved"),
        ("FR-HASH", full_hash_audit_passed, "full compact block-hash audit passed"),
        ("FR-FRESH", fresh_independent_replay_passed, "fresh independent replay passed from original source artifacts"),
        ("FR-NOSMOKE", not allow_smoke_limits, "release candidate requires full non-smoke execution"),
    ])
    write_csv(dirs["review"] / f"{ARTIFACT_PREFIX}_final_independent_review_acceptance.csv", list(final_review_rows[0].keys()), final_review_rows)

    branch_domain_rows = [
        {"domain_item": "Branch_A_symbolic_range_reduction", "v107_status": "not_closed", "accepted_for_release_candidate": "False", "detail": "Branch A remains unclosed and is not used as the theorem-domain route."},
        {"domain_item": "Branch_B_enlarged_domain_replay", "v107_status": "accepted_final_review_candidate" if g5_accept else "not_accepted", "accepted_for_release_candidate": str(bool(g5_accept)), "detail": "Branch B is the adopted candidate domain route, based on v096 full ledger + v097 terminal replay + v106 dry-freeze consistency."},
        {"domain_item": "terminal_route_coverage", "v107_status": "passed" if routes_clean else "failed", "accepted_for_release_candidate": str(bool(routes_clean)), "detail": f"terminal_route_rows={route_stats['terminal_route_rows']}; failures={route_stats['terminal_route_failures']}"},
        {"domain_item": "route_family_counts", "v107_status": "passed" if route_stats.get("route_counts_status") else "failed", "accepted_for_release_candidate": str(bool(route_stats.get("route_counts_status"))), "detail": json.dumps(route_stats.get("route_counts", {}), sort_keys=True)},
    ]
    write_csv(dirs["domain"] / f"{ARTIFACT_PREFIX}_BranchB_domain_final_acceptance.csv", list(branch_domain_rows[0].keys()), branch_domain_rows)

    # 0.83201 triage remains separate.
    stress_rows, triage_rows, stress_count, stress_min = copy_and_triage_stress_failures(v105_feedback_zip)
    write_csv(dirs["gap"] / f"{ARTIFACT_PREFIX}_083201_stress_failures.csv", list(stress_rows[0].keys()) if stress_rows else ["empty"], stress_rows)
    launch_rows: List[dict] = []
    for row in triage_rows:
        launch = dict(row)
        launch["v107_repair_branch"] = "v0.11.x_083201_directed_repair"
        launch["included_in_bs0832_theorem_claim"] = "False"
        launch_rows.append(launch)
    write_csv(dirs["triage"] / f"{ARTIFACT_PREFIX}_083201_v011_repair_launch_queue.csv", list(launch_rows[0].keys()) if launch_rows else ["empty"], launch_rows)

    gates = [
        {"gate_id": "G1", "gate_family": "adaptive_full_ledger_and_terminal_route_coverage", "v107_final_review_status": "accepted_candidate" if g1_accept else "blocked", "blocks_release_candidate": str(not g1_accept), "theorem_boundary_status": "candidate_component_not_standalone_theorem"},
        {"gate_id": "G2", "gate_family": "external_arb_directed_interval_kernel", "v107_final_review_status": "accepted_candidate" if g2_accept else "blocked", "blocks_release_candidate": str(not g2_accept), "theorem_boundary_status": "external_arb_kernel_formalized_false"},
        {"gate_id": "G3", "gate_family": "true_local_tensor_certificate", "v107_final_review_status": "accepted_candidate" if g3_accept else "blocked", "blocks_release_candidate": str(not g3_accept), "theorem_boundary_status": "local_tensor_formalized_false"},
        {"gate_id": "G4", "gate_family": "h004_bridge_containment_appendix", "v107_final_review_status": "accepted_candidate" if g4_accept else "blocked", "blocks_release_candidate": str(not g4_accept), "theorem_boundary_status": "candidate_component_not_standalone_theorem"},
        {"gate_id": "G5", "gate_family": "formal_domain_translation_range_reduction", "v107_final_review_status": "BranchB_accepted_candidate" if g5_accept else "blocked", "blocks_release_candidate": str(not g5_accept), "theorem_boundary_status": "BranchB_candidate_route; BranchA_symbolic_proof_unclosed"},
        {"gate_id": "G6", "gate_family": "final_theorem_release_candidate_bundle", "v107_final_review_status": "release_candidate_ready" if final_review_all_candidate else "not_ready", "blocks_release_candidate": str(not final_review_all_candidate), "theorem_boundary_status": "theorem_ready_false_by_construction"},
    ]
    write_csv(dirs["gates"] / f"{ARTIFACT_PREFIX}_theorem_gate_matrix.csv", list(gates[0].keys()), gates)

    # Release and Appendix outputs.
    source_hashes = {role: sha256_file(path) for role, path in required_sources.items()}
    release_manifest = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": now_utc(),
        "bs0832_release_candidate_ready": final_review_all_candidate,
        "theorem_release_candidate": final_review_all_candidate,
        "theorem_ready": False,
        "proof_boundary": STRICT_BOUNDARY_FLAGS,
        "source_hashes": source_hashes,
        "key_counts": {
            "adaptive_parent_child_edges": ledger_stats["parent_child_rows"],
            "adaptive_endpoint_rows": ledger_stats["endpoint_rows"],
            "adaptive_terminal_route_rows": ledger_stats["terminal_rows"],
            "terminal_route_replay_rows": route_stats["terminal_route_rows"],
            "directed_rows": directed_stats["directed_rows"],
            "tensor_rows": tensor_stats["tensor_rows"],
            "tensor_packages": tensor_stats["tensor_packages"],
            "h004_rows": h004_stats["h004_rows"],
        },
        "hash_audit_summary": hash_stats,
        "083201": {"target_proved": False, "stress_failures": stress_count, "min_margin": stress_min},
    }
    write_json(dirs["release"] / "BS0832_THEOREM_RELEASE_CANDIDATE_MANIFEST.json", release_manifest)
    write_text(dirs["release"] / "BS0832_PROOF_BOUNDARY.md", release_text("BS0832 proof boundary", """
This v0.10.7 package is a final theorem release-candidate review bundle.  It is
not a theorem proof by itself.  The following flags remain false by construction:

- bs0832_reproduced_theorem_level
- theorem_ready
- external_arb_kernel_formalized
- local_tensor_formalized
- formal_domain_proof_closed
- target_083201_proved

The package supports reviewer-level final acceptance of candidate components and
one-command replay, while preserving the distinction between candidate artifacts
and a completed theorem proof.
"""))
    write_text(dirs["release"] / "BS0832_REPRODUCIBILITY.md", release_text("BS0832 reproducibility", f"""
Run from the project root after placing the required feedback zips in the root.

```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\run_v107_local.ps1
```

Expected feedback output:

```text
runs\\v107\\{FEEDBACK_NAME}
```

This run performs fresh replay from v096/v097/v086/v050/v105/v106 artifacts and
emits compact block-hash audits instead of huge per-row tables by default.
"""))
    artifact_index_rows = [
        {"artifact_family": "status", "path": f"status/{ARTIFACT_PREFIX}.status.json", "purpose": "machine-readable run status"},
        {"artifact_family": "summary", "path": f"data/{ARTIFACT_PREFIX}_readiness_summary.json", "purpose": "release-candidate readiness summary"},
        {"artifact_family": "gates", "path": f"gates/{ARTIFACT_PREFIX}_theorem_gate_matrix.csv", "purpose": "G1-G6 final review gate matrix"},
        {"artifact_family": "hash_audit", "path": f"audit/{ARTIFACT_PREFIX}_full_route_hash_audit.csv", "purpose": "compact full terminal-route block hashes"},
        {"artifact_family": "hash_audit", "path": f"audit/{ARTIFACT_PREFIX}_directed_kernel_hash_audit.csv", "purpose": "compact directed kernel block hashes"},
        {"artifact_family": "hash_audit", "path": f"audit/{ARTIFACT_PREFIX}_tensor_kernel_hash_audit.csv", "purpose": "compact tensor kernel block hashes"},
        {"artifact_family": "proof", "path": "proof/bs0832_theorem_package_v16_final_freeze_decision_v107.json", "purpose": "final freeze release-candidate decision"},
        {"artifact_family": "release", "path": "release/BS0832_THEOREM_RELEASE_CANDIDATE_MANIFEST.json", "purpose": "reviewer-facing release candidate manifest"},
    ]
    write_csv(dirs["release"] / "BS0832_ARTIFACT_INDEX.csv", list(artifact_index_rows[0].keys()), artifact_index_rows)

    one_command_ps1 = f"""# v0.10.7 BS0832 final theorem release-candidate and independent review bundle
# Run from project root after placing required feedback zips.
python .\\scripts\\85_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.py `
  --run-id v107 `
  --v106-feedback-zip .\\feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip `
  --v105-feedback-zip .\\feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip `
  --v096-feedback-zip .\\feedback_v096_adaptive_full_ledger_rerun_executor.zip `
  --adaptive-full-ledger-zip .\\adaptive_full_ledger_export_v096.zip `
  --v097-feedback-zip .\\feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip `
  --v086-feedback-zip .\\feedback_v086_true_arb_and_local_tensor_port_v1.zip `
  --v050-feedback-zip .\\feedback_v050_h004_local_proof_freeze_main.zip `
  --decimal-precision 180 `
  --terminal-route-limit 0 `
  --directed-row-limit 0 `
  --tensor-member-limit 0 `
  --h004-witness-limit 0 `
  --accept-margin 0.0000001 `
  --route-hash-block-size 50000 `
  --directed-hash-block-size 10000 `
  --tensor-hash-block-size 2000 `
  --h004-hash-block-size 500 `
  --progress-interval 100000 `
  --log-level INFO
"""
    write_text(dirs["release"] / "one_command_replay_v107.ps1", one_command_ps1)
    write_text(dirs["release"] / "one_command_replay_v107.py", """from pathlib import Path\nimport subprocess, sys\ncmd = [sys.executable, str(Path('scripts') / '85_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.py'), '--run-id', 'v107', '--v106-feedback-zip', 'feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip', '--v105-feedback-zip', 'feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip', '--v096-feedback-zip', 'feedback_v096_adaptive_full_ledger_rerun_executor.zip', '--adaptive-full-ledger-zip', 'adaptive_full_ledger_export_v096.zip', '--v097-feedback-zip', 'feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip', '--v086-feedback-zip', 'feedback_v086_true_arb_and_local_tensor_port_v1.zip', '--v050-feedback-zip', 'feedback_v050_h004_local_proof_freeze_main.zip']\nraise SystemExit(subprocess.call(cmd))\n""")

    appendix_specs = [
        ("Appendix_A_adaptive_tree_final_checklist.md", "Appendix A: adaptive full ledger / terminal route closure", [
            f"parent-child edges observed: {ledger_stats['parent_child_rows']}",
            f"terminal routes observed: {ledger_stats['terminal_rows']}",
            f"route counts: {json.dumps(ledger_stats.get('route_counts', {}), sort_keys=True)}",
            f"final-review accepted candidate: {g1_accept}",
        ]),
        ("Appendix_B_directed_kernel_final_checklist.md", "Appendix B: directed interval / external-Arb kernel", [
            f"directed rows observed: {directed_stats['directed_rows']}",
            f"directed failures vs 0.832: {directed_stats['directed_failures_vs_0832']}",
            f"G2 v086 rows: {g2_stats['g2_v086_directed_rows']}",
            f"min margin v105 vs 0.832: {directed_stats['directed_min_margin_v105_vs_0832']}",
            f"final-review accepted candidate: {g2_accept}",
            "formal theorem flag remains false; this checklist is for final review acceptance candidate only.",
        ]),
        ("Appendix_C_tensor_theorem_final_checklist.md", "Appendix C: local tensor theorem", [
            f"tensor rows observed: {tensor_stats['tensor_rows']}",
            f"tensor packages observed: {tensor_stats['tensor_packages']}",
            f"tensor failures vs 0.832: {tensor_stats['tensor_failures_vs_0832']}",
            f"G3 package-member mismatches: {g3_stats['g3_v086_package_member_mismatches']}",
            f"final-review accepted candidate: {g3_accept}",
            "formal tensor theorem flag remains false; this checklist is for final review acceptance candidate only.",
        ]),
        ("Appendix_D_h004_final_checklist.md", "Appendix D: h004 bridge", [
            f"h004 rows observed: {h004_stats['h004_rows']}",
            f"h004 failures: {h004_stats['h004_failures']}",
            f"v050 freeze valid: {h004_stats['h004_v050_freeze_valid']}",
            f"final-review accepted candidate: {g4_accept}",
        ]),
        ("Appendix_E_domain_BranchB_final_checklist.md", "Appendix E: Branch B domain route", [
            "Branch A symbolic range reduction remains unclosed.",
            "Branch B enlarged-domain replay is the adopted candidate domain route.",
            f"terminal route replay rows: {route_stats['terminal_route_rows']}",
            f"terminal route replay failures: {route_stats['terminal_route_failures']}",
            f"final-review accepted candidate: {g5_accept}",
        ]),
    ]
    for filename, title, bullets in appendix_specs:
        body = "\n".join(f"- {b}" for b in bullets)
        write_text(dirs["appendix"] / filename, release_text(title, body))

    remaining_blockers = []
    for gate in gates:
        if gate["blocks_release_candidate"] == "True":
            remaining_blockers.append(gate["gate_id"] + ":" + gate["gate_family"])
    if allow_smoke_limits:
        remaining_blockers.append("SMOKE_LIMITS_ACTIVE")

    execution_status = "smoke_success" if allow_smoke_limits else "success"
    summary = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "execution_status": execution_status,
        "status": execution_status,
        "source_integrity_passed": src_ok,
        "schema_validation_passed": schema_ok,
        "v106_candidate_consistency_passed": v106_stats["v106_candidate_acceptance_status"],
        "fresh_independent_replay_passed": fresh_independent_replay_passed,
        "full_hash_audit_passed": full_hash_audit_passed,
        "G1_final_review_accepted_candidate": g1_accept,
        "G2_final_review_accepted_candidate": g2_accept,
        "G3_final_review_accepted_candidate": g3_accept,
        "G4_final_review_accepted_candidate": g4_accept,
        "G5_BranchB_domain_final_acceptance_candidate": g5_accept,
        "theorem_package_v16_final_freeze_candidate": final_review_all_candidate,
        "bs0832_release_candidate_ready": final_review_all_candidate,
        "theorem_release_candidate": final_review_all_candidate,
        "theorem_ready": False,
        "bs0832_reproduced_theorem_level": False,
        "target_083201_proved": False,
        "external_arb_kernel_formalized": False,
        "local_tensor_formalized": False,
        "formal_domain_proof_closed": False,
        "remaining_blockers": remaining_blockers,
        "adaptive_parent_child_edges": ledger_stats["parent_child_rows"],
        "adaptive_endpoint_rows": ledger_stats["endpoint_rows"],
        "adaptive_terminal_route_rows": ledger_stats["terminal_rows"],
        "adaptive_route_counts": ledger_stats["route_counts"],
        "terminal_route_replay_rows": route_stats["terminal_route_rows"],
        "terminal_route_replay_failures": route_stats["terminal_route_failures"],
        "directed_rows": directed_stats["directed_rows"],
        "directed_failures_vs_0832": directed_stats["directed_failures_vs_0832"],
        "directed_min_margin_v105_vs_0832": directed_stats["directed_min_margin_v105_vs_0832"],
        "G2_v086_directed_rows": g2_stats["g2_v086_directed_rows"],
        "G2_v086_duplicate_source_identifiers": g2_stats["g2_v086_duplicate_source_identifiers"],
        "tensor_rows": tensor_stats["tensor_rows"],
        "tensor_packages": tensor_stats["tensor_packages"],
        "tensor_failures_vs_0832": tensor_stats["tensor_failures_vs_0832"],
        "G3_v086_tensor_member_rows": g3_stats["g3_v086_tensor_member_rows"],
        "G3_v086_tensor_package_rows": g3_stats["g3_v086_tensor_package_rows"],
        "G3_v086_package_member_mismatches": g3_stats["g3_v086_package_member_mismatches"],
        "h004_rows": h004_stats["h004_rows"],
        "h004_failures": h004_stats["h004_failures"],
        "stress_failures_083201": stress_count,
        "stress_min_margin_083201": stress_min,
        "proof_boundary_violations": boundary_violations,
        "allow_smoke_limits": allow_smoke_limits,
        "hash_audit_summary": hash_stats,
    }
    write_json(dirs["data"] / f"{ARTIFACT_PREFIX}_readiness_summary.json", summary)

    freeze_decision = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "fresh_independent_replay_passed": fresh_independent_replay_passed,
        "full_hash_audit_passed": full_hash_audit_passed,
        "G1_final_review_accepted_candidate": g1_accept,
        "G2_final_review_accepted_candidate": g2_accept,
        "G3_final_review_accepted_candidate": g3_accept,
        "G4_final_review_accepted_candidate": g4_accept,
        "G5_BranchB_domain_final_acceptance_candidate": g5_accept,
        "theorem_package_v16_final_freeze_candidate": final_review_all_candidate,
        "bs0832_release_candidate_ready": final_review_all_candidate,
        "theorem_release_candidate": final_review_all_candidate,
        "theorem_ready": False,
        "strict_boundary": STRICT_BOUNDARY_FLAGS,
        "remaining_blockers": remaining_blockers,
        "gate_matrix": gates,
        "release_manifest": "release/BS0832_THEOREM_RELEASE_CANDIDATE_MANIFEST.json",
    }
    write_json(dirs["proof"] / "bs0832_theorem_package_v16_final_freeze_decision_v107.json", freeze_decision)
    freeze_rows = [{
        "decision_key": k,
        "decision_value": json.dumps(v, sort_keys=True, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v),
    } for k, v in freeze_decision.items() if k != "gate_matrix"]
    write_csv(dirs["proof"] / "bs0832_theorem_package_v16_final_freeze_decision_v107.csv", list(freeze_rows[0].keys()), freeze_rows)

    repro_rows = [
        {"check_id": "R1", "status": "passed" if src_ok else "failed", "detail": "source integrity"},
        {"check_id": "R2", "status": "passed" if schema_ok else "failed", "detail": "schema validation including v106"},
        {"check_id": "R3", "status": "passed" if v106_stats["v106_candidate_acceptance_status"] else "failed", "detail": "v106 dry-freeze candidate consistency"},
        {"check_id": "R4", "status": "passed" if fresh_independent_replay_passed else "failed", "detail": "fresh independent replay"},
        {"check_id": "R5", "status": "passed" if full_hash_audit_passed else "failed", "detail": "full compact block-hash audit"},
        {"check_id": "R6", "status": "passed" if final_review_all_candidate else "pending", "detail": "BS0832 theorem release-candidate readiness"},
        {"check_id": "R7", "status": "passed" if boundary_clean else "failed", "detail": "proof boundary preserved"},
        {"check_id": "R8", "status": "passed" if stress_count == 8 else "failed", "detail": "0.83201 failures preserved and isolated"},
    ]
    write_csv(dirs["reproducibility"] / f"{ARTIFACT_PREFIX}_reproducibility_checklist.csv", list(repro_rows[0].keys()), repro_rows)

    status = {
        "status": summary["status"],
        "run_id": run_id,
        "version": VERSION,
        "fresh_independent_replay_passed": fresh_independent_replay_passed,
        "full_hash_audit_passed": full_hash_audit_passed,
        "bs0832_release_candidate_ready": final_review_all_candidate,
        "theorem_release_candidate": final_review_all_candidate,
        "theorem_ready": False,
        "target_083201_proved": False,
        "generated_at": now_utc(),
    }
    write_json(dirs["status"] / f"{ARTIFACT_PREFIX}.status.json", status)

    report = f"""# v0.10.7 BS0832 final theorem release-candidate and independent review bundle

Status: `{summary['status']}`

## Key results

- fresh independent replay passed: `{summary['fresh_independent_replay_passed']}`
- full hash audit passed: `{summary['full_hash_audit_passed']}`
- G1 final review accepted candidate: `{summary['G1_final_review_accepted_candidate']}`
- G2 final review accepted candidate: `{summary['G2_final_review_accepted_candidate']}`
- G3 final review accepted candidate: `{summary['G3_final_review_accepted_candidate']}`
- G4 final review accepted candidate: `{summary['G4_final_review_accepted_candidate']}`
- G5 Branch-B domain final acceptance candidate: `{summary['G5_BranchB_domain_final_acceptance_candidate']}`
- theorem package v16 final freeze candidate: `{summary['theorem_package_v16_final_freeze_candidate']}`
- BS0832 release candidate ready: `{summary['bs0832_release_candidate_ready']}`
- theorem ready: `false`
- 0.83201 proved: `false`
- proof boundary violations: `{summary['proof_boundary_violations']}`

## Counts

- adaptive terminal routes: `{summary['adaptive_terminal_route_rows']}`
- terminal replay failures: `{summary['terminal_route_replay_failures']}`
- directed rows/failures: `{summary['directed_rows']}` / `{summary['directed_failures_vs_0832']}`
- tensor rows/packages/failures: `{summary['tensor_rows']}` / `{summary['tensor_packages']}` / `{summary['tensor_failures_vs_0832']}`
- h004 rows/failures: `{summary['h004_rows']}` / `{summary['h004_failures']}`
- 0.83201 stress failures preserved: `{summary['stress_failures_083201']}`

## Boundary

v0.10.7 produces a release-candidate review bundle.  It does not make the final
theorem claim.  `theorem_ready`, `bs0832_reproduced_theorem_level`, and
`target_083201_proved` remain false.
"""
    write_text(dirs["report"] / f"{ARTIFACT_PREFIX}.md", report)

    manifest = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "feedback_name": FEEDBACK_NAME,
        "outputs": sorted([p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_file()]),
    }
    write_json(dirs["manifest"] / f"{ARTIFACT_PREFIX}_manifest.json", manifest)
    log_line(log_path, f"Finished v107; release_candidate={final_review_all_candidate}; theorem_ready=False")

    feedback_zip = run_dir / FEEDBACK_NAME
    make_feedback_zip(run_dir, feedback_zip)
    return {"summary": summary, "run_dir": str(run_dir), "feedback_zip": str(feedback_zip)}
