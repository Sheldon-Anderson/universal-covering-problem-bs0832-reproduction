"""v0.10.8 BS0832 theorem-level reproduction closure attempt and final signoff package.

This step consumes the v0.10.7 final theorem release-candidate review bundle and
makes the largest proof-boundary-safe move toward completing the reproduction of
Brass-Sharifi's 0.832 lower bound:

1. Validate the v107 release-candidate bundle and source-hash binding.
2. Convert the artifact/review bundle into a proof-manuscript candidate.
3. Emit a lemma registry, claim-dependency DAG, and artifact-to-lemma binding ledger.
4. Run a red-team proof-text audit that prevents stronger numerical or theorem-ready claims
   from leaking into the manuscript.
5. Emit a final reproduction-closure candidate decision.

Strict boundary: this step may set bs0832_reproduction_complete_candidate=true
and theorem_claim_ready_for_final_human_review=true, but it intentionally keeps
bs0832_reproduced_theorem_level=false and theorem_ready=false.  It is a final
candidate/signoff package, not an automatic theorem proof.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from app.domain.adaptive_global_v106 import (
    STRICT_BOUNDARY_FLAGS,
    REFERENCE_COUNTS,
    now_utc,
    ensure_parent,
    write_csv,
    write_json,
    write_text,
    log_line,
    sha256_file,
    read_json_from_zip,
    iter_csv_from_zip,
    csv_header_from_zip,
    zip_has,
    make_feedback_zip,
)
from app.domain.adaptive_global_v107 import release_text

# Stage identity written into v108 reproduction-closure metadata.
VERSION = "v0.10.8-bs0832-theorem-level-reproduction-closure-attempt-and-final-signoff-package"
SCHEMA_VERSION = "v108-theorem-level-reproduction-closure-attempt-v1"
STEP_NAME = "86_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package"
ARTIFACT_PREFIX = "v108"
FEEDBACK_NAME = "feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip"

# ZIP-member map for the v107 release-candidate archive consumed by v108.
V107 = {
    "summary": "data/v107_readiness_summary.json",
    "status": "status/v107.status.json",
    "release_manifest": "release/BS0832_THEOREM_RELEASE_CANDIDATE_MANIFEST.json",
    "freeze_json": "proof/bs0832_theorem_package_v16_final_freeze_decision_v107.json",
    "freeze_csv": "proof/bs0832_theorem_package_v16_final_freeze_decision_v107.csv",
    "gates": "gates/v107_theorem_gate_matrix.csv",
    "proof_boundary": "audit/v107_proof_boundary_audit.csv",
    "artifact_index": "release/BS0832_ARTIFACT_INDEX.csv",
    "repro": "reproducibility/v107_reproducibility_checklist.csv",
    "hash_summary": "audit/v107_full_hash_audit_summary.json",
    "route_hash": "audit/v107_full_route_hash_audit.csv",
    "directed_hash": "audit/v107_directed_kernel_hash_audit.csv",
    "tensor_hash": "audit/v107_tensor_kernel_hash_audit.csv",
    "h004_hash": "audit/v107_h004_hash_audit.csv",
    "g2_review": "kernel/v107_G2_external_arb_final_review.csv",
    "g3_review": "kernel/v107_G3_local_tensor_final_review.csv",
    "domain_review": "domain/v107_BranchB_domain_final_acceptance.csv",
    "stress": "gap/v107_083201_stress_failures.csv",
    "repair_queue": "triage/v107_083201_v011_repair_launch_queue.csv",
    "appendix_a": "appendix/Appendix_A_adaptive_tree_final_checklist.md",
    "appendix_b": "appendix/Appendix_B_directed_kernel_final_checklist.md",
    "appendix_c": "appendix/Appendix_C_tensor_theorem_final_checklist.md",
    "appendix_d": "appendix/Appendix_D_h004_final_checklist.md",
    "appendix_e": "appendix/Appendix_E_domain_BranchB_final_checklist.md",
}

# Optional source paths are hashed for traceability when present.
OPTIONAL_SOURCE_ROLES = {
    "v106_feedback_zip": "feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip",
    "v105_feedback_zip": "feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip",
    "v096_feedback_zip": "feedback_v096_adaptive_full_ledger_rerun_executor.zip",
    "adaptive_full_ledger_zip": "adaptive_full_ledger_export_v096.zip",
    "v097_feedback_zip": "feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip",
    "v086_feedback_zip": "feedback_v086_true_arb_and_local_tensor_port_v1.zip",
    "v050_feedback_zip": "feedback_v050_h004_local_proof_freeze_main.zip",
}


def ensure_dirs(run_dir: Path) -> Dict[str, Path]:
    """Create the stage output directory tree and return named paths."""
    names = [
        "data", "status", "manifest", "log", "audit", "review", "proof", "release",
        "manuscript", "reproducibility", "report", "triage", "gates", "appendix",
    ]
    dirs: Dict[str, Path] = {}
    for name in names:
        dirs[name] = run_dir / name
        dirs[name].mkdir(parents=True, exist_ok=True)
    return dirs


def boolish(value) -> bool:
    """Interpret common boolean-like status values used in certificate tables."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "passed", "success"}


def _read_csv_rows_from_zip(zip_path: Path, member: str, limit: int = 0) -> List[dict]:
    """Read CSV rows from a ZIP member into memory for small ledgers."""
    rows: List[dict] = []
    for idx, row in enumerate(iter_csv_from_zip(zip_path, member, limit=limit)):
        rows.append(row)
    return rows


def validate_v107_schema(v107_zip: Path) -> Tuple[List[dict], bool]:
    """Validate the v107 release-candidate schema before v108 aggregation."""
    specs = [
        ("json", "v107_summary", V107["summary"], [
            "status", "fresh_independent_replay_passed", "full_hash_audit_passed",
            "bs0832_release_candidate_ready", "theorem_release_candidate", "theorem_ready",
            "target_083201_proved", "proof_boundary_violations", "stress_failures_083201",
        ]),
        ("json", "v107_status", V107["status"], [
            "status", "fresh_independent_replay_passed", "full_hash_audit_passed",
            "bs0832_release_candidate_ready", "theorem_release_candidate", "theorem_ready",
            "target_083201_proved",
        ]),
        ("json", "v107_release_manifest", V107["release_manifest"], [
            "version", "schema_version", "run_id", "bs0832_release_candidate_ready",
            "theorem_release_candidate", "theorem_ready", "proof_boundary", "source_hashes", "key_counts",
        ]),
        ("json", "v107_freeze_json", V107["freeze_json"], [
            "fresh_independent_replay_passed", "full_hash_audit_passed",
            "G1_final_review_accepted_candidate", "G2_final_review_accepted_candidate",
            "G3_final_review_accepted_candidate", "G4_final_review_accepted_candidate",
            "G5_BranchB_domain_final_acceptance_candidate", "theorem_package_v16_final_freeze_candidate",
            "theorem_ready", "strict_boundary", "remaining_blockers",
        ]),
        ("csv", "v107_gate_matrix", V107["gates"], [
            "gate_id", "gate_family", "v107_final_review_status", "blocks_release_candidate", "theorem_boundary_status",
        ]),
        ("csv", "v107_reproducibility", V107["repro"], ["check_id", "status", "detail"]),
        ("csv", "v107_artifact_index", V107["artifact_index"], ["artifact_family", "path", "purpose"]),
        ("csv", "v107_proof_boundary", V107["proof_boundary"], ["boundary_flag", "observed_value", "expected_value", "status"]),
        ("json", "v107_hash_summary", V107["hash_summary"], [
            "adaptive_terminal_ledger", "v097_terminal_routes", "v086_directed_kernel",
            "v097_directed_external_replay", "v086_tensor_members", "v086_tensor_packages",
            "v097_tensor_external_replay", "v097_h004_appendix_replay",
        ]),
    ]
    out: List[dict] = []
    ok = True
    for kind, label, member, req in specs:
        exists = zip_has(v107_zip, member)
        present: List[str] = []
        missing = list(req)
        passed = False
        if exists:
            try:
                if kind == "json":
                    obj = read_json_from_zip(v107_zip, member)
                    present = [k for k in req if k in obj]
                    missing = [k for k in req if k not in obj]
                else:
                    header = csv_header_from_zip(v107_zip, member)
                    present = [k for k in req if k in header]
                    missing = [k for k in req if k not in header]
                passed = not missing
            except Exception as exc:  # pragma: no cover - diagnostic path
                missing = [f"exception:{type(exc).__name__}:{exc}"]
                passed = False
        ok = ok and passed
        out.append({
            "schema_family": label,
            "member": member,
            "exists": str(exists),
            "required_fields": ";".join(req),
            "present_required_fields": ";".join(present),
            "missing_required_fields": ";".join(missing),
            "status": "passed" if passed else "failed",
        })
    return out, ok


