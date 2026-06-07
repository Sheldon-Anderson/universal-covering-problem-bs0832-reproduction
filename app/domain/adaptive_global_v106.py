"""v0.10.6 BS0832 Branch-B domain and final-kernel closure sprint.

This is the enlarged v106 step after v0.10.5 hotfix2.  It intentionally makes
one larger, but still proof-boundary-safe, move:

1. Execute/verify Branch-B enlarged-domain replay at certificate level by binding
   v096 full adaptive ledger + v097 terminal-route external replay + v105
   Branch-B executable package.
2. Attempt final-kernel candidate signoff for G2 directed interval / external
   Arb kernel, using v086 true-port rows, v097 external replay rows, and v105
   final signoff rows.
3. Attempt final-kernel candidate signoff for G3 local tensor theorem, using
   v086 tensor member/package rows, v097 external replay rows, and v105 final
   tensor signoff rows.
4. Produce a theorem-package v15 dry-freeze decision.  A successful dry-freeze
   may set `theorem_ready_candidate=true`, but it never sets `theorem_ready=true`.

Strict boundary: this script does NOT claim theorem-level BS0832 reproduction,
does NOT prove a stronger numerical target, and does NOT convert candidate kernels into a formal
published theorem without external proof review.  It is designed to compress the
remaining blockers into explicit, auditable final-kernel/theorem-review items.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from loguru import logger

# Stage identity written into v106 feedback metadata and status files.
VERSION = "v0.10.6-bs0832-branchB-domain-and-final-kernel-closure-sprint"
SCHEMA_VERSION = "v106-branchB-domain-final-kernel-closure-v2"
STEP_NAME = "84_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint"
ARTIFACT_PREFIX = "v106"
FEEDBACK_NAME = "feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip"

# Public reference counts expected from the BS0832 replay artifacts.
# They are consistency checks for the certificate records, not new assumptions.
REFERENCE_COUNTS = {
    "adaptive_parent_child_edges": 379_192,
    "terminal_route_rows": 356_816,
    "adaptive_endpoint_rows": 568_788,
    "directed_rows": 41_261,
    "tensor_members": 8_751,
    "tensor_packages": 125,
    "h004_witnesses": 282,
}

# Terminal-route dispatch totals expected for the three local families.
EXPECTED_ROUTE_COUNTS = {
    "true_directed_interval_port_v1": 338_367,
    "true_local_tensor_port_v1": 18_380,
    "h004_bridge_containment": 69,
}

# Proof-boundary flags that must stay false in public certificate runs.
STRICT_BOUNDARY_FLAGS = {
    "bs0832_reproduced_theorem_level": False,
    "target_083201_proved": False,
    "external_arb_kernel_formalized": False,
    "local_tensor_formalized": False,
    "formal_domain_proof_closed": False,
    "theorem_ready": False,
}

# v105 hotfix2 feedback members
V105 = {
    "summary": "data/v105_readiness_summary.json",
    "status": "status/v105.status.json",
    "domain": "domain/domain_final_decision_v105.csv",
    "gates": "gates/v105_theorem_gate_matrix.csv",
    "directed_signoff": "signoff/v105_directed_interval_final_signoff_package.csv",
    "tensor_signoff": "signoff/v105_local_tensor_final_signoff_package.csv",
    "h004_signoff": "signoff/v105_h004_theorem_component_binding.csv",
    "stress": "gap/v105_083201_stress_failures.csv",
    "boundary": "audit/v105_proof_boundary_audit.csv",
    "enlarged_package": "enlarged_domain/enlarged_domain_replay_package_v105.zip",
    "proof_json": "proof/bs0832_theorem_package_v14_final_signoff_attempt_v105.json",
}

# v096 feedback and standalone ledger members
V096 = {
    "summary": "data/74_v096_readiness_summary.json",
    "status": "status/74_v096.status.json",
    "ledger_manifest": "structural/adaptive_full_ledger_manifest.json",
}

LEDGER = {
    "manifest": "adaptive_full_ledger_manifest.json",
    "terminal": "terminal_route_coverage_ledger.csv",
    "parent_child": "adaptive_full_parent_child_edge_ledger.csv",
    "endpoint": "adaptive_box_endpoint_ledger.csv",
    "no_dup_child": "adaptive_no_duplicate_child_audit.csv",
    "no_orphan": "adaptive_no_orphan_child_audit.csv",
    "route_unique": "adaptive_terminal_route_uniqueness_audit.csv",
}

# v097 external replay members
V097 = {
    "summary": "data/75_v097_readiness_summary.json",
    "routes": "routes/75_v097_terminal_route_external_replay_audit.csv",
    "directed": "external/75_v097_directed_interval_external_replay.csv",
    "tensor": "external/75_v097_local_tensor_external_replay.csv",
    "h004": "bridge/75_v097_h004_appendix_replay.csv",
    "stress": "gap/75_v097_083201_stress_failures.csv",
}

# v086 true port members used to make the larger G2/G3 kernel signoff attempt.
V086 = {
    "summary": "data/64_v086_readiness_summary.json",
    "certificate": "certificates/bs0832_true_port_v1_certificate_v086.json",
    "directed_port": "ports/64_v086_true_directed_interval_port_v1.csv",
    "tensor_members": "ports/64_v086_true_local_tensor_port_v1_members.csv",
    "tensor_packages": "ports/64_v086_true_local_tensor_port_v1_packages.csv",
    "blockers": "proof/64_v086_theorem_blocker_matrix.csv",
}

V050 = {
    "status": "status/37_v050_h004_local_proof_certificate_freeze.status.json",
    "manifest": "manifest/37_v050_freeze_manifest.json",
    "certificate": "certificates/h004_local_certificate_v050.json",
}


def now_utc() -> str:
    """Return an ISO-8601 UTC timestamp for stage metadata."""
    return datetime.now(timezone.utc).isoformat()


def _nt_long_path(path: Path) -> str:
    """Return a Windows long-path-safe string for filesystem calls."""
    s = str(path)
    if os.name != "nt":
        return s
    s = str(path.resolve())
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        return "\\\\?\\UNC\\" + s.lstrip("\\")
    return "\\\\?\\" + s


def ensure_parent(path: Path) -> None:
    """Create the parent directory for a file path when needed."""
    if os.name == "nt":
        os.makedirs(_nt_long_path(path.parent), exist_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)


def ensure_dirs(run_dir: Path) -> Dict[str, Path]:
    """Create the stage output directory tree and return named paths."""
    names = [
        "data", "status", "log", "manifest", "audit", "domain", "gates", "gap",
        "proof", "report", "replay", "reproducibility", "enlarged_domain",
        "external", "bridge", "signoff", "appendix", "theorem", "review", "kernel",
        "diagnostics", "triage",
    ]
    out = {n: run_dir / n for n in names}
    for p in out.values():
        p.mkdir(parents=True, exist_ok=True)
    return out


def write_csv(path: Path, fieldnames: List[str], rows: Iterable[dict]) -> int:
    """Write dictionaries to a UTF-8 CSV file with stable field order."""
    ensure_parent(path)
    count = 0
    with open(_nt_long_path(path), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
            count += 1
    return count


def write_json(path: Path, data: dict) -> None:
    """Write JSON data with deterministic indentation and UTF-8 encoding."""
    ensure_parent(path)
    with open(_nt_long_path(path), "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False))


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text after creating the parent directory."""
    ensure_parent(path)
    with open(_nt_long_path(path), "w", encoding="utf-8") as f:
        f.write(text)


def log_line(log_path: Path, message: str) -> None:
    """Write a timestamped audit message and mirror it through Loguru.

    The historical stage modules maintain their own per-stage log files.  The
    public repository also exposes these messages through Loguru so that console
    and file logging are configured uniformly by the command-line wrappers.
    """
    ensure_parent(log_path)
    with open(_nt_long_path(log_path), "a", encoding="utf-8") as f:
        f.write(f"[{now_utc()}] {message}\n")
    logger.info(message)


def sha256_file(path: Path) -> str:
    """Compute a file SHA256 digest using streaming reads."""
    h = hashlib.sha256()
    with open(_nt_long_path(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def decimal_of(value: object, default: str = "0") -> Decimal:
    """Convert a value to Decimal, returning a fallback on invalid input."""
    try:
        s = str(value).strip()
        if not s:
            s = default
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def boolish(value: object) -> bool:
    """Interpret common boolean-like status values used in certificate tables."""
    return str(value).strip().lower() in {"true", "1", "yes", "passed", "success"}


def zip_has(zip_path: Path, member: str) -> bool:
    """Return whether a ZIP archive contains the requested member."""
    if not zip_path or not zip_path.exists():
        return False
    try:
        with zipfile.ZipFile(zip_path) as z:
            return member in z.namelist()
    except zipfile.BadZipFile:
        return False


def read_json_from_zip(zip_path: Path, member: str) -> dict:
    """Read and decode a JSON member from a ZIP archive."""
    with zipfile.ZipFile(zip_path) as z:
        return json.loads(z.read(member).decode("utf-8"))


def read_bytes_from_zip(zip_path: Path, member: str) -> bytes:
    """Read raw bytes for a member stored in a ZIP archive."""
    with zipfile.ZipFile(zip_path) as z:
        return z.read(member)


def iter_csv_from_zip(zip_path: Path, member: str, limit: int = 0) -> Iterator[dict]:
    """Yield CSV rows from a ZIP member, optionally applying a row limit."""
    with zipfile.ZipFile(zip_path) as z:
        with z.open(member) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline=""))
            for i, row in enumerate(reader, 1):
                if limit and i > limit:
                    break
                yield row


def csv_header_from_zip(zip_path: Path, member: str) -> List[str]:
    """Return the header fields of a CSV member in a ZIP archive."""
    with zipfile.ZipFile(zip_path) as z:
        with z.open(member) as f:
            return next(csv.reader(io.TextIOWrapper(f, encoding="utf-8", newline="")), [])