def source_integrity_v108(v107_feedback_zip: Path, optional_sources: Dict[str, Optional[Path]], manifest: Optional[dict]) -> Tuple[List[dict], bool, bool]:
    """Record v108 source hashes and optional-source integrity information."""
    rows: List[dict] = []
    source_ok = True
    hash_ok = True
    rows.append({
        "source_role": "v107_feedback_zip",
        "path": str(v107_feedback_zip),
        "required": "True",
        "exists": str(v107_feedback_zip.exists()),
        "sha256": sha256_file(v107_feedback_zip) if v107_feedback_zip.exists() else "",
        "expected_sha256_from_v107_manifest": "",
        "hash_status": "not_applicable",
        "status": "passed" if v107_feedback_zip.exists() else "failed",
    })
    if not v107_feedback_zip.exists():
        source_ok = False
    expected_hashes = {}
    if manifest and isinstance(manifest.get("source_hashes"), dict):
        expected_hashes = manifest["source_hashes"]
    for role, default_name in OPTIONAL_SOURCE_ROLES.items():
        path = optional_sources.get(role)
        exists = bool(path and path.exists())
        actual_hash = sha256_file(path) if exists else ""
        expected = str(expected_hashes.get(role, ""))
        if exists and expected:
            hstatus = "passed" if actual_hash == expected else "failed"
            if hstatus != "passed":
                hash_ok = False
        elif exists and not expected:
            hstatus = "observed_no_manifest_hash"
        else:
            hstatus = "not_provided_optional"
        rows.append({
            "source_role": role,
            "path": str(path) if path else default_name,
            "required": "False",
            "exists": str(exists),
            "sha256": actual_hash,
            "expected_sha256_from_v107_manifest": expected,
            "hash_status": hstatus,
            "status": "passed" if hstatus in {"passed", "observed_no_manifest_hash", "not_provided_optional"} else "failed",
        })
    return rows, source_ok, hash_ok


def audit_v107_release_candidate(v107_zip: Path) -> Tuple[dict, List[dict]]:
    """Audit v107 release-candidate flags and proof-boundary status."""
    summary = read_json_from_zip(v107_zip, V107["summary"])
    status = read_json_from_zip(v107_zip, V107["status"])
    manifest = read_json_from_zip(v107_zip, V107["release_manifest"])
    freeze = read_json_from_zip(v107_zip, V107["freeze_json"])
    gates = _read_csv_rows_from_zip(v107_zip, V107["gates"])
    repro = _read_csv_rows_from_zip(v107_zip, V107["repro"])
    boundary = _read_csv_rows_from_zip(v107_zip, V107["proof_boundary"])

    gate_ok = all(str(r.get("blocks_release_candidate", "")).strip().lower() == "false" for r in gates)
    repro_ok = all(str(r.get("status", "")).strip().lower() == "passed" for r in repro if r.get("check_id") != "R6") and any(r.get("check_id") == "R6" and r.get("status") == "passed" for r in repro)
    boundary_ok = all(str(r.get("status", "")).strip().lower() == "passed" for r in boundary)
    counts_ok = (
        int(summary.get("adaptive_terminal_route_rows", -1)) == REFERENCE_COUNTS["terminal_route_rows"]
        and int(summary.get("terminal_route_replay_rows", -1)) == REFERENCE_COUNTS["terminal_route_rows"]
        and int(summary.get("directed_rows", -1)) == REFERENCE_COUNTS["directed_rows"]
        and int(summary.get("tensor_rows", -1)) == REFERENCE_COUNTS["tensor_members"]
        and int(summary.get("tensor_packages", -1)) == REFERENCE_COUNTS["tensor_packages"]
        and int(summary.get("h004_rows", -1)) == REFERENCE_COUNTS["h004_witnesses"]
    )
    checks = [
        ("V107-1", "status_success", summary.get("status") == "success" and status.get("status") == "success"),
        ("V107-2", "fresh_independent_replay_passed", boolish(summary.get("fresh_independent_replay_passed")) and boolish(status.get("fresh_independent_replay_passed")) and boolish(freeze.get("fresh_independent_replay_passed"))),
        ("V107-3", "full_hash_audit_passed", boolish(summary.get("full_hash_audit_passed")) and boolish(status.get("full_hash_audit_passed")) and boolish(freeze.get("full_hash_audit_passed"))),
        ("V107-4", "release_candidate_ready", boolish(summary.get("bs0832_release_candidate_ready")) and boolish(manifest.get("bs0832_release_candidate_ready")) and boolish(freeze.get("bs0832_release_candidate_ready"))),
        ("V107-5", "theorem_release_candidate_ready", boolish(summary.get("theorem_release_candidate")) and boolish(manifest.get("theorem_release_candidate")) and boolish(freeze.get("theorem_release_candidate"))),
        ("V107-6", "theorem_ready_false", not boolish(summary.get("theorem_ready")) and not boolish(status.get("theorem_ready")) and not boolish(manifest.get("theorem_ready")) and not boolish(freeze.get("theorem_ready"))),
        ("V107-7", "083201_not_proved", not boolish(summary.get("target_083201_proved")) and int(summary.get("stress_failures_083201", -1)) == 8),
        ("V107-8", "proof_boundary_clean", int(summary.get("proof_boundary_violations", -1)) == 0 and boundary_ok),
        ("V107-9", "gate_matrix_unblocked", gate_ok),
        ("V107-10", "reproducibility_passed", repro_ok),
        ("V107-11", "reference_counts_match", counts_ok),
        ("V107-12", "remaining_blockers_empty", list(summary.get("remaining_blockers", [])) == [] and list(freeze.get("remaining_blockers", [])) == []),
    ]
    rows = [{"check_id": cid, "check_family": family, "status": "passed" if ok else "failed", "detail": "v107 release-candidate input audit"} for cid, family, ok in checks]
    stats = {
        "summary": summary,
        "status": status,
        "manifest": manifest,
        "freeze": freeze,
        "gates": gates,
        "repro": repro,
        "boundary": boundary,
        "v107_input_release_candidate_accepted": all(ok for _, _, ok in checks),
        "gate_ok": gate_ok,
        "repro_ok": repro_ok,
        "boundary_ok": boundary_ok,
        "counts_ok": counts_ok,
    }
    return stats, rows


def build_lemma_registry(v107_summary: dict) -> List[dict]:
    """Build the v108 lemma registry from accepted v107 summary counts."""
    route_counts = v107_summary.get("adaptive_route_counts", {}) or {}
    return [
        {
            "lemma_id": "L1",
            "lemma_name": "Adaptive full ledger closure",
            "statement_candidate": f"The adaptive full ledger contains {v107_summary.get('adaptive_parent_child_edges')} parent-child edges, {v107_summary.get('adaptive_endpoint_rows')} endpoint rows, and {v107_summary.get('adaptive_terminal_route_rows')} terminal routes with no duplicate/orphan/unrouted terminal entries in the v107 release candidate.",
            "depends_on": "SRC-v096;SRC-ledger;HASH-route;V107-G1",
            "artifact_inputs": "adaptive_full_ledger_export_v096;feedback_v096;feedback_v107",
            "hash_audit_inputs": "audit/v107_full_route_hash_audit.csv;audit/v107_full_hash_audit_summary.json",
            "route_or_component_count": str(v107_summary.get("adaptive_terminal_route_rows")),
            "status": "complete_candidate" if boolish(v107_summary.get("G1_final_review_accepted_candidate")) else "blocked",
            "proof_boundary_flag": "candidate_component_not_standalone_theorem",
            "remaining_human_review_note": "Verify that the Branch-B adoption of this ledger is acceptable in the final proof text.",
        },
        {
            "lemma_id": "L2",
            "lemma_name": "Terminal route dispatch coverage",
            "statement_candidate": "Every terminal route in the v096/v097 replay is assigned to exactly one accepted route family: directed interval, local tensor, or h004 bridge.",
            "depends_on": "L1;SRC-v097;HASH-route",
            "artifact_inputs": "v097 terminal route replay;v107 terminal route hash audit",
            "hash_audit_inputs": "audit/v107_full_route_hash_audit.csv",
            "route_or_component_count": json.dumps(route_counts, sort_keys=True),
            "status": "complete_candidate" if int(v107_summary.get("terminal_route_replay_failures", 1)) == 0 else "blocked",
            "proof_boundary_flag": "route_dispatch_candidate",
            "remaining_human_review_note": "Check route-family definitions against Appendix A/E text.",
        },
        {
            "lemma_id": "L3",
            "lemma_name": "Directed interval certificate lemma",
            "statement_candidate": f"The directed interval/external-Arb candidate kernel covers {v107_summary.get('directed_rows')} directed rows with zero failures against 0.832 and minimum v105 signoff margin {v107_summary.get('directed_min_margin_v105_vs_0832')}.",
            "depends_on": "L2;SRC-v086;SRC-v097;SRC-v105;HASH-directed",
            "artifact_inputs": "v086 directed kernel;v097 directed replay;v105 directed signoff;v107 G2 final review",
            "hash_audit_inputs": "audit/v107_directed_kernel_hash_audit.csv",
            "route_or_component_count": str(v107_summary.get("directed_rows")),
            "status": "complete_candidate" if boolish(v107_summary.get("G2_final_review_accepted_candidate")) else "blocked",
            "proof_boundary_flag": "external_arb_kernel_formalized_false",
            "remaining_human_review_note": "External Arb/outward-rounded theorem kernel is review-accepted candidate, not machine-formalized theorem.",
        },
        {
            "lemma_id": "L4",
            "lemma_name": "Local tensor certificate lemma",
            "statement_candidate": f"The local tensor candidate kernel covers {v107_summary.get('tensor_rows')} members across {v107_summary.get('tensor_packages')} packages with zero failures against 0.832.",
            "depends_on": "L2;SRC-v086;SRC-v097;SRC-v105;HASH-tensor",
            "artifact_inputs": "v086 tensor members/packages;v097 tensor replay;v105 tensor signoff;v107 G3 final review",
            "hash_audit_inputs": "audit/v107_tensor_kernel_hash_audit.csv",
            "route_or_component_count": f"members={v107_summary.get('tensor_rows')};packages={v107_summary.get('tensor_packages')}",
            "status": "complete_candidate" if boolish(v107_summary.get("G3_final_review_accepted_candidate")) else "blocked",
            "proof_boundary_flag": "local_tensor_formalized_false",
            "remaining_human_review_note": "Tensor domination theorem is review-accepted candidate, not machine-formalized theorem.",
        },
        {
            "lemma_id": "L5",
            "lemma_name": "h004 bridge containment lemma",
            "statement_candidate": f"The h=0.004 bridge binds {v107_summary.get('h004_rows')} witness rows with zero failures and preserves the frozen v050 local proof package.",
            "depends_on": "L2;SRC-v050;SRC-v097;HASH-h004",
            "artifact_inputs": "v050 h004 freeze;v097 h004 replay;v107 h004 hash audit",
            "hash_audit_inputs": "audit/v107_h004_hash_audit.csv",
            "route_or_component_count": str(v107_summary.get("h004_rows")),
            "status": "complete_candidate" if boolish(v107_summary.get("G4_final_review_accepted_candidate")) else "blocked",
            "proof_boundary_flag": "candidate_component_not_standalone_theorem",
            "remaining_human_review_note": "Bridge statement should cite v050 frozen local package and v097 replay binding.",
        },
        {
            "lemma_id": "L6",
            "lemma_name": "Branch-B enlarged-domain route lemma",
            "statement_candidate": "The formal domain gate is discharged at candidate level by the Branch-B enlarged-domain replay route; Branch A symbolic range reduction remains unclosed and is not used.",
            "depends_on": "L1;L2;V107-G5",
            "artifact_inputs": "v105 Branch-B package;v106 Branch-B closure;v107 Branch-B final acceptance",
            "hash_audit_inputs": "audit/v107_full_route_hash_audit.csv",
            "route_or_component_count": str(v107_summary.get("adaptive_terminal_route_rows")),
            "status": "complete_candidate" if boolish(v107_summary.get("G5_BranchB_domain_final_acceptance_candidate")) else "blocked",
            "proof_boundary_flag": "BranchB_candidate_route;BranchA_symbolic_proof_unclosed",
            "remaining_human_review_note": "Final text must explicitly adopt Branch B and must not claim Branch A closure.",
        },
        {
            "lemma_id": "L7",
            "lemma_name": "BS0832 aggregation theorem candidate",
            "statement_candidate": "Combining the Branch-B domain route, terminal route dispatch, directed interval, local tensor, and h004 bridge lemmas yields the reproduction-candidate lower bound A(v) >= 0.832 for the adopted Brass-Sharifi three-test-set domain.",
            "depends_on": "L1;L2;L3;L4;L5;L6",
            "artifact_inputs": "v107 release candidate bundle;v108 proof manuscript candidate",
            "hash_audit_inputs": "all v107 hash audit summaries",
            "route_or_component_count": "final_aggregation",
            "status": "complete_candidate",
            "proof_boundary_flag": "theorem_ready_false_until_external_or_human_signoff",
            "remaining_human_review_note": "This is a final proof-manuscript candidate and requires final external/human theorem signoff before theorem_ready may be true.",
        },
    ]


def build_claim_dag() -> Tuple[List[dict], List[dict], str, bool, List[str]]:
    """Construct the claim-dependency DAG used by the proof-obligation layer."""
    nodes = [
        {"node_id": "D0", "node_type": "domain_assumption", "label": "Brass-Sharifi normalized three-test-set domain", "status": "adopted_candidate"},
        {"node_id": "L1", "node_type": "lemma", "label": "Adaptive full ledger closure", "status": "complete_candidate"},
        {"node_id": "L2", "node_type": "lemma", "label": "Terminal route dispatch coverage", "status": "complete_candidate"},
        {"node_id": "L3", "node_type": "lemma", "label": "Directed interval certificate", "status": "complete_candidate"},
        {"node_id": "L4", "node_type": "lemma", "label": "Local tensor certificate", "status": "complete_candidate"},
        {"node_id": "L5", "node_type": "lemma", "label": "h004 bridge containment", "status": "complete_candidate"},
        {"node_id": "L6", "node_type": "lemma", "label": "Branch-B enlarged-domain route", "status": "complete_candidate"},
        {"node_id": "T1", "node_type": "theorem_candidate", "label": "BS0832 reproduction candidate: A(v) >= 0.832", "status": "human_review_ready_candidate"},
    ]
    edges = [
        {"edge_id": "E1", "from_node": "D0", "to_node": "L1", "relation": "domain_partition_materialized_by"},
        {"edge_id": "E2", "from_node": "L1", "to_node": "L2", "relation": "terminal_routes_dispatched_by"},
        {"edge_id": "E3", "from_node": "L2", "to_node": "L3", "relation": "directed_route_family_bound_by"},
        {"edge_id": "E4", "from_node": "L2", "to_node": "L4", "relation": "tensor_route_family_bound_by"},
        {"edge_id": "E5", "from_node": "L2", "to_node": "L5", "relation": "h004_route_family_bound_by"},
        {"edge_id": "E6", "from_node": "L1", "to_node": "L6", "relation": "domain_route_acceptance_uses"},
        {"edge_id": "E7", "from_node": "L2", "to_node": "L6", "relation": "domain_route_acceptance_uses"},
        {"edge_id": "E8", "from_node": "L3", "to_node": "T1", "relation": "aggregates_into"},
        {"edge_id": "E9", "from_node": "L4", "to_node": "T1", "relation": "aggregates_into"},
        {"edge_id": "E10", "from_node": "L5", "to_node": "T1", "relation": "aggregates_into"},
        {"edge_id": "E11", "from_node": "L6", "to_node": "T1", "relation": "domain_scope_for"},
    ]
    node_ids = {n["node_id"] for n in nodes}
    indeg = {n: 0 for n in node_ids}
    adj = defaultdict(list)
    issues: List[str] = []
    for e in edges:
        if e["from_node"] not in node_ids or e["to_node"] not in node_ids:
            issues.append(f"missing_node_for_edge:{e['edge_id']}")
            continue
        adj[e["from_node"]].append(e["to_node"])
        indeg[e["to_node"]] += 1
    q = deque([n for n, d in indeg.items() if d == 0])
    seen = []
    while q:
        n = q.popleft()
        seen.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    acyclic = len(seen) == len(node_ids) and not issues
    dot_lines = ["digraph BS0832_v108_claim_dag {"]
    for n in nodes:
        dot_lines.append(f'  {n["node_id"]} [label="{n["node_id"]}: {n["label"]}"];')
    for e in edges:
        dot_lines.append(f'  {e["from_node"]} -> {e["to_node"]} [label="{e["relation"]}"];')
    dot_lines.append("}")
    return nodes, edges, "\n".join(dot_lines) + "\n", acyclic, issues