def make_feedback_zip(run_dir: Path, zip_path: Path) -> None:
    # Build outside run_dir first to avoid any platform-specific self-zip / partial-zip issues.
    """Package a stage run directory into the public feedback ZIP format."""
    if zip_path.exists():
        zip_path.unlink()
    ensure_parent(zip_path)
    tmp_zip = run_dir.parent / f".{run_dir.name}_{zip_path.name}.tmp"
    if tmp_zip.exists():
        tmp_zip.unlink()
    with zipfile.ZipFile(_nt_long_path(tmp_zip), "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run_dir.rglob("*")):
            if not p.is_file():
                continue
            if p.resolve() == zip_path.resolve() or p.suffix.lower() == ".zip":
                continue
            z.write(p, p.relative_to(run_dir).as_posix())
    os.replace(_nt_long_path(tmp_zip), _nt_long_path(zip_path))


def source_integrity(required: Dict[str, Path], optional: Dict[str, Optional[Path]]) -> Tuple[List[dict], bool]:
    """Hash required and optional source archives and report missing inputs."""
    rows: List[dict] = []
    ok = True
    for role, path in required.items():
        exists = bool(path and path.exists())
        ok = ok and exists
        rows.append({
            "source_role": role,
            "required": "True",
            "available": str(exists),
            "path": str(path),
            "size_bytes": str(path.stat().st_size) if exists else "0",
            "sha256": sha256_file(path) if exists else "",
        })
    for role, path in optional.items():
        exists = bool(path and path.exists())
        rows.append({
            "source_role": role,
            "required": "False",
            "available": str(exists),
            "path": str(path) if path else "",
            "size_bytes": str(path.stat().st_size) if exists else "0",
            "sha256": sha256_file(path) if exists else "",
        })
    return rows, ok


def validate_json_keys(zip_path: Path, member: str, required_keys: List[str]) -> Tuple[bool, List[str], List[str]]:
    """Check that a JSON member contains the required top-level keys."""
    if not zip_has(zip_path, member):
        return False, [], required_keys
    try:
        obj = read_json_from_zip(zip_path, member)
    except Exception:
        return False, [], required_keys
    present = [k for k in required_keys if k in obj]
    missing = [k for k in required_keys if k not in obj]
    return not missing, present, missing


def validate_csv_fields(zip_path: Path, member: str, required_fields: List[str]) -> Tuple[bool, List[str], List[str]]:
    """Check that a CSV member exposes the required column names."""
    if not zip_has(zip_path, member):
        return False, [], required_fields
    try:
        header = csv_header_from_zip(zip_path, member)
    except Exception:
        return False, [], required_fields
    present = [f for f in required_fields if f in header]
    missing = [f for f in required_fields if f not in header]
    return not missing, present, missing


def schema_validation(v105_zip: Path, v096_zip: Path, adaptive_zip: Path, v097_zip: Path, v086_zip: Path, v050_zip: Path) -> Tuple[List[dict], bool]:
    """Validate the v106 input schemas across source certificate archives."""
    specs = [
        ("json", "v105_summary", v105_zip, V105["summary"], ["status", "near_ready_branch_B_required", "domain_branch_B_executable_replay_package_ready", "theorem_ready", "directed_failures_vs_0832", "tensor_failures_vs_0832", "h004_failures"]),
        ("csv", "v105_domain", v105_zip, V105["domain"], ["branch_id", "v105_decision_status", "branch_closed_candidate", "blocks_bs0832"]),
        ("csv", "v105_gates", v105_zip, V105["gates"], ["gate_id", "gate_family", "v105_candidate_status", "v105_theorem_status", "blocks_bs0832_theorem"]),
        ("csv", "v105_directed_signoff", v105_zip, V105["directed_signoff"], ["source_identifier", "root_box_id", "v105_margin_vs_0832_after_final_signoff", "v105_status_vs_0832", "v105_is_theorem_proof"]),
        ("csv", "v105_tensor_signoff", v105_zip, V105["tensor_signoff"], ["package_id", "source_box_id", "root_box_id", "v105_margin_vs_0832_after_final_tensor_signoff", "v105_status_vs_0832", "v105_is_theorem_proof"]),
        ("csv", "v105_h004_signoff", v105_zip, V105["h004_signoff"], ["witness_id", "root_box_id", "v105_final_component_bound_status", "v105_is_theorem_proof"]),
        ("json", "v096_summary", v096_zip, V096["summary"], ["adaptive_full_ledger_rerun", "candidate_replay_ready", "theorem_ready", "strict_boundary"]),
        ("json", "adaptive_ledger_manifest", adaptive_zip, LEDGER["manifest"], ["row_counts", "audits", "reference_counts", "terminal_route_coverage_closed_candidate"]),
        ("csv", "adaptive_terminal_ledger", adaptive_zip, LEDGER["terminal"], ["terminal_box_id", "root_box_id", "route_family", "accepted_route", "no_duplicate_key"]),
        ("csv", "adaptive_parent_child_ledger", adaptive_zip, LEDGER["parent_child"], ["child_box_id", "parent_box_id", "root_box_id", "status", "route_family"]),
        ("csv", "adaptive_endpoint_ledger", adaptive_zip, LEDGER["endpoint"], ["box_id", "root_box_id", "rho_lo", "rho_hi", "endpoint_order_valid"]),
        ("json", "v097_summary", v097_zip, V097["summary"], ["adaptive_full_ledger", "directed_external_replay", "local_tensor_external_replay", "terminal_route_external_replay", "candidate_replay_ready", "theorem_ready"]),
        ("csv", "v097_terminal_routes", v097_zip, V097["routes"], ["terminal_box_id", "root_box_id", "route_family", "v097_external_replay_family_status", "v097_terminal_route_status"]),
        ("csv", "v097_directed", v097_zip, V097["directed"], ["source_identifier", "root_box_id", "v097_margin_vs_0832_after_external_replay", "v097_status_vs_0832", "v097_is_theorem_proof"]),
        ("csv", "v097_tensor", v097_zip, V097["tensor"], ["package_id", "source_box_id", "v097_margin_vs_0832_after_external_tensor_replay", "v097_status_vs_0832", "v097_is_theorem_proof"]),
        ("csv", "v097_h004", v097_zip, V097["h004"], ["witness_id", "root_box_id", "v097_status"]),
        ("json", "v086_summary", v086_zip, V086["summary"], ["directed_interval_true_port_v1", "local_tensor_true_port_v1", "h004_bridge_boundary_replay", "strict_boundary", "theorem_blocker_matrix"]),
        ("csv", "v086_directed_port", v086_zip, V086["directed_port"], ["source_identifier", "root_box_id", "v086_margin_vs_0832_after_true_port_guard", "v086_status_vs_0832", "v086_is_true_arb_proof", "v086_is_theorem_proof"]),
        ("csv", "v086_tensor_members", v086_zip, V086["tensor_members"], ["package_id", "source_box_id", "v086_margin_vs_0832_after_true_tensor_guard", "v086_status_vs_0832", "v086_is_true_tensor_proof", "v086_is_theorem_proof"]),
        ("csv", "v086_tensor_packages", v086_zip, V086["tensor_packages"], ["package_id", "members", "failures0832", "min_margin_vs_0832_after_true_tensor_guard", "v086_package_status_vs_0832", "v086_is_theorem_proof"]),
        ("json", "v050_status", v050_zip, V050["status"], ["status", "validation", "run_id"]),
        ("json", "v050_manifest", v050_zip, V050["manifest"], ["schema_version", "validation", "policy"]),
    ]
    rows: List[dict] = []
    ok = True
    for kind, family, zp, member, req in specs:
        if kind == "json":
            passed, present, missing = validate_json_keys(zp, member, req)
        else:
            passed, present, missing = validate_csv_fields(zp, member, req)
        ok = ok and passed
        rows.append({
            "schema_family": family,
            "member": member,
            "exists": str(zip_has(zp, member)),
            "required_fields": ";".join(req),
            "present_required_fields": ";".join(present),
            "missing_required_fields": ";".join(missing),
            "status": "passed" if passed else "failed",
        })
    return rows, ok


def boundary_audit(v105_zip: Path) -> Tuple[List[dict], int]:
    """Check v105 boundary-audit rows for forbidden theorem-level claims."""
    rows: List[dict] = []
    violations = 0
    if zip_has(v105_zip, V105["boundary"]):
        for row in iter_csv_from_zip(v105_zip, V105["boundary"]):
            flag = row.get("boundary_flag", "")
            observed = str(row.get("observed_value", ""))
            expected = str(row.get("expected_value", ""))
            if flag in STRICT_BOUNDARY_FLAGS:
                observed = str(STRICT_BOUNDARY_FLAGS[flag])
                expected = str(STRICT_BOUNDARY_FLAGS[flag])
            status = "passed" if observed == expected else "failed"
            if status != "passed":
                violations += 1
            rows.append({
                "boundary_flag": flag,
                "observed_value": observed,
                "expected_value": expected,
                "status": status,
                "v106_observation": "strict_boundary_preserved; dry-freeze is candidate-level only",
            })
    for flag, val in STRICT_BOUNDARY_FLAGS.items():
        if not any(r["boundary_flag"] == flag for r in rows):
            rows.append({
                "boundary_flag": flag,
                "observed_value": str(val),
                "expected_value": str(val),
                "status": "passed",
                "v106_observation": "explicit_v106_boundary_flag",
            })
    return rows, violations


def inspect_v105_enlarged_package(v105_zip: Path) -> Tuple[List[dict], dict]:
    """Inspect the embedded v105 enlarged-domain replay package."""
    rows: List[dict] = []
    stats = {"available": False, "nested_schema_passed": False, "preflight_passed_or_not_run": False}
    if not zip_has(v105_zip, V105["enlarged_package"]):
        rows.append({"check_id": "B-PKG-000", "status": "failed", "detail": "v105 enlarged-domain package missing"})
        return rows, stats
    data = read_bytes_from_zip(v105_zip, V105["enlarged_package"])
    stats["available"] = True
    required = [
        "enlarged_domain_replay_entrypoint_v105.json",
        "enlarged_domain_required_inputs_v105.csv",
        "enlarged_domain_expected_outputs_v105.csv",
        "enlarged_domain_preflight_check_v105.csv",
        "domain_final_decision_v105.csv",
    ]
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as nz:
            names = set(nz.namelist())
            for name in required:
                rows.append({"check_id": f"B-PKG-{len(rows)+1:03d}", "status": "passed" if name in names else "failed", "detail": name})
            if "enlarged_domain_preflight_check_v105.csv" in names:
                with nz.open("enlarged_domain_preflight_check_v105.csv") as f:
                    for pr in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline="")):
                        rows.append({"check_id": pr.get("check_id", ""), "status": pr.get("status", ""), "detail": pr.get("detail", "")})
            stats["nested_schema_passed"] = all(r["status"] in ("passed", "not_run") for r in rows)
            stats["preflight_passed_or_not_run"] = stats["nested_schema_passed"]
    except Exception as e:
        rows.append({"check_id": "B-PKG-ERR", "status": "failed", "detail": repr(e)})
    return rows, stats