def build_artifact_to_lemma_binding(v107_summary: dict) -> List[dict]:
    """Bind v107 artifacts and hash audits to the v108 lemma registry."""
    rows = [
        ("A1", "v096 adaptive full ledger", "L1;L2;L6", "adaptive_full_ledger_export_v096.zip", "parent-child edges, endpoints, terminal routes", v107_summary.get("adaptive_terminal_route_rows")),
        ("A2", "v097 terminal route replay", "L2;L6", "feedback_v097...zip", "terminal replay rows and failures", v107_summary.get("terminal_route_replay_rows")),
        ("A3", "v086 directed interval kernel", "L3", "feedback_v086...zip", "directed candidate kernel rows", v107_summary.get("G2_v086_directed_rows")),
        ("A4", "v097 directed external replay", "L3", "feedback_v097...zip", "external directed replay zero failures", v107_summary.get("directed_rows")),
        ("A5", "v105 directed final signoff", "L3", "feedback_v105...zip", "final directed min margin after signoff", v107_summary.get("directed_min_margin_v105_vs_0832")),
        ("A6", "v086 local tensor members/packages", "L4", "feedback_v086...zip", "tensor member/package proof kernel", f"{v107_summary.get('G3_v086_tensor_member_rows')}/{v107_summary.get('G3_v086_tensor_package_rows')}"),
        ("A7", "v097 local tensor external replay", "L4", "feedback_v097...zip", "tensor replay zero failures", v107_summary.get("tensor_rows")),
        ("A8", "v050 h004 local proof freeze", "L5", "feedback_v050...zip", "frozen h004 local proof package", "frozen"),
        ("A9", "v097 h004 replay", "L5", "feedback_v097...zip", "h004 witness replay zero failures", v107_summary.get("h004_rows")),
        ("A10", "v106 Branch-B closure candidate", "L6", "feedback_v106...zip", "domain Branch-B replay closure candidate", "accepted_candidate"),
        ("A11", "v107 release candidate bundle", "L1;L2;L3;L4;L5;L6;L7", "feedback_v107...zip", "fresh replay + hash audit + final review", "release_candidate_ready"),
        ("A12", "v107 stronger-bound repair queue", "not_used_in_L7", "triage/v107_083201_v011_repair_launch_queue.csv", "stress target isolation only", v107_summary.get("stress_failures_083201")),
    ]
    return [{
        "binding_id": bid,
        "artifact_name": name,
        "bound_lemma_ids": lemmas,
        "source_or_member": source,
        "binding_purpose": purpose,
        "observed_count_or_status": str(count),
        "included_in_bs0832_claim": "False" if lemmas == "not_used_in_L7" else "True",
        "included_in_083201_claim": "False",
        "status": "passed_bound" if lemmas != "not_used_in_L7" else "passed_isolated_from_bs0832_claim",
    } for bid, name, lemmas, source, purpose, count in rows]


def artifact_binding_complete(lemma_rows: List[dict], binding_rows: List[dict]) -> Tuple[bool, List[str]]:
    """Return whether every lemma has an accepted artifact binding."""
    needed = {r["lemma_id"] for r in lemma_rows if r["lemma_id"] != "L7"}
    covered = set()
    for row in binding_rows:
        if row["included_in_bs0832_claim"] != "True":
            continue
        for lemma in row["bound_lemma_ids"].split(";"):
            if lemma in needed:
                covered.add(lemma)
    missing = sorted(needed - covered)
    # L7 is bound by prior lemmas and v107/v108 release bundle.
    return (not missing, missing)


def final_theorem_statement_text() -> str:
    """Render the candidate BS0832 theorem statement used in v108."""
    return """# BS0832 theorem statement candidate

Let

```text
v = (rho, x3, y3, x5, y5)
```

be an admissible Brass-Sharifi three-test-set placement in the adopted
Branch-B replay domain: the unit-diameter disk is fixed at the origin, the
unit-diameter equilateral triangle is translated by `(x3, y3)`, and the
unit-diameter regular pentagon is rotated by `rho` and translated by `(x5, y5)`.
Let

```text
A(v) = area(conv(C union (T + (x3, y3)) union (R_rho P5 + (x5, y5))))
```

be the convex-hull area functional used throughout the certificate chain.

**Theorem statement candidate.** For every admissible placement `v` covered by
the Branch-B replay domain route, the candidate certificate chain supports

```text
A(v) >= 0.832.
```

This v0.10.8 package is a reproduction-complete candidate and final signoff
package.  It does not assert a true theorem-ready flag, does not assert a stronger numerical lower
bound, and does not claim that the Branch-A symbolic range-reduction proof is
closed.
"""


def proof_overview_text(summary: dict) -> str:
    """Render the high-level proof overview from v108 summary fields."""
    return f"""# BS0832 proof overview candidate

The proof-manuscript candidate follows the Brass-Sharifi three-test-set route
with parameters `(rho, x3, y3, x5, y5)`.  The v0.10.8 package converts the
v0.10.7 artifact release candidate into a structured proof manuscript candidate.

The argument is organized as follows.

1. **Adaptive route closure.** The adaptive ledger contains
   `{summary.get('adaptive_parent_child_edges')}` parent-child edges,
   `{summary.get('adaptive_endpoint_rows')}` endpoint rows, and
   `{summary.get('adaptive_terminal_route_rows')}` terminal routes.  The v107
   full hash audit and fresh replay reported no terminal route failures.
2. **Route dispatch.** Terminal routes split into three candidate proof routes:
   `{json.dumps(summary.get('adaptive_route_counts', {}), sort_keys=True)}`.
3. **Directed interval route.** The directed/external-Arb candidate kernel binds
   `{summary.get('directed_rows')}` rows with zero failures against `0.832` and
   final signoff minimum margin `{summary.get('directed_min_margin_v105_vs_0832')}`.
4. **Local tensor route.** The tensor candidate kernel binds
   `{summary.get('tensor_rows')}` members across `{summary.get('tensor_packages')}`
   packages with zero failures against `0.832`.
5. **h004 bridge route.** The frozen h=0.004 local package binds
   `{summary.get('h004_rows')}` bridge witnesses with zero failures.
6. **Domain route.** Branch A remains unclosed.  The theorem-candidate package
   adopts the Branch-B enlarged-domain replay route, accepted as a final-review
   candidate in v107.

Boundary: this is a proof-manuscript candidate for reproducing the old `0.832`
lower bound.  It preserves `theorem_ready=false` and isolates the the stronger numerical target
stress failures for a later stronger-bound repair branch.
"""


def full_proof_draft_text(summary: dict) -> str:
    """Render the v108 proof draft tying lemmas to the certificate theorem."""
    return f"""# BS0832 full proof draft candidate

## 1. Setup

We use the Brass-Sharifi three-test-set normalization with parameter vector
`v = (rho, x3, y3, x5, y5)`.  The disk is fixed at the origin, the equilateral
triangle is translated, and the regular pentagon is rotated and translated.  The
quantity to be bounded is the convex-hull area `A(v)`.

## 2. Domain route

The final candidate proof package uses Branch B.  Branch A symbolic
range-reduction remains unclosed.  Branch B is not a new theorem statement by
itself; it is the adopted candidate replay route that connects the admissible
parameter domain to the adaptive terminal-route ledger.

## 3. Adaptive ledger and terminal route coverage

The v096/v097/v107 chain records `{summary.get('adaptive_terminal_route_rows')}`
terminal routes.  The route replay has `{summary.get('terminal_route_replay_failures')}`
failures against the BS0832 target.  The route-family dispatch is:

```json
{json.dumps(summary.get('adaptive_route_counts', {}), indent=2, sort_keys=True)}
```

## 4. Directed interval route

The directed interval route is certified by the v086/v097/v105/v107 candidate
chain.  The directed component has `{summary.get('directed_rows')}` rows,
`{summary.get('directed_failures_vs_0832')}` failures against `0.832`, and a
v105 final-signoff minimum margin of `{summary.get('directed_min_margin_v105_vs_0832')}`.
The external-Arb/outward-rounded theorem kernel remains a final-review accepted
candidate rather than a machine-formalized theorem.

## 5. Local tensor route

The local tensor route is certified by `{summary.get('tensor_rows')}` members in
`{summary.get('tensor_packages')}` packages, with
`{summary.get('tensor_failures_vs_0832')}` failures against `0.832`.  The tensor
domination theorem remains a final-review accepted candidate rather than a
machine-formalized theorem.

## 6. h004 bridge route

The h=0.004 bridge route uses the frozen v050 local package and the v097/v107
replay binding.  It has `{summary.get('h004_rows')}` witness rows and
`{summary.get('h004_failures')}` failures.

## 7. Aggregation

For each terminal route, the route dispatch sends the route to exactly one of the
three accepted candidate proof components: directed interval, local tensor, or
h004 bridge.  Each component supplies a candidate lower bound at or above
`0.832` after its recorded guards.  Therefore the v0.10.8 package is a
reproduction-complete candidate for the old Brass-Sharifi lower bound
`A(v) >= 0.832` over the Branch-B replay domain.

## 8. Boundary and non-claims

This draft does not prove the stronger numerical target.  The v107/v108 chain preserves
`{summary.get('stress_failures_083201')}` stress failures for the stronger numerical target; these
are isolated into a separate stronger-bound repair queue and are not included in the BS0832
claim.  This draft also keeps the theorem-ready flag false; final external/human
signoff is still required before theorem-level language is appropriate.
"""