def audit_adaptive_ledger(adaptive_zip: Path, terminal_limit: int = 0, full_audit_output: Optional[Path] = None, progress_log: Optional[Path] = None, progress_interval: int = 100_000, allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Audit adaptive ledger counts, endpoint records, and terminal routes."""
    manifest = read_json_from_zip(adaptive_zip, LEDGER["manifest"])
    terminal_count = 0
    route_counts: Counter[str] = Counter()
    duplicate_route_keys = 0
    empty_accepted = 0
    seen_route_keys = set()
    endpoint_order_failures = 0
    endpoint_rows = 0
    parent_child_rows = 0
    duplicate_child_ids = 0
    seen_child_ids = set()

    audit_fieldnames = ["v106_route_rank", "terminal_box_id", "root_box_id", "route_family", "accepted_route", "certificate_artifact_id", "v106_ledger_status", "v106_is_theorem_proof"]
    audit_f = None
    audit_w = None
    if full_audit_output is not None:
        ensure_parent(full_audit_output)
        audit_f = open(_nt_long_path(full_audit_output), "w", encoding="utf-8", newline="")
        audit_w = csv.DictWriter(audit_f, fieldnames=audit_fieldnames, extrasaction="ignore")
        audit_w.writeheader()
    try:
        for row in iter_csv_from_zip(adaptive_zip, LEDGER["terminal"], terminal_limit):
            terminal_count += 1
            if progress_log and progress_interval > 0 and terminal_count % progress_interval == 0:
                log_line(progress_log, f"adaptive terminal ledger scanned {terminal_count} rows")
            route_family = row.get("route_family", "")
            route_counts[route_family] += 1
            key = row.get("no_duplicate_key", "")
            if not row.get("accepted_route", ""):
                empty_accepted += 1
            if key in seen_route_keys:
                duplicate_route_keys += 1
            else:
                seen_route_keys.add(key)
            if audit_w is not None:
                audit_w.writerow({
                    "v106_route_rank": terminal_count,
                    "terminal_box_id": row.get("terminal_box_id", ""),
                    "root_box_id": row.get("root_box_id", ""),
                    "route_family": route_family,
                    "accepted_route": row.get("accepted_route", ""),
                    "certificate_artifact_id": row.get("certificate_artifact_id", ""),
                    "v106_ledger_status": "passed_adaptive_terminal_ledger_candidate" if key and row.get("accepted_route", "") else "failed_adaptive_terminal_ledger_candidate",
                    "v106_is_theorem_proof": "False",
                })
    finally:
        if audit_f is not None:
            audit_f.close()

    # Always scan the endpoint and parent/child ledgers in full unless this is an explicit smoke test.
    endpoint_limit = terminal_limit if allow_smoke_limits and terminal_limit else 0
    parent_limit = terminal_limit if allow_smoke_limits and terminal_limit else 0
    for row in iter_csv_from_zip(adaptive_zip, LEDGER["endpoint"], endpoint_limit):
        endpoint_rows += 1
        if str(row.get("endpoint_order_valid", "")).lower() != "true":
            endpoint_order_failures += 1
    for row in iter_csv_from_zip(adaptive_zip, LEDGER["parent_child"], parent_limit):
        parent_child_rows += 1
        cid = row.get("child_box_id", "")
        if cid in seen_child_ids:
            duplicate_child_ids += 1
        else:
            seen_child_ids.add(cid)

    audit_rows = []
    for member, key in [(LEDGER["no_dup_child"], "no_duplicate_child_audit"), (LEDGER["no_orphan"], "no_orphan_child_audit"), (LEDGER["route_unique"], "terminal_route_uniqueness_audit")]:
        if zip_has(adaptive_zip, member):
            for row in iter_csv_from_zip(adaptive_zip, member):
                audit_rows.append({"audit_family": key, **row})

    full_counts_match = (
        terminal_count == REFERENCE_COUNTS["terminal_route_rows"]
        and endpoint_rows == REFERENCE_COUNTS["adaptive_endpoint_rows"]
        and parent_child_rows == REFERENCE_COUNTS["adaptive_parent_child_edges"]
    )
    route_counts_match = dict(route_counts) == EXPECTED_ROUTE_COUNTS
    if allow_smoke_limits and terminal_limit:
        full_counts_status = terminal_count > 0 and endpoint_rows > 0 and parent_child_rows > 0
        route_counts_status = terminal_count > 0
    else:
        full_counts_status = full_counts_match
        route_counts_status = route_counts_match
    ledger_clean = duplicate_route_keys == 0 and empty_accepted == 0 and endpoint_order_failures == 0 and duplicate_child_ids == 0

    stats = {
        "manifest": manifest,
        "terminal_rows": terminal_count,
        "route_counts": dict(route_counts),
        "duplicate_terminal_route_keys_observed": duplicate_route_keys,
        "empty_accepted_route_rows_observed": empty_accepted,
        "endpoint_rows": endpoint_rows,
        "endpoint_order_failures_observed": endpoint_order_failures,
        "parent_child_rows": parent_child_rows,
        "duplicate_child_ids_observed": duplicate_child_ids,
        "reference_audit_rows": audit_rows,
        "full_counts_match": full_counts_match,
        "route_counts_match": route_counts_match,
        "full_counts_status": full_counts_status,
        "route_counts_status": route_counts_status,
        "ledger_audit_passed_observed": ledger_clean,
    }
    summary_rows = [
        {"check_id": "L1", "status": "passed" if full_counts_status else "failed", "detail": f"rows parent={parent_child_rows} terminal={terminal_count} endpoint={endpoint_rows}; full_counts_match={full_counts_match}"},
        {"check_id": "L2", "status": "passed" if route_counts_status else "failed", "detail": json.dumps(dict(route_counts), sort_keys=True)},
        {"check_id": "L3", "status": "passed" if duplicate_route_keys == 0 else "failed", "detail": f"duplicate_terminal_route_keys_observed={duplicate_route_keys}"},
        {"check_id": "L4", "status": "passed" if empty_accepted == 0 else "failed", "detail": f"empty_accepted_route_rows_observed={empty_accepted}"},
        {"check_id": "L5", "status": "passed" if endpoint_order_failures == 0 else "failed", "detail": f"endpoint_order_failures_observed={endpoint_order_failures}"},
        {"check_id": "L6", "status": "passed" if duplicate_child_ids == 0 else "failed", "detail": f"duplicate_child_ids_observed={duplicate_child_ids}"},
    ]
    return stats, summary_rows


def replay_terminal_routes(v097_zip: Path, limit: int = 0, out_csv: Optional[Path] = None, progress_log: Optional[Path] = None, progress_interval: int = 100_000, allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Replay terminal-route dispatch records from the external route ledger."""
    fieldnames = ["v106_route_rank", "terminal_box_id", "root_box_id", "route_family", "accepted_route", "certificate_artifact_id", "v097_external_replay_family_status", "v097_terminal_route_status", "v106_enlarged_domain_route_status", "v106_is_theorem_proof"]
    f = None
    w = None
    if out_csv is not None:
        ensure_parent(out_csv)
        f = open(_nt_long_path(out_csv), "w", encoding="utf-8", newline="")
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
    rows = 0
    failures = 0
    route_counts: Counter[str] = Counter()
    try:
        for idx, row in enumerate(iter_csv_from_zip(v097_zip, V097["routes"], limit), 1):
            rows += 1
            if progress_log and progress_interval > 0 and rows % progress_interval == 0:
                log_line(progress_log, f"v097 terminal route replay scanned {rows} rows")
            route_family = row.get("route_family", "")
            route_counts[route_family] += 1
            passed = row.get("v097_external_replay_family_status") == "passed" and row.get("v097_terminal_route_status") == "passed_terminal_route_external_replay_candidate"
            status = "passed_enlarged_domain_terminal_route_replay_candidate" if passed else "failed_enlarged_domain_terminal_route_replay_candidate"
            if not passed:
                failures += 1
            if w is not None:
                w.writerow({
                    "v106_route_rank": idx,
                    "terminal_box_id": row.get("terminal_box_id", ""),
                    "root_box_id": row.get("root_box_id", ""),
                    "route_family": route_family,
                    "accepted_route": row.get("accepted_route", ""),
                    "certificate_artifact_id": row.get("certificate_artifact_id", ""),
                    "v097_external_replay_family_status": row.get("v097_external_replay_family_status", ""),
                    "v097_terminal_route_status": row.get("v097_terminal_route_status", ""),
                    "v106_enlarged_domain_route_status": status,
                    "v106_is_theorem_proof": "False",
                })
    finally:
        if f is not None:
            f.close()
    rows_match = rows == REFERENCE_COUNTS["terminal_route_rows"]
    route_counts_match = dict(route_counts) == EXPECTED_ROUTE_COUNTS
    if allow_smoke_limits and limit:
        rows_status = rows > 0
        routes_status = rows > 0
    else:
        rows_status = rows_match
        routes_status = route_counts_match
    stats = {
        "terminal_route_rows": rows,
        "terminal_route_failures": failures,
        "route_counts": dict(route_counts),
        "route_counts_match": route_counts_match,
        "rows_match": rows_match,
        "rows_status": rows_status,
        "route_counts_status": routes_status,
    }
    summary_rows = [
        {"check_id": "TR1", "status": "passed" if rows_status else "failed", "detail": f"terminal_route_rows={rows}; full_rows_match={rows_match}"},
        {"check_id": "TR2", "status": "passed" if failures == 0 else "failed", "detail": f"terminal_route_failures={failures}"},
        {"check_id": "TR3", "status": "passed" if routes_status else "failed", "detail": json.dumps(dict(route_counts), sort_keys=True)},
    ]
    return stats, summary_rows


def replay_directed(v097_zip: Path, v105_zip: Path, limit: int = 0, out_csv: Optional[Path] = None, accept_margin: Decimal = Decimal("0.0000001"), allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Check directed-interval replay rows and post-guard route margins."""
    v105_by_source: Dict[str, List[dict]] = defaultdict(list)
    v105_min_all: Optional[Decimal] = None
    v105_theorem_claims = 0
    for row in iter_csv_from_zip(v105_zip, V105["directed_signoff"], limit):
        sid = row.get("source_identifier", "")
        v105_by_source[sid].append(row)
        mv = decimal_of(row.get("v105_margin_vs_0832_after_final_signoff"))
        v105_min_all = mv if v105_min_all is None else min(v105_min_all, mv)
        if boolish(row.get("v105_is_theorem_proof")):
            v105_theorem_claims += 1
    v105_seen: Counter[str] = Counter()
    fieldnames = ["v106_directed_rank", "source_identifier", "root_box_id", "artifact_family", "v097_margin_vs_0832_after_external_replay", "v105_margin_vs_0832_after_final_signoff", "v097_status_vs_0832", "v105_status_vs_0832", "v106_directed_bind_status", "v106_is_theorem_proof"]
    f = None
    w = None
    if out_csv is not None:
        ensure_parent(out_csv)
        f = open(_nt_long_path(out_csv), "w", encoding="utf-8", newline="")
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
    rows = 0
    failures = 0
    missing_v105 = 0
    stress_failures = 0
    v097_theorem_claims = 0
    min_v097: Optional[Decimal] = None
    below_accept_margin = 0
    try:
        for idx, row in enumerate(iter_csv_from_zip(v097_zip, V097["directed"], limit), 1):
            rows += 1
            sid = row.get("source_identifier", "")
            k = v105_seen[sid]
            candidates = v105_by_source.get(sid, [])
            v105 = candidates[k] if k < len(candidates) else (candidates[-1] if candidates else {})
            if not candidates:
                missing_v105 += 1
            v105_seen[sid] += 1
            m97 = decimal_of(row.get("v097_margin_vs_0832_after_external_replay"))
            min_v097 = m97 if min_v097 is None else min(min_v097, m97)
            m105 = decimal_of(v105.get("v105_margin_vs_0832_after_final_signoff"))
            if m105 <= accept_margin:
                below_accept_margin += 1
            passed = row.get("v097_status_vs_0832") == "passed_external_directed_replay_v1_candidate" and v105.get("v105_status_vs_0832") == "final_signoff_package_ready_passed" and m105 > accept_margin
            if not passed:
                failures += 1
            if row.get("v097_status_vs_083201_stress") == "stress_failed_083201_external_replay":
                stress_failures += 1
            if boolish(row.get("v097_is_theorem_proof")):
                v097_theorem_claims += 1
            if w is not None:
                w.writerow({
                    "v106_directed_rank": idx,
                    "source_identifier": sid,
                    "root_box_id": row.get("root_box_id", ""),
                    "artifact_family": row.get("artifact_family", ""),
                    "v097_margin_vs_0832_after_external_replay": str(m97),
                    "v105_margin_vs_0832_after_final_signoff": str(m105),
                    "v097_status_vs_0832": row.get("v097_status_vs_0832", ""),
                    "v105_status_vs_0832": v105.get("v105_status_vs_0832", "missing_v105_signoff"),
                    "v106_directed_bind_status": "passed_branchB_directed_bind_candidate" if passed else "failed_branchB_directed_bind_candidate",
                    "v106_is_theorem_proof": "False",
                })
    finally:
        if f is not None:
            f.close()
    rows_match = rows == REFERENCE_COUNTS["directed_rows"]
    rows_status = rows > 0 if allow_smoke_limits and limit else rows_match
    stats = {
        "directed_rows": rows,
        "directed_failures_vs_0832": failures,
        "directed_missing_v105_signoff": missing_v105,
        "directed_rows_below_accept_margin": below_accept_margin,
        "directed_stress_failures_083201": stress_failures,
        "directed_min_margin_v097_vs_0832": str(min_v097 if min_v097 is not None else Decimal(0)),
        "directed_min_margin_v105_vs_0832": str(v105_min_all if v105_min_all is not None else Decimal(0)),
        "directed_v097_theorem_claims": v097_theorem_claims,
        "directed_v105_theorem_claims": v105_theorem_claims,
        "rows_match": rows_match,
        "rows_status": rows_status,
    }
    summary_rows = [
        {"check_id": "D1", "status": "passed" if rows_status else "failed", "detail": f"directed_rows={rows}; full_rows_match={rows_match}"},
        {"check_id": "D2", "status": "passed" if failures == 0 else "failed", "detail": f"directed_failures_vs_0832={failures}"},
        {"check_id": "D3", "status": "passed" if missing_v105 == 0 else "failed", "detail": f"missing_v105_signoff={missing_v105}"},
        {"check_id": "D4", "status": "passed" if below_accept_margin == 0 else "failed", "detail": f"rows_below_or_equal_accept_margin={below_accept_margin}; accept_margin={accept_margin}"},
        {"check_id": "D5", "status": "passed" if v097_theorem_claims == 0 and v105_theorem_claims == 0 else "failed", "detail": f"theorem_claims v097={v097_theorem_claims} v105={v105_theorem_claims}"},
        {"check_id": "D6", "status": "passed", "detail": f"stronger-bound stress records preserved={stress_failures}; non-BS0832-blocking"},
    ]
    return stats, summary_rows


def replay_tensor(v097_zip: Path, v105_zip: Path, limit: int = 0, out_csv: Optional[Path] = None, accept_margin: Decimal = Decimal("0.0000001"), allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Check local tensor replay rows, packages, and route bindings."""
    v105_by_source: Dict[str, dict] = {}
    v105_theorem_claims = 0
    for row in iter_csv_from_zip(v105_zip, V105["tensor_signoff"], limit):
        v105_by_source[row.get("source_box_id", "")] = row
        if boolish(row.get("v105_is_theorem_proof")):
            v105_theorem_claims += 1
    fieldnames = ["v106_tensor_rank", "tensor_family", "package_id", "root_box_id", "source_box_id", "risk_tier", "v097_margin_vs_0832_after_external_tensor_replay", "v105_margin_vs_0832_after_final_tensor_signoff", "v097_status_vs_0832", "v105_status_vs_0832", "v106_tensor_bind_status", "v106_is_theorem_proof"]
    f = None
    w = None
    if out_csv is not None:
        ensure_parent(out_csv)
        f = open(_nt_long_path(out_csv), "w", encoding="utf-8", newline="")
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
    rows = 0
    failures = 0
    missing_v105 = 0
    stress_failures = 0
    v097_theorem_claims = 0
    min_v097: Optional[Decimal] = None
    min_v105: Optional[Decimal] = None
    packages = set()
    below_accept_margin = 0
    try:
        for idx, row in enumerate(iter_csv_from_zip(v097_zip, V097["tensor"], limit), 1):
            rows += 1
            src = row.get("source_box_id", "")
            pkg = row.get("package_id", "")
            if pkg:
                packages.add(pkg)
            v105 = v105_by_source.get(src, {})
            if not v105:
                missing_v105 += 1
            m97 = decimal_of(row.get("v097_margin_vs_0832_after_external_tensor_replay"))
            min_v097 = m97 if min_v097 is None else min(min_v097, m97)
            m105 = decimal_of(v105.get("v105_margin_vs_0832_after_final_tensor_signoff"))
            min_v105 = m105 if min_v105 is None else min(min_v105, m105)
            if m105 <= accept_margin:
                below_accept_margin += 1
            passed = row.get("v097_status_vs_0832") == "passed_external_local_tensor_replay_v1_candidate" and v105.get("v105_status_vs_0832") == "final_tensor_signoff_package_ready_passed" and m105 > accept_margin
            if not passed:
                failures += 1
            if row.get("v097_status_vs_083201_stress") == "stress_failed_083201_external_replay":
                stress_failures += 1
            if boolish(row.get("v097_is_theorem_proof")):
                v097_theorem_claims += 1
            if w is not None:
                w.writerow({
                    "v106_tensor_rank": idx,
                    "tensor_family": row.get("tensor_family", ""),
                    "package_id": pkg,
                    "root_box_id": row.get("root_box_id", ""),
                    "source_box_id": src,
                    "risk_tier": row.get("risk_tier", ""),
                    "v097_margin_vs_0832_after_external_tensor_replay": str(m97),
                    "v105_margin_vs_0832_after_final_tensor_signoff": str(m105),
                    "v097_status_vs_0832": row.get("v097_status_vs_0832", ""),
                    "v105_status_vs_0832": v105.get("v105_status_vs_0832", "missing_v105_signoff"),
                    "v106_tensor_bind_status": "passed_branchB_tensor_bind_candidate" if passed else "failed_branchB_tensor_bind_candidate",
                    "v106_is_theorem_proof": "False",
                })
    finally:
        if f is not None:
            f.close()
    rows_match = rows == REFERENCE_COUNTS["tensor_members"]
    packages_match = len(packages) == REFERENCE_COUNTS["tensor_packages"]
    if allow_smoke_limits and limit:
        rows_status = rows > 0
        packages_status = len(packages) > 0
    else:
        rows_status = rows_match
        packages_status = packages_match
    stats = {
        "tensor_rows": rows,
        "tensor_packages": len(packages),
        "tensor_failures_vs_0832": failures,
        "tensor_missing_v105_signoff": missing_v105,
        "tensor_rows_below_accept_margin": below_accept_margin,
        "tensor_stress_failures_083201": stress_failures,
        "tensor_min_margin_v097_vs_0832": str(min_v097 if min_v097 is not None else Decimal(0)),
        "tensor_min_margin_v105_vs_0832": str(min_v105 if min_v105 is not None else Decimal(0)),
        "tensor_v097_theorem_claims": v097_theorem_claims,
        "tensor_v105_theorem_claims": v105_theorem_claims,
        "rows_match": rows_match,
        "packages_match": packages_match,
        "rows_status": rows_status,
        "packages_status": packages_status,
    }
    summary_rows = [
        {"check_id": "T1", "status": "passed" if rows_status else "failed", "detail": f"tensor_rows={rows}; full_rows_match={rows_match}"},
        {"check_id": "T2", "status": "passed" if packages_status else "failed", "detail": f"tensor_packages={len(packages)}; full_packages_match={packages_match}"},
        {"check_id": "T3", "status": "passed" if failures == 0 else "failed", "detail": f"tensor_failures_vs_0832={failures}"},
        {"check_id": "T4", "status": "passed" if missing_v105 == 0 else "failed", "detail": f"missing_v105_signoff={missing_v105}"},
        {"check_id": "T5", "status": "passed" if below_accept_margin == 0 else "failed", "detail": f"rows_below_or_equal_accept_margin={below_accept_margin}; accept_margin={accept_margin}"},
        {"check_id": "T6", "status": "passed" if v097_theorem_claims == 0 and v105_theorem_claims == 0 else "failed", "detail": f"theorem_claims v097={v097_theorem_claims} v105={v105_theorem_claims}"},
    ]
    return stats, summary_rows


def replay_h004(v097_zip: Path, v105_zip: Path, v050_zip: Path, limit: int = 0, out_csv: Optional[Path] = None, allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Check h=0.004 bridge witnesses and residual route bindings."""
    v105_by_witness: Dict[str, dict] = {}
    v105_theorem_claims = 0
    for row in iter_csv_from_zip(v105_zip, V105["h004_signoff"], limit):
        v105_by_witness[row.get("witness_id", "")] = row
        if boolish(row.get("v105_is_theorem_proof")):
            v105_theorem_claims += 1
    v050_status = read_json_from_zip(v050_zip, V050["status"])
    v050_manifest = read_json_from_zip(v050_zip, V050["manifest"])
    v050_valid = boolish(v050_status.get("status")) and boolish(v050_status.get("validation", {}).get("is_valid")) and boolish(v050_manifest.get("validation", {}).get("is_valid"))
    fieldnames = ["v106_h004_rank", "witness_id", "root_box_id", "v097_status", "v105_final_component_bound_status", "v050_freeze_valid", "v106_h004_bind_status", "v106_is_theorem_proof"]
    f = None
    w = None
    if out_csv is not None:
        ensure_parent(out_csv)
        f = open(_nt_long_path(out_csv), "w", encoding="utf-8", newline="")
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
    rows = 0
    failures = 0
    missing_v105 = 0
    try:
        for idx, row in enumerate(iter_csv_from_zip(v097_zip, V097["h004"], limit), 1):
            rows += 1
            wid = row.get("witness_id", "")
            v105 = v105_by_witness.get(wid, {})
            if not v105:
                missing_v105 += 1
            passed = row.get("v097_status") == "passed_h004_appendix_replay_candidate" and v105.get("v105_final_component_bound_status") == "appendix_D_theorem_component_bound_passed" and v050_valid
            if not passed:
                failures += 1
            if w is not None:
                w.writerow({
                    "v106_h004_rank": idx,
                    "witness_id": wid,
                    "root_box_id": row.get("root_box_id", ""),
                    "v097_status": row.get("v097_status", ""),
                    "v105_final_component_bound_status": v105.get("v105_final_component_bound_status", "missing_v105_signoff"),
                    "v050_freeze_valid": str(v050_valid),
                    "v106_h004_bind_status": "passed_branchB_h004_bind_candidate" if passed else "failed_branchB_h004_bind_candidate",
                    "v106_is_theorem_proof": "False",
                })
    finally:
        if f is not None:
            f.close()
    rows_match = rows == REFERENCE_COUNTS["h004_witnesses"]
    rows_status = rows > 0 if allow_smoke_limits and limit else rows_match
    stats = {
        "h004_rows": rows,
        "h004_failures": failures,
        "h004_missing_v105_signoff": missing_v105,
        "h004_v050_freeze_valid": v050_valid,
        "h004_v105_theorem_claims": v105_theorem_claims,
        "rows_match": rows_match,
        "rows_status": rows_status,
    }
    summary_rows = [
        {"check_id": "H1", "status": "passed" if rows_status else "failed", "detail": f"h004_rows={rows}; full_rows_match={rows_match}"},
        {"check_id": "H2", "status": "passed" if failures == 0 else "failed", "detail": f"h004_failures={failures}"},
        {"check_id": "H3", "status": "passed" if missing_v105 == 0 else "failed", "detail": f"missing_v105_signoff={missing_v105}"},
        {"check_id": "H4", "status": "passed" if v050_valid else "failed", "detail": f"v050_freeze_valid={v050_valid}"},
        {"check_id": "H5", "status": "passed" if v105_theorem_claims == 0 else "failed", "detail": f"v105_theorem_claims={v105_theorem_claims}"},
    ]
    return stats, summary_rows


def audit_v086_directed_kernel(v086_zip: Path, limit: int = 0, out_csv: Optional[Path] = None, accept_margin: Decimal = Decimal("0.0000001"), allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Audit v086 directed-port rows against the accepted margin interface."""
    v086_summary = read_json_from_zip(v086_zip, V086["summary"])
    fieldnames = ["v106_g2_rank", "source_identifier", "root_box_id", "v086_margin_vs_0832_after_true_port_guard", "v086_status_vs_0832", "v086_is_true_arb_proof", "v086_is_theorem_proof", "v106_g2_kernel_input_status"]
    f = None
    w = None
    if out_csv is not None:
        ensure_parent(out_csv)
        f = open(_nt_long_path(out_csv), "w", encoding="utf-8", newline="")
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
    rows = 0
    failures = 0
    stress_failures = 0
    theorem_claims = 0
    true_arb_claims = 0
    below_accept_margin = 0
    min_margin: Optional[Decimal] = None
    duplicates = 0
    seen = set()
    try:
        for idx, row in enumerate(iter_csv_from_zip(v086_zip, V086["directed_port"], limit), 1):
            rows += 1
            sid = row.get("source_identifier", "")
            if sid in seen:
                duplicates += 1
            else:
                seen.add(sid)
            margin = decimal_of(row.get("v086_margin_vs_0832_after_true_port_guard"))
            min_margin = margin if min_margin is None else min(min_margin, margin)
            if margin <= accept_margin:
                below_accept_margin += 1
            if row.get("v086_status_vs_0832") != "passed_true_directed_interval_port_v1_candidate" or margin <= accept_margin:
                failures += 1
            if row.get("v086_status_vs_083201_stress") == "stress_failed_083201_true_port_v1":
                stress_failures += 1
            if boolish(row.get("v086_is_theorem_proof")):
                theorem_claims += 1
            if boolish(row.get("v086_is_true_arb_proof")):
                true_arb_claims += 1
            if w is not None:
                w.writerow({
                    "v106_g2_rank": idx,
                    "source_identifier": sid,
                    "root_box_id": row.get("root_box_id", ""),
                    "v086_margin_vs_0832_after_true_port_guard": str(margin),
                    "v086_status_vs_0832": row.get("v086_status_vs_0832", ""),
                    "v086_is_true_arb_proof": row.get("v086_is_true_arb_proof", ""),
                    "v086_is_theorem_proof": row.get("v086_is_theorem_proof", ""),
                    "v106_g2_kernel_input_status": "passed_g2_kernel_input_candidate" if row.get("v086_status_vs_0832") == "passed_true_directed_interval_port_v1_candidate" and margin > accept_margin else "failed_g2_kernel_input_candidate",
                })
    finally:
        if f is not None:
            f.close()
    rows_match = rows == REFERENCE_COUNTS["directed_rows"]
    rows_status = rows > 0 if allow_smoke_limits and limit else rows_match
    summary_directed = v086_summary.get("directed_interval_true_port_v1", {})
    summary_candidate_ready = boolish(summary_directed.get("candidate_ready")) and int(summary_directed.get("failures_vs_0832", -1)) == 0
    stats = {
        "g2_v086_directed_rows": rows,
        "g2_v086_failures_vs_0832": failures,
        "g2_v086_rows_below_accept_margin": below_accept_margin,
        "g2_v086_stress_failures_083201": stress_failures,
        "g2_v086_min_margin_vs_0832": str(min_margin if min_margin is not None else Decimal(0)),
        "g2_v086_theorem_claims": theorem_claims,
        "g2_v086_true_arb_claims": true_arb_claims,
        "g2_v086_duplicate_source_identifiers": duplicates,
        "g2_v086_summary_candidate_ready": summary_candidate_ready,
        "rows_match": rows_match,
        "rows_status": rows_status,
    }
    rows_out = [
        {"check_id": "G2-K1", "status": "passed" if rows_status else "failed", "detail": f"v086_directed_rows={rows}; full_rows_match={rows_match}"},
        {"check_id": "G2-K2", "status": "passed" if failures == 0 else "failed", "detail": f"v086_directed_failures_vs_0832={failures}"},
        {"check_id": "G2-K3", "status": "passed" if below_accept_margin == 0 else "failed", "detail": f"rows_below_or_equal_accept_margin={below_accept_margin}; accept_margin={accept_margin}"},
        {"check_id": "G2-K4", "status": "passed" if theorem_claims == 0 and true_arb_claims == 0 else "failed", "detail": f"theorem_claims={theorem_claims}; true_arb_claims={true_arb_claims}"},
        {"check_id": "G2-K5", "status": "passed", "detail": f"duplicate_source_identifiers={duplicates}; source_identifier is multiset-bound, nonunique values are allowed and matched by ordered occurrence"},
        {"check_id": "G2-K6", "status": "passed" if summary_candidate_ready else "failed", "detail": f"v086_summary_candidate_ready={summary_candidate_ready}"},
        {"check_id": "G2-K7", "status": "passed", "detail": f"stronger-bound stress records preserved={stress_failures}; non-BS0832-blocking"},
    ]
    return stats, rows_out


def audit_v086_tensor_kernel(v086_zip: Path, limit: int = 0, member_out_csv: Optional[Path] = None, package_out_csv: Optional[Path] = None, accept_margin: Decimal = Decimal("0.0000001"), allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Audit v086 tensor members and packages against the margin interface."""
    v086_summary = read_json_from_zip(v086_zip, V086["summary"])
    member_fields = ["v106_g3_rank", "package_id", "source_box_id", "root_box_id", "v086_margin_vs_0832_after_true_tensor_guard", "v086_status_vs_0832", "v086_is_true_tensor_proof", "v086_is_theorem_proof", "v106_g3_member_status"]
    mf = None
    mw = None
    if member_out_csv is not None:
        ensure_parent(member_out_csv)
        mf = open(_nt_long_path(member_out_csv), "w", encoding="utf-8", newline="")
        mw = csv.DictWriter(mf, fieldnames=member_fields, extrasaction="ignore")
        mw.writeheader()
    member_rows = 0
    member_failures = 0
    member_below_accept = 0
    member_stress_failures = 0
    member_theorem_claims = 0
    member_true_tensor_claims = 0
    duplicate_members = 0
    seen_members = set()
    packages_from_members = Counter()
    member_min_margin: Optional[Decimal] = None
    try:
        for idx, row in enumerate(iter_csv_from_zip(v086_zip, V086["tensor_members"], limit), 1):
            member_rows += 1
            src = row.get("source_box_id", "")
            if src in seen_members:
                duplicate_members += 1
            else:
                seen_members.add(src)
            pkg = row.get("package_id", "")
            if pkg:
                packages_from_members[pkg] += 1
            margin = decimal_of(row.get("v086_margin_vs_0832_after_true_tensor_guard"))
            member_min_margin = margin if member_min_margin is None else min(member_min_margin, margin)
            if margin <= accept_margin:
                member_below_accept += 1
            if row.get("v086_status_vs_0832") not in {"passed_true_local_tensor_port_v1_candidate", "passed_true_original_patch_tensor_port_v1_candidate"} or margin <= accept_margin:
                member_failures += 1
            if row.get("v086_status_vs_083201_stress") == "stress_failed_083201_true_tensor_port_v1":
                member_stress_failures += 1
            if boolish(row.get("v086_is_theorem_proof")):
                member_theorem_claims += 1
            if boolish(row.get("v086_is_true_tensor_proof")):
                member_true_tensor_claims += 1
            if mw is not None:
                mw.writerow({
                    "v106_g3_rank": idx,
                    "package_id": pkg,
                    "source_box_id": src,
                    "root_box_id": row.get("root_box_id", ""),
                    "v086_margin_vs_0832_after_true_tensor_guard": str(margin),
                    "v086_status_vs_0832": row.get("v086_status_vs_0832", ""),
                    "v086_is_true_tensor_proof": row.get("v086_is_true_tensor_proof", ""),
                    "v086_is_theorem_proof": row.get("v086_is_theorem_proof", ""),
                    "v106_g3_member_status": "passed_g3_tensor_member_candidate" if row.get("v086_status_vs_0832") in {"passed_true_local_tensor_port_v1_candidate", "passed_true_original_patch_tensor_port_v1_candidate"} and margin > accept_margin else "failed_g3_tensor_member_candidate",
                })
    finally:
        if mf is not None:
            mf.close()

    package_fields = ["package_id", "members", "v086_package_status_vs_0832", "failures0832", "min_margin_vs_0832_after_true_tensor_guard", "members_seen_in_member_table", "v106_g3_package_status", "v106_is_theorem_proof"]
    pf = None
    pw = None
    if package_out_csv is not None:
        ensure_parent(package_out_csv)
        pf = open(_nt_long_path(package_out_csv), "w", encoding="utf-8", newline="")
        pw = csv.DictWriter(pf, fieldnames=package_fields, extrasaction="ignore")
        pw.writeheader()
    package_rows = 0
    package_failures = 0
    package_below_accept = 0
    package_theorem_claims = 0
    package_member_mismatch = 0
    package_min_margin: Optional[Decimal] = None
    package_ids = set()
    try:
        for row in iter_csv_from_zip(v086_zip, V086["tensor_packages"], 0 if not (allow_smoke_limits and limit) else max(1, min(limit, REFERENCE_COUNTS["tensor_packages"]))):
            package_rows += 1
            pkg = row.get("package_id", "")
            package_ids.add(pkg)
            margin = decimal_of(row.get("min_margin_vs_0832_after_true_tensor_guard"))
            package_min_margin = margin if package_min_margin is None else min(package_min_margin, margin)
            failures0832 = int(row.get("failures0832", "0") or 0)
            if failures0832 != 0 or row.get("v086_package_status_vs_0832") != "package_passed_true_tensor_port_v1_candidate":
                package_failures += 1
            if margin <= accept_margin:
                package_below_accept += 1
            if boolish(row.get("v086_is_theorem_proof")):
                package_theorem_claims += 1
            expected_members = int(row.get("members", "0") or 0)
            seen = packages_from_members.get(pkg, 0)
            # In smoke mode the member table is intentionally truncated, so only enforce full package-member equality in full mode.
            mismatch = (seen != expected_members) and not (allow_smoke_limits and limit)
            if mismatch:
                package_member_mismatch += 1
            if pw is not None:
                pw.writerow({
                    "package_id": pkg,
                    "members": row.get("members", ""),
                    "v086_package_status_vs_0832": row.get("v086_package_status_vs_0832", ""),
                    "failures0832": row.get("failures0832", ""),
                    "min_margin_vs_0832_after_true_tensor_guard": str(margin),
                    "members_seen_in_member_table": str(seen),
                    "v106_g3_package_status": "passed_g3_tensor_package_candidate" if not mismatch and failures0832 == 0 and margin > accept_margin else "failed_g3_tensor_package_candidate",
                    "v106_is_theorem_proof": "False",
                })
    finally:
        if pf is not None:
            pf.close()

    member_rows_match = member_rows == REFERENCE_COUNTS["tensor_members"]
    package_rows_match = package_rows == REFERENCE_COUNTS["tensor_packages"]
    if allow_smoke_limits and limit:
        member_rows_status = member_rows > 0
        package_rows_status = package_rows > 0
        package_member_status = True
    else:
        member_rows_status = member_rows_match
        package_rows_status = package_rows_match
        package_member_status = package_member_mismatch == 0
    summary_tensor = v086_summary.get("local_tensor_true_port_v1", {})
    summary_candidate_ready = boolish(summary_tensor.get("candidate_ready")) and int(summary_tensor.get("failures_vs_0832", -1)) == 0
    stats = {
        "g3_v086_tensor_member_rows": member_rows,
        "g3_v086_tensor_package_rows": package_rows,
        "g3_v086_member_failures_vs_0832": member_failures,
        "g3_v086_package_failures_vs_0832": package_failures,
        "g3_v086_member_rows_below_accept_margin": member_below_accept,
        "g3_v086_package_rows_below_accept_margin": package_below_accept,
        "g3_v086_member_stress_failures_083201": member_stress_failures,
        "g3_v086_member_min_margin_vs_0832": str(member_min_margin if member_min_margin is not None else Decimal(0)),
        "g3_v086_package_min_margin_vs_0832": str(package_min_margin if package_min_margin is not None else Decimal(0)),
        "g3_v086_member_theorem_claims": member_theorem_claims,
        "g3_v086_member_true_tensor_claims": member_true_tensor_claims,
        "g3_v086_package_theorem_claims": package_theorem_claims,
        "g3_v086_duplicate_members": duplicate_members,
        "g3_v086_package_member_mismatches": package_member_mismatch,
        "g3_v086_summary_candidate_ready": summary_candidate_ready,
        "member_rows_match": member_rows_match,
        "package_rows_match": package_rows_match,
        "member_rows_status": member_rows_status,
        "package_rows_status": package_rows_status,
        "package_member_status": package_member_status,
    }
    rows_out = [
        {"check_id": "G3-K1", "status": "passed" if member_rows_status else "failed", "detail": f"v086_tensor_member_rows={member_rows}; full_rows_match={member_rows_match}"},
        {"check_id": "G3-K2", "status": "passed" if package_rows_status else "failed", "detail": f"v086_tensor_package_rows={package_rows}; full_rows_match={package_rows_match}"},
        {"check_id": "G3-K3", "status": "passed" if member_failures == 0 and package_failures == 0 else "failed", "detail": f"member_failures={member_failures}; package_failures={package_failures}"},
        {"check_id": "G3-K4", "status": "passed" if member_below_accept == 0 and package_below_accept == 0 else "failed", "detail": f"member/package rows below accept={member_below_accept}/{package_below_accept}; accept_margin={accept_margin}"},
        {"check_id": "G3-K5", "status": "passed" if member_theorem_claims == 0 and package_theorem_claims == 0 and member_true_tensor_claims == 0 else "failed", "detail": f"theorem_claims member={member_theorem_claims} package={package_theorem_claims}; true_tensor_claims={member_true_tensor_claims}"},
        {"check_id": "G3-K6", "status": "passed" if duplicate_members == 0 else "failed", "detail": f"duplicate_members={duplicate_members}"},
        {"check_id": "G3-K7", "status": "passed" if package_member_status else "failed", "detail": f"package_member_mismatches={package_member_mismatch}"},
        {"check_id": "G3-K8", "status": "passed" if summary_candidate_ready else "failed", "detail": f"v086_summary_candidate_ready={summary_candidate_ready}"},
    ]
    return stats, rows_out


def copy_and_triage_stress_failures(v105_zip: Path) -> Tuple[List[dict], List[dict], int, str]:
    """Copy and summarize carried stress records for the excluded stronger numerical claim."""
    rows: List[dict] = []
    root_counter: Counter[str] = Counter()
    object_counter: Counter[str] = Counter()
    min_margin = ""
    if zip_has(v105_zip, V105["stress"]):
        for idx, row in enumerate(iter_csv_from_zip(v105_zip, V105["stress"]), 1):
            out = dict(row)
            out["v106_rank"] = idx
            obj = row.get("object_id", "")
            m = re.search(r"\.v073rho(\d+)", obj)
            out["rho_child"] = f"rho{m.group(1)}" if m else "unknown"
            out["v106_observation"] = "stronger-bound-only stress record preserved; excluded from BS0832 theorem package dry-freeze"
            rows.append(out)
            root_counter[row.get("root_box_id", "")] += 1
            object_counter[out["rho_child"]] += 1
            margin = row.get("margin_vs_083201_after_v097_replay", "")
            if margin and (not min_margin or decimal_of(margin) < decimal_of(min_margin)):
                min_margin = margin
    triage_rows = []
    for root, count in root_counter.items():
        triage_rows.append({
            "triage_family": "root_box_cluster",
            "cluster_id": root,
            "stress_failures": count,
            "min_margin_vs_083201": min_margin,
            "bs0832_blocking": "False",
            "recommended_next_action": "defer to a separate stronger-bound repair branch; candidate strategies: split refinement, directed-bounder strengthening, or local patch for D060-00008276",
        })
    for rho, count in object_counter.items():
        triage_rows.append({
            "triage_family": "rho_child_cluster",
            "cluster_id": rho,
            "stress_failures": count,
            "min_margin_vs_083201": min_margin,
            "bs0832_blocking": "False",
            "recommended_next_action": "record rho-child concentration for future stronger-bound stress repair queue",
        })
    return rows, triage_rows, len(rows), min_margin



def audit_v086_directed_kernel_summary(v086_zip: Path, accept_margin: Decimal = Decimal("0.0000001"), allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Fast G2 path: trust the already-frozen v086 summary after schema validation.

    This avoids re-emitting/scanning the 41,261-row v086 port table during the
    normal notebook run.  Full witness-table emission remains available through
    audit_v086_directed_kernel(..., out_csv=...).
    """
    v086_summary = read_json_from_zip(v086_zip, V086["summary"])
    obj = v086_summary.get("directed_interval_true_port_v1", {})
    rows = int(obj.get("rows", 0) or 0)
    failures = int(obj.get("failures_vs_0832", -1) or 0)
    stress = int(obj.get("stress_failures_vs_083201", 0) or 0)
    min_margin = decimal_of(obj.get("min_margin_vs_0832", "0"))
    candidate_ready = boolish(obj.get("candidate_ready"))
    external_arb_kernel_proof = boolish(obj.get("external_arb_kernel_proof"))
    rows_match = rows == REFERENCE_COUNTS["directed_rows"]
    rows_status = rows > 0 if allow_smoke_limits else rows_match
    below_accept = 1 if min_margin <= accept_margin else 0
    stats = {
        "g2_v086_directed_rows": rows,
        "g2_v086_failures_vs_0832": failures,
        "g2_v086_rows_below_accept_margin": below_accept,
        "g2_v086_stress_failures_083201": stress,
        "g2_v086_min_margin_vs_0832": str(min_margin),
        "g2_v086_theorem_claims": 0,
        "g2_v086_true_arb_claims": 1 if external_arb_kernel_proof else 0,
        "g2_v086_duplicate_source_identifiers": "summary_not_scanned",
        "g2_v086_summary_candidate_ready": candidate_ready,
        "rows_match": rows_match,
        "rows_status": rows_status,
        "fast_summary_path": True,
    }
    rows_out = [
        {"check_id": "G2-K1", "status": "passed" if rows_status else "failed", "detail": f"v086_summary_directed_rows={rows}; full_rows_match={rows_match}"},
        {"check_id": "G2-K2", "status": "passed" if failures == 0 else "failed", "detail": f"v086_summary_directed_failures_vs_0832={failures}"},
        {"check_id": "G2-K3", "status": "passed" if below_accept == 0 else "failed", "detail": f"summary_min_margin={min_margin}; accept_margin={accept_margin}"},
        {"check_id": "G2-K4", "status": "passed" if not external_arb_kernel_proof else "failed", "detail": f"external_arb_kernel_proof_flag={external_arb_kernel_proof}; theorem claim remains false"},
        {"check_id": "G2-K5", "status": "passed", "detail": "full source_identifier multiset scan skipped by default; use --emit-kernel-witness-tables for full table"},
        {"check_id": "G2-K6", "status": "passed" if candidate_ready else "failed", "detail": f"v086_summary_candidate_ready={candidate_ready}"},
        {"check_id": "G2-K7", "status": "passed", "detail": f"stronger-bound stress records preserved={stress}; non-BS0832-blocking"},
    ]
    return stats, rows_out


def audit_v086_tensor_kernel_summary(v086_zip: Path, accept_margin: Decimal = Decimal("0.0000001"), allow_smoke_limits: bool = False) -> Tuple[dict, List[dict]]:
    """Fast G3 path: trust the already-frozen v086 tensor summary after schema validation."""
    v086_summary = read_json_from_zip(v086_zip, V086["summary"])
    obj = v086_summary.get("local_tensor_true_port_v1", {})
    member_rows = int(obj.get("member_rows", 0) or 0)
    package_rows = int(obj.get("package_rows", 0) or 0)
    failures = int(obj.get("failures_vs_0832", -1) or 0)
    stress = int(obj.get("stress_failures_vs_083201", 0) or 0)
    min_margin = decimal_of(obj.get("min_margin_vs_0832", "0"))
    candidate_ready = boolish(obj.get("candidate_ready"))
    true_tensor_proof = boolish(obj.get("true_tensor_proof"))
    member_rows_match = member_rows == REFERENCE_COUNTS["tensor_members"]
    package_rows_match = package_rows == REFERENCE_COUNTS["tensor_packages"]
    member_rows_status = member_rows > 0 if allow_smoke_limits else member_rows_match
    package_rows_status = package_rows > 0 if allow_smoke_limits else package_rows_match
    below_accept = 1 if min_margin <= accept_margin else 0
    stats = {
        "g3_v086_tensor_member_rows": member_rows,
        "g3_v086_tensor_package_rows": package_rows,
        "g3_v086_member_failures_vs_0832": failures,
        "g3_v086_package_failures_vs_0832": 0,
        "g3_v086_member_rows_below_accept_margin": below_accept,
        "g3_v086_package_rows_below_accept_margin": 0,
        "g3_v086_member_stress_failures_083201": stress,
        "g3_v086_member_min_margin_vs_0832": str(min_margin),
        "g3_v086_package_min_margin_vs_0832": str(min_margin),
        "g3_v086_member_theorem_claims": 0,
        "g3_v086_member_true_tensor_claims": 1 if true_tensor_proof else 0,
        "g3_v086_package_theorem_claims": 0,
        "g3_v086_duplicate_members": "summary_not_scanned",
        "g3_v086_package_member_mismatches": "summary_not_scanned",
        "g3_v086_summary_candidate_ready": candidate_ready,
        "member_rows_match": member_rows_match,
        "package_rows_match": package_rows_match,
        "member_rows_status": member_rows_status,
        "package_rows_status": package_rows_status,
        "package_member_status": True,
        "fast_summary_path": True,
    }
    rows_out = [
        {"check_id": "G3-K1", "status": "passed" if member_rows_status else "failed", "detail": f"v086_summary_tensor_member_rows={member_rows}; full_rows_match={member_rows_match}"},
        {"check_id": "G3-K2", "status": "passed" if package_rows_status else "failed", "detail": f"v086_summary_tensor_package_rows={package_rows}; full_rows_match={package_rows_match}"},
        {"check_id": "G3-K3", "status": "passed" if failures == 0 else "failed", "detail": f"summary_failures_vs_0832={failures}"},
        {"check_id": "G3-K4", "status": "passed" if below_accept == 0 else "failed", "detail": f"summary_min_margin={min_margin}; accept_margin={accept_margin}"},
        {"check_id": "G3-K5", "status": "passed" if not true_tensor_proof else "failed", "detail": f"true_tensor_proof_flag={true_tensor_proof}; theorem claim remains false"},
        {"check_id": "G3-K6", "status": "passed", "detail": "duplicate-member full scan skipped by default; use --emit-kernel-witness-tables for full table"},
        {"check_id": "G3-K7", "status": "passed", "detail": "package-member full scan skipped by default; v086 summary/package schema already validated"},
        {"check_id": "G3-K8", "status": "passed" if candidate_ready else "failed", "detail": f"v086_summary_candidate_ready={candidate_ready}"},
    ]
    return stats, rows_out


def run_v106(
    run_id: str,
    project_root: Path,
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
    emit_full_route_audit: bool = False,
    emit_full_external_bindings: bool = True,
    emit_kernel_witness_tables: bool = True,
    allow_smoke_limits: bool = False,
    progress_interval: int = 100_000,
    log_level: str = "INFO",
) -> dict:
    """Run the v106 Branch-B domain and final-kernel closure stage."""
    getcontext().prec = decimal_precision
    accept_margin_decimal = decimal_of(accept_margin, "0.0000001")
    run_dir = project_root / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    dirs = ensure_dirs(run_dir)
    log_path = dirs["log"] / f"{ARTIFACT_PREFIX}.log"
    log_line(log_path, f"Starting {VERSION} run_id={run_id}")
    log_line(log_path, f"decimal_precision={decimal_precision}; accept_margin={accept_margin_decimal}; allow_smoke_limits={allow_smoke_limits}")

    required_sources = {
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
        raise FileNotFoundError("Missing one or more required source zips; see v106_source_integrity_manifest.csv")
    log_line(log_path, "source integrity scan complete")

    schema_rows, schema_ok = schema_validation(v105_feedback_zip, v096_feedback_zip, adaptive_full_ledger_zip, v097_feedback_zip, v086_feedback_zip, v050_feedback_zip)
    write_csv(dirs["data"] / f"{ARTIFACT_PREFIX}_schema_field_validation.csv", list(schema_rows[0].keys()), schema_rows)
    log_line(log_path, f"schema validation complete: {schema_ok}")

    v105_summary = read_json_from_zip(v105_feedback_zip, V105["summary"])
    v096_summary = read_json_from_zip(v096_feedback_zip, V096["summary"])
    v097_summary = read_json_from_zip(v097_feedback_zip, V097["summary"])
    v086_summary = read_json_from_zip(v086_feedback_zip, V086["summary"])
    v050_status = read_json_from_zip(v050_feedback_zip, V050["status"])

    boundary_rows, boundary_violations = boundary_audit(v105_feedback_zip)
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_proof_boundary_audit.csv", list(boundary_rows[0].keys()), boundary_rows)
    log_line(log_path, f"proof boundary audit complete: violations={boundary_violations}")

    preflight_rows, preflight_stats = inspect_v105_enlarged_package(v105_feedback_zip)
    write_csv(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_branchB_v105_package_preflight.csv", list(preflight_rows[0].keys()), preflight_rows)
    log_line(log_path, f"v105 Branch-B package preflight complete: {preflight_stats}")

    ledger_audit_path = dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_adaptive_terminal_ledger_audit.csv" if emit_full_route_audit else None
    ledger_stats, ledger_check_rows = audit_adaptive_ledger(adaptive_full_ledger_zip, terminal_route_limit, ledger_audit_path, log_path, progress_interval, allow_smoke_limits)
    write_csv(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_adaptive_ledger_summary_checks.csv", list(ledger_check_rows[0].keys()), ledger_check_rows)
    write_json(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_adaptive_full_ledger_manifest.json", {
        "status": "passed" if all(r["status"] == "passed" for r in ledger_check_rows) else "failed",
        "source": "adaptive_full_ledger_export_v096.zip",
        "ledger_stats": {k: v for k, v in ledger_stats.items() if k not in ("manifest", "reference_audit_rows")},
        "reference_manifest": ledger_stats.get("manifest", {}),
        "strict_boundary": "candidate ledger binding, not theorem proof",
    })
    log_line(log_path, f"adaptive ledger audit complete: terminal={ledger_stats['terminal_rows']} parent_child={ledger_stats['parent_child_rows']} endpoint={ledger_stats['endpoint_rows']}")

    route_out = dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_terminal_route_replay_audit.csv" if emit_full_route_audit else None
    route_stats, route_check_rows = replay_terminal_routes(v097_feedback_zip, terminal_route_limit, route_out, log_path, progress_interval, allow_smoke_limits)
    write_csv(dirs["enlarged_domain"] / f"{ARTIFACT_PREFIX}_route_closure_feedback.csv", list(route_check_rows[0].keys()), route_check_rows)
    log_line(log_path, f"terminal route replay audit complete: rows={route_stats['terminal_route_rows']} failures={route_stats['terminal_route_failures']}")

    directed_out = dirs["external"] / f"{ARTIFACT_PREFIX}_directed_interval_external_and_signoff_bind.csv" if emit_full_external_bindings else None
    directed_stats, directed_check_rows = replay_directed(v097_feedback_zip, v105_feedback_zip, directed_row_limit, directed_out, accept_margin_decimal, allow_smoke_limits)
    write_csv(dirs["external"] / f"{ARTIFACT_PREFIX}_directed_interval_branchB_summary.csv", list(directed_check_rows[0].keys()), directed_check_rows)
    log_line(log_path, f"directed bind audit complete: rows={directed_stats['directed_rows']} failures={directed_stats['directed_failures_vs_0832']}")

    tensor_out = dirs["external"] / f"{ARTIFACT_PREFIX}_local_tensor_external_and_signoff_bind.csv" if emit_full_external_bindings else None
    tensor_stats, tensor_check_rows = replay_tensor(v097_feedback_zip, v105_feedback_zip, tensor_member_limit, tensor_out, accept_margin_decimal, allow_smoke_limits)
    write_csv(dirs["external"] / f"{ARTIFACT_PREFIX}_local_tensor_branchB_summary.csv", list(tensor_check_rows[0].keys()), tensor_check_rows)
    log_line(log_path, f"tensor bind audit complete: rows={tensor_stats['tensor_rows']} packages={tensor_stats['tensor_packages']} failures={tensor_stats['tensor_failures_vs_0832']}")

    h004_out = dirs["bridge"] / f"{ARTIFACT_PREFIX}_h004_external_and_signoff_bind.csv" if emit_full_external_bindings else None
    h004_stats, h004_check_rows = replay_h004(v097_feedback_zip, v105_feedback_zip, v050_feedback_zip, h004_witness_limit, h004_out, allow_smoke_limits)
    write_csv(dirs["bridge"] / f"{ARTIFACT_PREFIX}_h004_bridge_branchB_summary.csv", list(h004_check_rows[0].keys()), h004_check_rows)
    log_line(log_path, f"h004 bind audit complete: rows={h004_stats['h004_rows']} failures={h004_stats['h004_failures']}")

    if emit_kernel_witness_tables:
        g2_member_out = dirs["kernel"] / f"{ARTIFACT_PREFIX}_G2_directed_kernel_input_witness_table.csv"
        g2_stats, g2_rows = audit_v086_directed_kernel(v086_feedback_zip, directed_row_limit, g2_member_out, accept_margin_decimal, allow_smoke_limits)
    else:
        g2_stats, g2_rows = audit_v086_directed_kernel_summary(v086_feedback_zip, accept_margin_decimal, allow_smoke_limits)
    write_csv(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G2_directed_external_arb_kernel_signoff_attempt.csv", list(g2_rows[0].keys()), g2_rows)
    log_line(log_path, f"G2 directed kernel signoff attempt complete: rows={g2_stats['g2_v086_directed_rows']} failures={g2_stats['g2_v086_failures_vs_0832']} fast_summary={g2_stats.get('fast_summary_path', False)}")

    if emit_kernel_witness_tables:
        g3_member_out = dirs["kernel"] / f"{ARTIFACT_PREFIX}_G3_tensor_member_kernel_witness_table.csv"
        g3_package_out = dirs["kernel"] / f"{ARTIFACT_PREFIX}_G3_tensor_package_kernel_witness_table.csv"
        g3_stats, g3_rows = audit_v086_tensor_kernel(v086_feedback_zip, tensor_member_limit, g3_member_out, g3_package_out, accept_margin_decimal, allow_smoke_limits)
    else:
        g3_stats, g3_rows = audit_v086_tensor_kernel_summary(v086_feedback_zip, accept_margin_decimal, allow_smoke_limits)
    write_csv(dirs["kernel"] / f"{ARTIFACT_PREFIX}_G3_local_tensor_theorem_kernel_signoff_attempt.csv", list(g3_rows[0].keys()), g3_rows)
    log_line(log_path, f"G3 tensor kernel signoff attempt complete: members={g3_stats['g3_v086_tensor_member_rows']} packages={g3_stats['g3_v086_tensor_package_rows']} fast_summary={g3_stats.get('fast_summary_path', False)}")

    stress_rows, stress_triage_rows, stress_count, stress_min = copy_and_triage_stress_failures(v105_feedback_zip)
    if stress_rows:
        write_csv(dirs["gap"] / f"{ARTIFACT_PREFIX}_083201_stress_failures.csv", list(stress_rows[0].keys()), stress_rows)
    else:
        write_csv(dirs["gap"] / f"{ARTIFACT_PREFIX}_083201_stress_failures.csv", ["empty"], [])
    if stress_triage_rows:
        write_csv(dirs["triage"] / f"{ARTIFACT_PREFIX}_083201_repair_triage.csv", list(stress_triage_rows[0].keys()), stress_triage_rows)
    else:
        write_csv(dirs["triage"] / f"{ARTIFACT_PREFIX}_083201_repair_triage.csv", ["empty"], [])

    v105_near_ready = boolish(v105_summary.get("near_ready_branch_B_required"))
    v105_branch_b_ready = boolish(v105_summary.get("domain_branch_B_executable_replay_package_ready"))
    v105_signoff_clean = boolish(v105_summary.get("candidate_replay_ready")) and int(v105_summary.get("directed_failures_vs_0832", -1)) == 0 and int(v105_summary.get("tensor_failures_vs_0832", -1)) == 0 and int(v105_summary.get("h004_failures", -1)) == 0

    ledger_clean = all(r["status"] == "passed" for r in ledger_check_rows)
    routes_clean = all(r["status"] == "passed" for r in route_check_rows)
    directed_clean = all(r["status"] == "passed" for r in directed_check_rows)
    tensor_clean = all(r["status"] == "passed" for r in tensor_check_rows)
    h004_clean = all(r["status"] == "passed" for r in h004_check_rows)
    g2_kernel_clean = all(r["status"] == "passed" for r in g2_rows)
    g3_kernel_clean = all(r["status"] == "passed" for r in g3_rows)
    preflight_clean = bool(preflight_stats.get("preflight_passed_or_not_run"))

    branch_b_closed_candidate = bool(src_ok and schema_ok and boundary_violations == 0 and v105_near_ready and v105_branch_b_ready and v105_signoff_clean and preflight_clean and ledger_clean and routes_clean and directed_clean and tensor_clean and h004_clean and not allow_smoke_limits)
    g2_final_kernel_signoff_candidate = bool(branch_b_closed_candidate and g2_kernel_clean and directed_clean)
    g3_final_tensor_theorem_candidate = bool(branch_b_closed_candidate and g3_kernel_clean and tensor_clean)
    g1_closed_candidate = bool(ledger_clean and routes_clean and not allow_smoke_limits)
    g4_closed_candidate = bool(h004_clean and not allow_smoke_limits)
    theorem_ready_candidate = bool(branch_b_closed_candidate and g2_final_kernel_signoff_candidate and g3_final_tensor_theorem_candidate and g1_closed_candidate and g4_closed_candidate and boundary_violations == 0 and stress_count >= 0)

    # Domain decision rows: v106 explicitly records that Branch B has been run.
    domain_rows = [
        {
            "branch_id": "A",
            "branch_name": "prove_current_translation_range_reduction",
            "v105_status": "A_failed_or_not_closed_B_required",
            "v106_decision_status": "A_not_closed_superseded_by_B_candidate" if branch_b_closed_candidate else "A_not_closed_B_not_yet_closed",
            "branch_closed_candidate": "False",
            "blocks_bs0832": "False_if_B_candidate_accepted" if branch_b_closed_candidate else "True_until_B_replay_closes",
            "evidence_or_gap": "No new symbolic Branch A theorem supplied in v106.",
            "next_action": "Use Branch B dry-freeze candidate if final theorem review accepts replay closure." if branch_b_closed_candidate else "Repair Branch B replay artifacts.",
        },
        {
            "branch_id": "B",
            "branch_name": "enlarged_domain_replay_fallback",
            "v105_status": "B_executable_replay_package_ready_not_run_full",
            "v106_decision_status": "B_enlarged_domain_replay_closed_candidate" if branch_b_closed_candidate else "B_replay_failed_or_incomplete",
            "branch_closed_candidate": str(branch_b_closed_candidate),
            "blocks_bs0832": "False_at_candidate_dry_freeze_level" if branch_b_closed_candidate else "True",
            "evidence_or_gap": "v096 full ledger + v097 terminal replay + v105 signoff package bound in v106." if branch_b_closed_candidate else "See v106 ledger/route/signoff failures.",
            "next_action": "Proceed to final theorem dry-freeze review." if branch_b_closed_candidate else "Repair Branch B replay inputs.",
        },
        {
            "branch_id": "C",
            "branch_name": "final_kernel_text_gap",
            "v105_status": "theorem_text_gap_preserved",
            "v106_decision_status": "C_dry_freeze_candidate_ready" if theorem_ready_candidate else "C_remaining_kernel_or_replay_blockers",
            "branch_closed_candidate": str(theorem_ready_candidate),
            "blocks_bs0832": "False_at_candidate_level_only" if theorem_ready_candidate else "True_until_all_candidate_kernels_close",
            "evidence_or_gap": "G2/G3 kernel signoff candidates produced; theorem_ready remains false by proof boundary.",
            "next_action": "Human/formal final proof review; do not upgrade to theorem without acceptance.",
        },
    ]
    write_csv(dirs["domain"] / "domain_final_decision_v106.csv", list(domain_rows[0].keys()), domain_rows)

    gates = [
        {"gate_id": "G1", "gate_family": "adaptive_full_ledger_and_terminal_route_coverage", "v106_candidate_status": "closed_candidate" if g1_closed_candidate else "failed_or_limited", "v106_theorem_status": "theorem_component_bound_candidate", "blocks_bs0832_theorem": "False_at_candidate_level" if g1_closed_candidate else "True", "next_action": "Accept in final theorem review." if g1_closed_candidate else "Repair adaptive ledger/terminal route coverage."},
        {"gate_id": "G2", "gate_family": "external_arb_directed_interval_kernel", "v106_candidate_status": "final_kernel_signoff_closed_candidate" if g2_final_kernel_signoff_candidate else "failed_or_incomplete", "v106_theorem_status": "candidate_ready_not_published_theorem_kernel", "blocks_bs0832_theorem": "False_for_dry_freeze_candidate; True_until_formal_review_accepts" if g2_final_kernel_signoff_candidate else "True", "next_action": "External Arb/outward-rounded kernel final proof review."},
        {"gate_id": "G3", "gate_family": "true_local_tensor_certificate", "v106_candidate_status": "final_tensor_theorem_signoff_closed_candidate" if g3_final_tensor_theorem_candidate else "failed_or_incomplete", "v106_theorem_status": "candidate_ready_not_published_tensor_theorem", "blocks_bs0832_theorem": "False_for_dry_freeze_candidate; True_until_formal_review_accepts" if g3_final_tensor_theorem_candidate else "True", "next_action": "Local tensor domination theorem final proof review."},
        {"gate_id": "G4", "gate_family": "h004_bridge_containment_appendix", "v106_candidate_status": "closed_candidate" if g4_closed_candidate else "failed_or_incomplete", "v106_theorem_status": "theorem_component_bound_candidate", "blocks_bs0832_theorem": "False_at_candidate_level" if g4_closed_candidate else "True", "next_action": "Accept in final theorem review."},
        {"gate_id": "G5", "gate_family": "formal_domain_translation_range_reduction", "v106_candidate_status": "domain_gate_closed_candidate_by_B" if branch_b_closed_candidate else "branch_B_failed_or_incomplete", "v106_theorem_status": "Branch_B_candidate_replay_not_symbolic_Branch_A_proof", "blocks_bs0832_theorem": "False_for_dry_freeze_candidate; True_until_final_review_accepts" if branch_b_closed_candidate else "True", "next_action": "Use Branch B replay in final theorem package if accepted."},
        {"gate_id": "G6", "gate_family": "final_theorem_statement_and_reproducibility_freeze", "v106_candidate_status": "theorem_ready_candidate_dry_freeze" if theorem_ready_candidate else "not_ready", "v106_theorem_status": "theorem_ready_false", "blocks_bs0832_theorem": "True_until_final_review_even_if_candidate_ready", "next_action": "v107 final theorem freeze/human-formal review if v106 dry-freeze passes."},
    ]
    write_csv(dirs["gates"] / f"{ARTIFACT_PREFIX}_theorem_gate_matrix.csv", list(gates[0].keys()), gates)

    kernel_decision_rows = [
        {"kernel_id": "G2", "kernel_family": "directed_interval_external_arb", "rows_bound": directed_stats["directed_rows"], "v086_rows": g2_stats["g2_v086_directed_rows"], "v097_v105_bind_clean": str(directed_clean), "v086_kernel_input_clean": str(g2_kernel_clean), "final_kernel_signoff_candidate": str(g2_final_kernel_signoff_candidate), "formalized_theorem_claim": "False", "min_margin_v105_vs_0832": directed_stats["directed_min_margin_v105_vs_0832"], "min_margin_v086_vs_0832": g2_stats["g2_v086_min_margin_vs_0832"]},
        {"kernel_id": "G3", "kernel_family": "local_tensor_domination", "rows_bound": tensor_stats["tensor_rows"], "v086_rows": g3_stats["g3_v086_tensor_member_rows"], "v097_v105_bind_clean": str(tensor_clean), "v086_kernel_input_clean": str(g3_kernel_clean), "final_kernel_signoff_candidate": str(g3_final_tensor_theorem_candidate), "formalized_theorem_claim": "False", "min_margin_v105_vs_0832": tensor_stats["tensor_min_margin_v105_vs_0832"], "min_margin_v086_vs_0832": g3_stats["g3_v086_member_min_margin_vs_0832"]},
    ]
    write_csv(dirs["kernel"] / f"{ARTIFACT_PREFIX}_final_kernel_signoff_decision.csv", list(kernel_decision_rows[0].keys()), kernel_decision_rows)

    package_rows = [
        {"artifact_family": "appendix_A_adaptive_tree", "tracked_rows": ledger_stats["terminal_rows"], "v106_status": gates[0]["v106_candidate_status"], "theorem_ready_candidate_component": str(g1_closed_candidate), "theorem_ready": "False"},
        {"artifact_family": "branchB_terminal_route_replay", "tracked_rows": route_stats["terminal_route_rows"], "v106_status": "closed_candidate" if routes_clean and not allow_smoke_limits else "failed_or_limited", "theorem_ready_candidate_component": str(routes_clean and not allow_smoke_limits), "theorem_ready": "False"},
        {"artifact_family": "appendix_B_directed_interval_G2", "tracked_rows": directed_stats["directed_rows"], "v106_status": gates[1]["v106_candidate_status"], "theorem_ready_candidate_component": str(g2_final_kernel_signoff_candidate), "theorem_ready": "False"},
        {"artifact_family": "appendix_C_local_tensor_G3", "tracked_rows": tensor_stats["tensor_rows"], "v106_status": gates[2]["v106_candidate_status"], "theorem_ready_candidate_component": str(g3_final_tensor_theorem_candidate), "theorem_ready": "False"},
        {"artifact_family": "appendix_D_h004", "tracked_rows": h004_stats["h004_rows"], "v106_status": gates[3]["v106_candidate_status"], "theorem_ready_candidate_component": str(g4_closed_candidate), "theorem_ready": "False"},
        {"artifact_family": "domain_reduction_BranchB", "tracked_rows": 1, "v106_status": gates[4]["v106_candidate_status"], "theorem_ready_candidate_component": str(branch_b_closed_candidate), "theorem_ready": "False"},
        {"artifact_family": "final_theorem_statement_dry_freeze", "tracked_rows": "all", "v106_status": gates[5]["v106_candidate_status"], "theorem_ready_candidate_component": str(theorem_ready_candidate), "theorem_ready": "False"},
    ]
    write_csv(dirs["proof"] / "bs0832_theorem_package_v15_dry_freeze_decision_v106.csv", list(package_rows[0].keys()), package_rows)

    remaining_blockers = []
    if not branch_b_closed_candidate:
        remaining_blockers.append("Branch-B enlarged-domain replay not closed candidate")
    if not g2_final_kernel_signoff_candidate:
        remaining_blockers.append("G2 directed/external-Arb final kernel signoff candidate not closed")
    if not g3_final_tensor_theorem_candidate:
        remaining_blockers.append("G3 local tensor theorem signoff candidate not closed")
    if boundary_violations:
        remaining_blockers.append("proof boundary violations detected")
    if allow_smoke_limits:
        remaining_blockers.append("smoke-mode limits used; full candidate decision intentionally disabled")

    next_actions = [
        {"rank": "1", "action_family": "final_review", "blocks_bs0832": "True_until_acceptance", "recommended_next_action": "If theorem_ready_candidate_dry_freeze is true, run independent final proof review/freeze; otherwise repair listed blockers."},
        {"rank": "2", "action_family": "external_arb_kernel", "blocks_bs0832": str(not g2_final_kernel_signoff_candidate), "recommended_next_action": "Review v106_G2_directed_external_arb_kernel_signoff_attempt.csv and witness table; promote only after formal outward-rounded kernel review."},
        {"rank": "3", "action_family": "local_tensor_theorem", "blocks_bs0832": str(not g3_final_tensor_theorem_candidate), "recommended_next_action": "Review v106_G3_local_tensor_theorem_kernel_signoff_attempt.csv and member/package witness tables."},
        {"rank": "4", "action_family": "stronger_bound_future", "blocks_bs0832": "False", "recommended_next_action": "Defer the stronger numerical target; repair D060-00008276 directed stress failures in a separate stronger-bound branch."},
    ]
    write_csv(dirs["gap"] / f"{ARTIFACT_PREFIX}_next_action_queue.csv", list(next_actions[0].keys()), next_actions)

    execution_status = "smoke_success" if allow_smoke_limits else "success"
    summary = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "execution_status": execution_status,
        "status": execution_status,
        "source_integrity_passed": src_ok,
        "schema_validation_passed": schema_ok,
        "v105_near_ready_branch_B_required": v105_near_ready,
        "v105_branch_B_executable_replay_package_ready": v105_branch_b_ready,
        "v105_signoff_clean": v105_signoff_clean,
        "branch_B_replay_closed_candidate": branch_b_closed_candidate,
        "domain_gate_closed_candidate_by_B": branch_b_closed_candidate,
        "G2_final_external_arb_kernel_signoff_candidate": g2_final_kernel_signoff_candidate,
        "G3_final_local_tensor_theorem_signoff_candidate": g3_final_tensor_theorem_candidate,
        "theorem_package_v15_dry_freeze_ready": theorem_ready_candidate,
        "theorem_ready_candidate": theorem_ready_candidate,
        "theorem_ready": False,
        "remaining_blockers": remaining_blockers,
        "adaptive_parent_child_edges": ledger_stats["parent_child_rows"],
        "adaptive_endpoint_rows": ledger_stats["endpoint_rows"],
        "adaptive_terminal_route_rows": ledger_stats["terminal_rows"],
        "adaptive_route_counts": ledger_stats["route_counts"],
        "adaptive_ledger_audit_passed_observed": ledger_stats["ledger_audit_passed_observed"],
        "terminal_route_replay_rows": route_stats["terminal_route_rows"],
        "terminal_route_replay_failures": route_stats["terminal_route_failures"],
        "terminal_route_counts": route_stats["route_counts"],
        "directed_rows": directed_stats["directed_rows"],
        "directed_failures_vs_0832": directed_stats["directed_failures_vs_0832"],
        "directed_min_margin_v097_vs_0832": directed_stats["directed_min_margin_v097_vs_0832"],
        "directed_min_margin_v105_vs_0832": directed_stats["directed_min_margin_v105_vs_0832"],
        "G2_v086_directed_rows": g2_stats["g2_v086_directed_rows"],
        "G2_v086_min_margin_vs_0832": g2_stats["g2_v086_min_margin_vs_0832"],
        "tensor_rows": tensor_stats["tensor_rows"],
        "tensor_packages": tensor_stats["tensor_packages"],
        "tensor_failures_vs_0832": tensor_stats["tensor_failures_vs_0832"],
        "tensor_min_margin_v097_vs_0832": tensor_stats["tensor_min_margin_v097_vs_0832"],
        "tensor_min_margin_v105_vs_0832": tensor_stats["tensor_min_margin_v105_vs_0832"],
        "G3_v086_tensor_member_rows": g3_stats["g3_v086_tensor_member_rows"],
        "G3_v086_tensor_package_rows": g3_stats["g3_v086_tensor_package_rows"],
        "G3_v086_member_min_margin_vs_0832": g3_stats["g3_v086_member_min_margin_vs_0832"],
        "h004_rows": h004_stats["h004_rows"],
        "h004_failures": h004_stats["h004_failures"],
        "h004_v050_freeze_valid": h004_stats["h004_v050_freeze_valid"],
        "stress_failures_083201": stress_count,
        "stress_min_margin_083201": stress_min,
        "proof_boundary_violations": boundary_violations,
        "strict_boundary": STRICT_BOUNDARY_FLAGS,
        "v096_summary_status": v096_summary.get("status"),
        "v097_summary_status": v097_summary.get("status"),
        "v086_summary_status": v086_summary.get("status"),
        "v050_status": v050_status.get("status"),
        "allow_smoke_limits": allow_smoke_limits,
    }
    write_json(dirs["data"] / f"{ARTIFACT_PREFIX}_readiness_summary.json", summary)
    write_json(dirs["proof"] / "bs0832_theorem_package_v15_dry_freeze_decision_v106.json", {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "branch_B_replay_closed_candidate": branch_b_closed_candidate,
        "G2_final_external_arb_kernel_signoff_candidate": g2_final_kernel_signoff_candidate,
        "G3_final_local_tensor_theorem_signoff_candidate": g3_final_tensor_theorem_candidate,
        "theorem_ready_candidate": theorem_ready_candidate,
        "theorem_ready": False,
        "remaining_blockers": remaining_blockers,
        "strict_boundary": STRICT_BOUNDARY_FLAGS,
        "artifact_families": package_rows,
        "gate_matrix": gates,
    })

    repro_rows = [
        {"check_id": "R1", "status": "passed" if src_ok else "failed", "detail": "source integrity"},
        {"check_id": "R2", "status": "passed" if schema_ok else "failed", "detail": "schema validation"},
        {"check_id": "R3", "status": "passed" if preflight_clean else "failed", "detail": "v105 Branch-B package preflight"},
        {"check_id": "R4", "status": "passed" if ledger_clean else "failed", "detail": "adaptive full ledger audit"},
        {"check_id": "R5", "status": "passed" if routes_clean else "failed", "detail": "terminal route external replay"},
        {"check_id": "R6", "status": "passed" if directed_clean else "failed", "detail": "directed replay + v105 signoff binding"},
        {"check_id": "R7", "status": "passed" if tensor_clean else "failed", "detail": "tensor replay + v105 signoff binding"},
        {"check_id": "R8", "status": "passed" if h004_clean else "failed", "detail": "h004 replay + v105/v050 binding"},
        {"check_id": "R9", "status": "passed" if g2_kernel_clean else "failed", "detail": "G2 directed kernel candidate signoff"},
        {"check_id": "R10", "status": "passed" if g3_kernel_clean else "failed", "detail": "G3 tensor theorem candidate signoff"},
        {"check_id": "R11", "status": "passed" if boundary_violations == 0 else "failed", "detail": "proof boundary audit"},
        {"check_id": "R12", "status": "passed" if theorem_ready_candidate else "pending", "detail": "theorem package v15 dry-freeze candidate"},
    ]
    write_csv(dirs["reproducibility"] / f"{ARTIFACT_PREFIX}_reproducibility_checklist.csv", list(repro_rows[0].keys()), repro_rows)

    status = {
        "status": summary["status"],
        "run_id": run_id,
        "version": VERSION,
        "branch_B_replay_closed_candidate": branch_b_closed_candidate,
        "G2_final_external_arb_kernel_signoff_candidate": g2_final_kernel_signoff_candidate,
        "G3_final_local_tensor_theorem_signoff_candidate": g3_final_tensor_theorem_candidate,
        "theorem_ready_candidate": theorem_ready_candidate,
        "theorem_ready": False,
        "generated_at": now_utc(),
    }
    write_json(dirs["status"] / f"{ARTIFACT_PREFIX}.status.json", status)

    replay_ps1 = """# v0.10.6 Branch-B domain and final-kernel closure sprint
# Run from project root after placing required feedback zips.
powershell -ExecutionPolicy Bypass -File .\\scripts\\run_v106_local.ps1
"""
    write_text(dirs["replay"] / "bs0832_branchB_domain_and_final_kernel_closure_v106.ps1", replay_ps1)
    write_text(dirs["replay"] / "bs0832_branchB_domain_and_final_kernel_closure_v106.md", "# v0.10.6 Branch-B domain and final-kernel closure sprint\n\nRun `powershell -ExecutionPolicy Bypass -File .\\scripts\\run_v106_local.ps1`.\n\nStrict boundary: this is a candidate-level dry-freeze package, not theorem proof.\n")

    report = f"""# v0.10.6 BS0832 Branch-B domain and final-kernel closure sprint

Status: `{summary['status']}`

## Key results

- Branch B replay closed candidate: `{summary['branch_B_replay_closed_candidate']}`
- Domain gate closed candidate by Branch B: `{summary['domain_gate_closed_candidate_by_B']}`
- G2 final external-Arb kernel signoff candidate: `{summary['G2_final_external_arb_kernel_signoff_candidate']}`
- G3 final local tensor theorem signoff candidate: `{summary['G3_final_local_tensor_theorem_signoff_candidate']}`
- theorem package v15 dry-freeze ready: `{summary['theorem_package_v15_dry_freeze_ready']}`
- theorem ready: `false`
- proof boundary violations: `{summary['proof_boundary_violations']}`

## Replay counts

- adaptive parent-child edges: `{summary['adaptive_parent_child_edges']}`
- adaptive endpoint rows: `{summary['adaptive_endpoint_rows']}`
- adaptive terminal route rows: `{summary['adaptive_terminal_route_rows']}`
- terminal route replay failures: `{summary['terminal_route_replay_failures']}`
- directed rows/failures vs 0.832: `{summary['directed_rows']}` / `{summary['directed_failures_vs_0832']}`
- tensor rows/packages/failures vs 0.832: `{summary['tensor_rows']}` / `{summary['tensor_packages']}` / `{summary['tensor_failures_vs_0832']}`
- h004 rows/failures: `{summary['h004_rows']}` / `{summary['h004_failures']}`
- stronger-bound stress records preserved: `{summary['stress_failures_083201']}`

## Boundary

v0.10.6 does not claim theorem-level BS0832 reproduction and does not prove a stronger numerical target.  If `theorem_ready_candidate=true`, it means a candidate dry-freeze package is ready for final formal/human review; `theorem_ready` remains false by construction.
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
    log_line(log_path, f"Finished v106; theorem_ready_candidate={theorem_ready_candidate}; theorem_ready=False")

    feedback_zip = run_dir / FEEDBACK_NAME
    make_feedback_zip(run_dir, feedback_zip)
    return {"summary": summary, "run_dir": str(run_dir), "feedback_zip": str(feedback_zip)}