def appendix_texts(summary: dict) -> Dict[str, str]:
    """Render appendix drafts for adaptive, directed, tensor, bridge, and domain routes."""
    return {
        "Appendix_A_adaptive_route_closure.md": release_text("Appendix A: adaptive route closure", f"""
- Input artifacts: v096 full adaptive ledger, adaptive_full_ledger_export_v096, v097 terminal route replay, v107 hash audit.
- Parent-child edges: `{summary.get('adaptive_parent_child_edges')}`.
- Endpoint rows: `{summary.get('adaptive_endpoint_rows')}`.
- Terminal route rows: `{summary.get('adaptive_terminal_route_rows')}`.
- Terminal replay failures: `{summary.get('terminal_route_replay_failures')}`.
- Candidate status: complete for reproduction-closure package.
"""),
        "Appendix_B_directed_interval_kernel.md": release_text("Appendix B: directed interval/external-Arb kernel", f"""
- Input artifacts: v086 directed kernel, v097 directed replay, v105 final signoff, v107 G2 final review.
- Directed rows: `{summary.get('directed_rows')}`.
- Failures against 0.832: `{summary.get('directed_failures_vs_0832')}`.
- Final signoff minimum margin: `{summary.get('directed_min_margin_v105_vs_0832')}`.
- Duplicate source identifiers: `{summary.get('G2_v086_duplicate_source_identifiers')}`; treated as multiset-bound ordered occurrences, not unique identifiers.
- Boundary: external-Arb kernel review accepted candidate; not machine-formalized theorem.
"""),
        "Appendix_C_local_tensor_theorem.md": release_text("Appendix C: local tensor theorem", f"""
- Input artifacts: v086 tensor members/packages, v097 tensor replay, v105 signoff, v107 G3 final review.
- Tensor member rows: `{summary.get('tensor_rows')}`.
- Tensor packages: `{summary.get('tensor_packages')}`.
- Failures against 0.832: `{summary.get('tensor_failures_vs_0832')}`.
- Package/member mismatches: `{summary.get('G3_v086_package_member_mismatches')}`.
- Boundary: tensor theorem review accepted candidate; not machine-formalized theorem.
"""),
        "Appendix_D_h004_bridge.md": release_text("Appendix D: h004 bridge", f"""
- Input artifacts: v050 frozen h004 package, v097 h004 replay, v107 h004 hash audit.
- h004 witness rows: `{summary.get('h004_rows')}`.
- h004 failures: `{summary.get('h004_failures')}`.
- Candidate status: complete for reproduction-closure package.
"""),
        "Appendix_E_BranchB_domain_route.md": release_text("Appendix E: Branch-B domain route", f"""
- Branch A symbolic range reduction: not closed.
- Adopted candidate domain route: Branch-B enlarged-domain replay.
- Terminal routes covered: `{summary.get('adaptive_terminal_route_rows')}`.
- Route families: `{json.dumps(summary.get('adaptive_route_counts', {}), sort_keys=True)}`.
- Candidate status: Branch-B final acceptance candidate from v107.
"""),
    }


def formalization_gap_rows() -> List[dict]:
    """List the remaining formalization gaps carried as explicit review items."""
    return [
        {
            "gap_id": "FG1",
            "gap_family": "external_arb_kernel",
            "current_state": "final_review_accepted_candidate",
            "remaining_gap": "external_arb_kernel_formalized_false",
            "required_for_theorem_ready_true": "external/human theorem signoff or machine-formal proof kernel",
            "blocks_reproduction_complete_candidate": "False",
            "blocks_theorem_ready": "True",
        },
        {
            "gap_id": "FG2",
            "gap_family": "local_tensor_theorem",
            "current_state": "final_review_accepted_candidate",
            "remaining_gap": "local_tensor_formalized_false",
            "required_for_theorem_ready_true": "external/human theorem signoff or machine-formal domination theorem",
            "blocks_reproduction_complete_candidate": "False",
            "blocks_theorem_ready": "True",
        },
        {
            "gap_id": "FG3",
            "gap_family": "domain_reduction",
            "current_state": "BranchB_final_review_accepted_candidate",
            "remaining_gap": "BranchA_symbolic_proof_unclosed; BranchB route used instead",
            "required_for_theorem_ready_true": "explicit acceptance of Branch-B route in final proof text or independent symbolic replacement",
            "blocks_reproduction_complete_candidate": "False",
            "blocks_theorem_ready": "True",
        },
        {
            "gap_id": "FG4",
            "gap_family": "final_signoff",
            "current_state": "theorem_claim_ready_for_final_human_review_candidate",
            "remaining_gap": "final external/human theorem signoff absent",
            "required_for_theorem_ready_true": "signed final review or formal proof assistant verification",
            "blocks_reproduction_complete_candidate": "False",
            "blocks_theorem_ready": "True",
        },
    ]


def theorem_statement_readiness_rows(theorem_text: str) -> List[dict]:
    """Check that the theorem statement preserves the intended scope."""
    checks = [
        ("TS1", "contains_0832_claim", "A(v) >= 0.832" in theorem_text),
        ("TS2", "does_not_claim_083201", "A(v) >= a stronger numerical target" not in theorem_text and "proved a stronger numerical target" not in theorem_text.lower()),
        ("TS3", "uses_BranchB_route", "Branch-B" in theorem_text or "Branch B" in theorem_text),
        ("TS4", "does_not_claim_BranchA_closed", "Branch A symbolic range-reduction proof is closed" not in theorem_text and "Branch A closed" not in theorem_text),
        ("TS5", "theorem_ready_not_true", "theorem_ready=true" not in theorem_text.replace(" ", "").lower()),
    ]
    return [{"check_id": cid, "check_family": fam, "status": "passed" if ok else "failed", "detail": "final theorem statement candidate audit"} for cid, fam, ok in checks]


def red_team_audit(manuscript_files: Dict[str, str]) -> Tuple[List[dict], bool]:
    # The scanner is intentionally phrase-based, not merely token-based, so safe
    # statements such as "does not prove a stronger numerical target" are not rejected.
    """Scan proof text for prohibited stronger or theorem-ready claims."""
    forbidden = [
        ("RT1", re.compile(r"proved\s+(?:a\s+)?stronger\s+numerical\s+target", re.I), "claims stronger numerical target proved"),
        ("RT2", re.compile(r"A\(v\)\s*>=\s*0\.832[0-9]+", re.I), "states a stronger numerical theorem inequality"),
        ("RT3", re.compile(r"theorem_ready\s*[=:]\s*true", re.I), "sets theorem_ready true in proof text"),
        ("RT4", re.compile(r"bs0832_reproduced_theorem_level\s*[=:]\s*true", re.I), "sets theorem-level reproduction true"),
        ("RT5", re.compile(r"Branch\s*A\s*(symbolic\s*)?(range[- ]reduction\s*)?(proof\s*)?(is\s*)?closed", re.I), "claims Branch A closed"),
        ("RT6", re.compile(r"external[- ]Arb\s+kernel\s+(is\s+)?formalized", re.I), "claims external Arb kernel formalized"),
        ("RT7", re.compile(r"local\s+tensor\s+(theorem\s+)?(is\s+)?formalized", re.I), "claims local tensor formalized"),
        ("RT8", re.compile(r"new\s+lower\s+bound", re.I), "claims a new lower bound"),
    ]
    rows: List[dict] = []
    all_passed = True
    for path, text in manuscript_files.items():
        for check_id, pattern, desc in forbidden:
            matches = pattern.findall(text)
            ok = len(matches) == 0
            all_passed = all_passed and ok
            rows.append({
                "check_id": check_id,
                "file": path,
                "forbidden_claim_family": desc,
                "match_count": str(len(matches)),
                "status": "passed" if ok else "failed",
            })
    return rows, all_passed


def build_reproducibility_rows(*checks: Tuple[str, bool, str]) -> List[dict]:
    """Build the v108 reproducibility checklist rows."""
    return [{"check_id": cid, "status": "passed" if ok else "failed", "detail": detail} for cid, ok, detail in checks]


def run_v108(
    run_id: str,
    project_root: Path,
    v107_feedback_zip: Path,
    optional_sources: Dict[str, Optional[Path]],
    allow_smoke_limits: bool = False,
    log_level: str = "INFO",
) -> dict:
    """Run the v108 reproduction-closure and proof-obligation binding stage."""
    run_dir = project_root / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    dirs = ensure_dirs(run_dir)
    log_path = dirs["log"] / f"{ARTIFACT_PREFIX}.log"
    log_line(log_path, f"Starting {VERSION} run_id={run_id}")
    log_line(log_path, f"v107_feedback_zip={v107_feedback_zip}")
    log_line(log_path, f"allow_smoke_limits={allow_smoke_limits}; log_level={log_level}")

    if not v107_feedback_zip.exists():
        raise FileNotFoundError(f"Missing required v107 feedback zip: {v107_feedback_zip}")

    # v107 schema and candidate checks.
    schema_rows, schema_ok = validate_v107_schema(v107_feedback_zip)
    write_csv(dirs["data"] / f"{ARTIFACT_PREFIX}_schema_field_validation.csv", list(schema_rows[0].keys()), schema_rows)
    log_line(log_path, f"v107 schema validation complete: {schema_ok}")

    v107_stats, v107_audit_rows = audit_v107_release_candidate(v107_feedback_zip)
    write_csv(dirs["review"] / f"{ARTIFACT_PREFIX}_v107_release_candidate_input_audit.csv", list(v107_audit_rows[0].keys()), v107_audit_rows)
    log_line(log_path, f"v107 release candidate audit complete: {v107_stats['v107_input_release_candidate_accepted']}")

    src_rows, src_ok, optional_hash_ok = source_integrity_v108(v107_feedback_zip, optional_sources, v107_stats.get("manifest"))
    write_csv(dirs["data"] / f"{ARTIFACT_PREFIX}_source_integrity_and_optional_hash_check.csv", list(src_rows[0].keys()), src_rows)
    log_line(log_path, f"source integrity complete: required={src_ok}; optional_hash_ok={optional_hash_ok}")

    summary107 = v107_stats["summary"]
    manifest107 = v107_stats["manifest"]

    # Proof manuscript candidate construction.
    theorem_statement = final_theorem_statement_text()
    overview = proof_overview_text(summary107)
    full_proof = full_proof_draft_text(summary107)
    appendices = appendix_texts(summary107)

    manuscript_files: Dict[str, str] = {
        "manuscript/BS0832_THEOREM_STATEMENT.md": theorem_statement,
        "manuscript/BS0832_PROOF_OVERVIEW.md": overview,
        "manuscript/BS0832_FULL_PROOF_DRAFT.md": full_proof,
    }
    for name, text in appendices.items():
        manuscript_files[f"manuscript/{name}"] = text
    for rel_path, text in manuscript_files.items():
        write_text(run_dir / rel_path, text)
    log_line(log_path, f"manuscript candidate emitted: files={len(manuscript_files)}")

    # Lemma registry and DAG.
    lemma_rows = build_lemma_registry(summary107)
    write_csv(dirs["proof"] / f"lemma_registry_{ARTIFACT_PREFIX}.csv", list(lemma_rows[0].keys()), lemma_rows)
    write_json(dirs["proof"] / f"lemma_registry_{ARTIFACT_PREFIX}.json", lemma_rows)
    lemma_registry_complete = all(r.get("status") == "complete_candidate" for r in lemma_rows)
    log_line(log_path, f"lemma registry complete={lemma_registry_complete}")

    nodes, edges, dot_text, dag_acyclic, dag_issues = build_claim_dag()
    write_csv(dirs["proof"] / f"claim_dependency_nodes_{ARTIFACT_PREFIX}.csv", list(nodes[0].keys()), nodes)
    write_csv(dirs["proof"] / f"claim_dependency_edges_{ARTIFACT_PREFIX}.csv", list(edges[0].keys()), edges)
    write_json(dirs["proof"] / f"claim_dependency_dag_{ARTIFACT_PREFIX}.json", {"nodes": nodes, "edges": edges, "acyclic": dag_acyclic, "issues": dag_issues})
    write_text(dirs["proof"] / f"claim_dependency_dag_{ARTIFACT_PREFIX}.dot", dot_text)
    log_line(log_path, f"claim DAG acyclic={dag_acyclic}; issues={dag_issues}")

    binding_rows = build_artifact_to_lemma_binding(summary107)
    write_csv(dirs["proof"] / f"artifact_to_lemma_binding_ledger_{ARTIFACT_PREFIX}.csv", list(binding_rows[0].keys()), binding_rows)
    binding_complete, binding_missing = artifact_binding_complete(lemma_rows, binding_rows)
    log_line(log_path, f"artifact-to-lemma binding complete={binding_complete}; missing={binding_missing}")

    # Theorem statement and proof boundary audits.
    ts_rows = theorem_statement_readiness_rows(theorem_statement)
    write_csv(dirs["proof"] / f"final_theorem_statement_readiness_{ARTIFACT_PREFIX}.csv", list(ts_rows[0].keys()), ts_rows)
    theorem_statement_ready = all(r["status"] == "passed" for r in ts_rows)

    red_rows, red_passed = red_team_audit(manuscript_files)
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_red_team_proof_text_audit.csv", list(red_rows[0].keys()), red_rows)
    log_line(log_path, f"red-team proof text audit passed={red_passed}")

    gap_rows = formalization_gap_rows()
    write_csv(dirs["proof"] / f"formalization_gap_ledger_{ARTIFACT_PREFIX}.csv", list(gap_rows[0].keys()), gap_rows)

    # Final gate matrix for v108: candidate closure vs theorem-ready boundary.
    v107_ok = v107_stats["v107_input_release_candidate_accepted"]
    proof_boundary_clean = int(summary107.get("proof_boundary_violations", -1)) == 0 and v107_stats["boundary_ok"]
    proof_manuscript_complete = len(manuscript_files) >= 8 and theorem_statement_ready and red_passed
    reproduction_complete_candidate = (
        src_ok
        and schema_ok
        and v107_ok
        and proof_boundary_clean
        and lemma_registry_complete
        and dag_acyclic
        and binding_complete
        and proof_manuscript_complete
        and boolish(summary107.get("bs0832_release_candidate_ready"))
        and not allow_smoke_limits
    )
    theorem_claim_ready_for_final_human_review = reproduction_complete_candidate and optional_hash_ok

    gates = [
        {"gate_id": "G1", "gate_family": "v107_release_candidate_input", "v108_status": "accepted" if v107_ok else "blocked", "blocks_reproduction_complete_candidate": str(not v107_ok), "theorem_boundary_status": "candidate input accepted"},
        {"gate_id": "G2", "gate_family": "proof_manuscript_candidate", "v108_status": "complete" if proof_manuscript_complete else "blocked", "blocks_reproduction_complete_candidate": str(not proof_manuscript_complete), "theorem_boundary_status": "manuscript candidate, not final theorem publication"},
        {"gate_id": "G3", "gate_family": "lemma_registry", "v108_status": "complete" if lemma_registry_complete else "blocked", "blocks_reproduction_complete_candidate": str(not lemma_registry_complete), "theorem_boundary_status": "lemma statements candidate"},
        {"gate_id": "G4", "gate_family": "claim_dependency_dag", "v108_status": "acyclic" if dag_acyclic else "blocked", "blocks_reproduction_complete_candidate": str(not dag_acyclic), "theorem_boundary_status": "DAG candidate"},
        {"gate_id": "G5", "gate_family": "artifact_to_lemma_binding", "v108_status": "complete" if binding_complete else "blocked", "blocks_reproduction_complete_candidate": str(not binding_complete), "theorem_boundary_status": "binding candidate"},
        {"gate_id": "G6", "gate_family": "red_team_proof_boundary", "v108_status": "passed" if red_passed and proof_boundary_clean else "blocked", "blocks_reproduction_complete_candidate": str(not (red_passed and proof_boundary_clean)), "theorem_boundary_status": "prevents theorem_ready/083201 leakage"},
        {"gate_id": "G7", "gate_family": "final_signoff_package", "v108_status": "reproduction_complete_candidate" if reproduction_complete_candidate else "not_ready", "blocks_reproduction_complete_candidate": str(not reproduction_complete_candidate), "theorem_boundary_status": "theorem_ready_false_until external/human signoff"},
    ]
    write_csv(dirs["gates"] / f"{ARTIFACT_PREFIX}_reproduction_closure_gate_matrix.csv", list(gates[0].keys()), gates)

    boundary_rows = []
    for flag, expected in STRICT_BOUNDARY_FLAGS.items():
        observed = False
        boundary_rows.append({
            "boundary_flag": flag,
            "observed_value": str(observed),
            "expected_value": str(expected),
            "status": "passed" if observed == expected else "failed",
            "v108_observation": "strict boundary retained in reproduction-closure candidate package",
        })
    # Additional textual audit summary rows.
    boundary_rows.extend([
        {"boundary_flag": "red_team_proof_text_audit", "observed_value": str(red_passed), "expected_value": "True", "status": "passed" if red_passed else "failed", "v108_observation": "proof manuscript does not contain forbidden theorem or stronger numerical claims"},
        {"boundary_flag": "v107_proof_boundary_clean", "observed_value": str(proof_boundary_clean), "expected_value": "True", "status": "passed" if proof_boundary_clean else "failed", "v108_observation": "v107 boundary audit carried forward"},
    ])
    proof_boundary_violations = sum(1 for r in boundary_rows if r["status"] != "passed")
    write_csv(dirs["audit"] / f"{ARTIFACT_PREFIX}_proof_boundary_audit.csv", list(boundary_rows[0].keys()), boundary_rows)

    # Keep the stronger-bound queue isolated.
    repair_rows: List[dict] = []
    if zip_has(v107_feedback_zip, V107["repair_queue"]):
        repair_rows = _read_csv_rows_from_zip(v107_feedback_zip, V107["repair_queue"])
        for r in repair_rows:
            r["v108_status"] = "carried_forward_to_stronger_bound_queue_not_used_in_bs0832_claim"
    else:
        repair_rows = [{"status": "missing_v107_repair_queue", "v108_status": "failed"}]
    write_csv(dirs["triage"] / f"{ARTIFACT_PREFIX}_083201_v011_repair_launch_queue_carried_forward.csv", list(repair_rows[0].keys()), repair_rows)

    # Release/signoff package.
    source_hashes = {"v107_feedback_zip": sha256_file(v107_feedback_zip)}
    for role, path in optional_sources.items():
        if path and path.exists():
            source_hashes[role] = sha256_file(path)
    release_manifest = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": now_utc(),
        "input_v107_release_candidate_ready": boolish(summary107.get("bs0832_release_candidate_ready")),
        "bs0832_reproduction_complete_candidate": reproduction_complete_candidate,
        "theorem_claim_ready_for_final_human_review": theorem_claim_ready_for_final_human_review,
        "theorem_ready": False,
        "proof_boundary": STRICT_BOUNDARY_FLAGS,
        "source_hashes": source_hashes,
        "v107_source_hashes_carried_forward": manifest107.get("source_hashes", {}),
        "key_counts": manifest107.get("key_counts", {}),
        "v108_outputs": {
            "manuscript_files": sorted(manuscript_files.keys()),
            "lemma_registry": f"proof/lemma_registry_{ARTIFACT_PREFIX}.csv",
            "claim_dependency_dag": f"proof/claim_dependency_dag_{ARTIFACT_PREFIX}.json",
            "artifact_to_lemma_binding": f"proof/artifact_to_lemma_binding_ledger_{ARTIFACT_PREFIX}.csv",
            "red_team_audit": f"audit/{ARTIFACT_PREFIX}_red_team_proof_text_audit.csv",
            "formalization_gap_ledger": f"proof/formalization_gap_ledger_{ARTIFACT_PREFIX}.csv",
        },
        "083201": {"target_proved": False, "stress_failures": summary107.get("stress_failures_083201"), "min_margin": summary107.get("stress_min_margin_083201")},
    }
    write_json(dirs["release"] / "BS0832_REPRODUCTION_CLOSURE_CANDIDATE_MANIFEST.json", release_manifest)
    write_text(dirs["release"] / "BS0832_REPRODUCTION_COMPLETE_CANDIDATE_BOUNDARY.md", release_text("BS0832 reproduction-complete candidate boundary", """
This v0.10.8 package is the reproduction-closure attempt and final signoff
package for the old Brass-Sharifi `0.832` lower-bound route.  It may mark
`bs0832_reproduction_complete_candidate=true` when the v107 release candidate,
manuscript candidate, lemma registry, claim DAG, artifact binding, and red-team
proof-text audit all pass.

It intentionally keeps the theorem-level flags false:

- `theorem_ready = false`
- `bs0832_reproduced_theorem_level = false`
- `target_083201_proved = false`
- `external_arb_kernel_formalized = false`
- `local_tensor_formalized = false`
- `formal_domain_proof_closed = false`

A final external/human theorem signoff or machine-formal proof kernel is still
required before theorem-level wording should be used.
"""))

    one_command_ps1 = """# v0.10.8 BS0832 theorem-level reproduction closure attempt and final signoff package
# Run from project root after placing the required v107 feedback zip.
python .\\scripts\\86_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.py `
  --run-id v108 `
  --v107-feedback-zip .\\feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip `
  --v106-feedback-zip .\\feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip `
  --v105-feedback-zip .\\feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip `
  --v096-feedback-zip .\\feedback_v096_adaptive_full_ledger_rerun_executor.zip `
  --adaptive-full-ledger-zip .\\adaptive_full_ledger_export_v096.zip `
  --v097-feedback-zip .\\feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip `
  --v086-feedback-zip .\\feedback_v086_true_arb_and_local_tensor_port_v1.zip `
  --v050-feedback-zip .\\feedback_v050_h004_local_proof_freeze_main.zip `
  --log-level INFO
"""
    write_text(dirs["release"] / "one_command_replay_v108.ps1", one_command_ps1)
    write_text(dirs["release"] / "one_command_replay_v108.py", """from pathlib import Path
import subprocess, sys
cmd = [sys.executable, str(Path('scripts') / '86_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.py'), '--run-id', 'v108', '--v107-feedback-zip', 'feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip']
raise SystemExit(subprocess.call(cmd))
""")

    artifact_index = [
        {"artifact_family": "status", "path": f"status/{ARTIFACT_PREFIX}.status.json", "purpose": "machine-readable v108 status"},
        {"artifact_family": "summary", "path": f"data/{ARTIFACT_PREFIX}_readiness_summary.json", "purpose": "reproduction closure readiness summary"},
        {"artifact_family": "manuscript", "path": "manuscript/BS0832_FULL_PROOF_DRAFT.md", "purpose": "full proof-manuscript candidate"},
        {"artifact_family": "proof", "path": f"proof/lemma_registry_{ARTIFACT_PREFIX}.csv", "purpose": "lemma registry"},
        {"artifact_family": "proof", "path": f"proof/claim_dependency_dag_{ARTIFACT_PREFIX}.json", "purpose": "claim dependency DAG"},
        {"artifact_family": "proof", "path": f"proof/artifact_to_lemma_binding_ledger_{ARTIFACT_PREFIX}.csv", "purpose": "artifact-to-lemma binding ledger"},
        {"artifact_family": "audit", "path": f"audit/{ARTIFACT_PREFIX}_red_team_proof_text_audit.csv", "purpose": "proof-text red-team audit"},
        {"artifact_family": "decision", "path": f"proof/bs0832_reproduction_closure_decision_{ARTIFACT_PREFIX}.json", "purpose": "final reproduction closure candidate decision"},
        {"artifact_family": "release", "path": "release/BS0832_REPRODUCTION_CLOSURE_CANDIDATE_MANIFEST.json", "purpose": "reviewer-facing v108 manifest"},
    ]
    write_csv(dirs["release"] / "BS0832_ARTIFACT_INDEX.csv", list(artifact_index[0].keys()), artifact_index)

    remaining_blockers = []
    if not reproduction_complete_candidate:
        for gate in gates:
            if gate["blocks_reproduction_complete_candidate"] == "True":
                remaining_blockers.append(gate["gate_id"] + ":" + gate["gate_family"])
    theorem_level_blockers = [r["gap_id"] + ":" + r["gap_family"] for r in gap_rows if r["blocks_theorem_ready"] == "True"]
    if allow_smoke_limits:
        remaining_blockers.append("SMOKE_LIMITS_ACTIVE")

    summary = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "status": "smoke_success" if allow_smoke_limits else "success",
        "input_v107_release_candidate_ready": boolish(summary107.get("bs0832_release_candidate_ready")),
        "v107_input_release_candidate_accepted": v107_ok,
        "source_integrity_passed": src_ok,
        "optional_source_hash_check_passed": optional_hash_ok,
        "schema_validation_passed": schema_ok,
        "lemma_registry_complete": lemma_registry_complete,
        "claim_dependency_dag_acyclic": dag_acyclic,
        "artifact_to_lemma_binding_complete": binding_complete,
        "proof_manuscript_complete": proof_manuscript_complete,
        "theorem_statement_candidate_ready": theorem_statement_ready,
        "red_team_proof_text_audit_passed": red_passed,
        "formalization_gap_ledger_emitted": True,
        "proof_boundary_violations": proof_boundary_violations,
        "bs0832_reproduction_complete_candidate": reproduction_complete_candidate,
        "theorem_claim_ready_for_final_human_review": theorem_claim_ready_for_final_human_review,
        "theorem_ready": False,
        "bs0832_reproduced_theorem_level": False,
        "target_083201_proved": False,
        "external_arb_kernel_formalized": False,
        "local_tensor_formalized": False,
        "formal_domain_proof_closed": False,
        "remaining_reproduction_candidate_blockers": remaining_blockers,
        "remaining_theorem_level_blockers": theorem_level_blockers,
        "adaptive_parent_child_edges": summary107.get("adaptive_parent_child_edges"),
        "adaptive_endpoint_rows": summary107.get("adaptive_endpoint_rows"),
        "adaptive_terminal_route_rows": summary107.get("adaptive_terminal_route_rows"),
        "adaptive_route_counts": summary107.get("adaptive_route_counts"),
        "directed_rows": summary107.get("directed_rows"),
        "directed_failures_vs_0832": summary107.get("directed_failures_vs_0832"),
        "directed_min_margin_v105_vs_0832": summary107.get("directed_min_margin_v105_vs_0832"),
        "tensor_rows": summary107.get("tensor_rows"),
        "tensor_packages": summary107.get("tensor_packages"),
        "tensor_failures_vs_0832": summary107.get("tensor_failures_vs_0832"),
        "h004_rows": summary107.get("h004_rows"),
        "h004_failures": summary107.get("h004_failures"),
        "stress_failures_083201": summary107.get("stress_failures_083201"),
        "stress_min_margin_083201": summary107.get("stress_min_margin_083201"),
        "allow_smoke_limits": allow_smoke_limits,
    }
    write_json(dirs["data"] / f"{ARTIFACT_PREFIX}_readiness_summary.json", summary)

    decision = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "input_v107_release_candidate_ready": boolish(summary107.get("bs0832_release_candidate_ready")),
        "lemma_registry_complete": lemma_registry_complete,
        "claim_dependency_dag_acyclic": dag_acyclic,
        "artifact_to_lemma_binding_complete": binding_complete,
        "proof_manuscript_complete": proof_manuscript_complete,
        "theorem_statement_candidate_ready": theorem_statement_ready,
        "red_team_proof_text_audit_passed": red_passed,
        "bs0832_reproduction_complete_candidate": reproduction_complete_candidate,
        "theorem_claim_ready_for_final_human_review": theorem_claim_ready_for_final_human_review,
        "theorem_ready": False,
        "strict_boundary": STRICT_BOUNDARY_FLAGS,
        "remaining_reproduction_candidate_blockers": remaining_blockers,
        "remaining_theorem_level_blockers": theorem_level_blockers,
        "gate_matrix": gates,
    }
    write_json(dirs["proof"] / f"bs0832_reproduction_closure_decision_{ARTIFACT_PREFIX}.json", decision)
    decision_rows = [{
        "decision_key": k,
        "decision_value": json.dumps(v, sort_keys=True, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v),
    } for k, v in decision.items() if k != "gate_matrix"]
    write_csv(dirs["proof"] / f"bs0832_reproduction_closure_decision_{ARTIFACT_PREFIX}.csv", list(decision_rows[0].keys()), decision_rows)

    repro_rows = build_reproducibility_rows(
        ("R1", src_ok, "required v107 feedback zip present and readable"),
        ("R2", schema_ok, "v107 schema validation passed"),
        ("R3", v107_ok, "v107 release candidate input accepted"),
        ("R4", lemma_registry_complete, "lemma registry complete"),
        ("R5", dag_acyclic, "claim dependency DAG acyclic"),
        ("R6", binding_complete, "artifact-to-lemma binding complete"),
        ("R7", proof_manuscript_complete, "proof manuscript candidate complete"),
        ("R8", red_passed, "red-team proof-text audit passed"),
        ("R9", reproduction_complete_candidate, "BS0832 reproduction complete candidate ready"),
        ("R10", not boolish(summary.get("target_083201_proved")), "stronger numerical target remains excluded"),
        ("R11", proof_boundary_violations == 0, "proof boundary preserved"),
    )
    write_csv(dirs["reproducibility"] / f"{ARTIFACT_PREFIX}_reproducibility_checklist.csv", list(repro_rows[0].keys()), repro_rows)

    status = {
        "status": summary["status"],
        "run_id": run_id,
        "version": VERSION,
        "bs0832_reproduction_complete_candidate": reproduction_complete_candidate,
        "theorem_claim_ready_for_final_human_review": theorem_claim_ready_for_final_human_review,
        "theorem_ready": False,
        "target_083201_proved": False,
        "generated_at": now_utc(),
    }
    write_json(dirs["status"] / f"{ARTIFACT_PREFIX}.status.json", status)

    report = f"""# v0.10.8 BS0832 theorem-level reproduction closure attempt and final signoff package

Status: `{summary['status']}`

## Key results

- input v107 release candidate ready: `{summary['input_v107_release_candidate_ready']}`
- lemma registry complete: `{summary['lemma_registry_complete']}`
- claim dependency DAG acyclic: `{summary['claim_dependency_dag_acyclic']}`
- artifact-to-lemma binding complete: `{summary['artifact_to_lemma_binding_complete']}`
- proof manuscript complete: `{summary['proof_manuscript_complete']}`
- red-team proof-text audit passed: `{summary['red_team_proof_text_audit_passed']}`
- BS0832 reproduction complete candidate: `{summary['bs0832_reproduction_complete_candidate']}`
- theorem claim ready for final human review: `{summary['theorem_claim_ready_for_final_human_review']}`
- theorem ready: `false`
- stronger numerical target proved: `false`
- proof boundary violations: `{summary['proof_boundary_violations']}`

## Counts inherited from v107

- adaptive terminal routes: `{summary['adaptive_terminal_route_rows']}`
- directed rows/failures: `{summary['directed_rows']}` / `{summary['directed_failures_vs_0832']}`
- tensor rows/packages/failures: `{summary['tensor_rows']}` / `{summary['tensor_packages']}` / `{summary['tensor_failures_vs_0832']}`
- h004 rows/failures: `{summary['h004_rows']}` / `{summary['h004_failures']}`
- stronger-bound stress records preserved: `{summary['stress_failures_083201']}`

## Boundary

v0.10.8 produces a reproduction-complete candidate and final signoff package.
It does not assert theorem-level completion.  `theorem_ready`,
`bs0832_reproduced_theorem_level`, and `target_083201_proved` remain false.
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
    log_line(log_path, f"Finished v108; reproduction_complete_candidate={reproduction_complete_candidate}; theorem_ready=False")

    feedback_zip = run_dir / FEEDBACK_NAME
    make_feedback_zip(run_dir, feedback_zip)
    return {"summary": summary, "run_dir": str(run_dir), "feedback_zip": str(feedback_zip)}
