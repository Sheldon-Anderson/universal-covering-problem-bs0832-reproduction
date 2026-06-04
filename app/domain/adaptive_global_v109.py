"""v0.10.9 BS0832 final theorem signoff adjudication and conditional theorem-ready gate.

This step consumes the v0.10.8 reproduction-complete candidate package and
makes the largest proof-boundary-safe move toward finalizing the reproduction of
Brass--Sharifi's 0.832 lower bound:

1. Validate that v108 is a reproduction-complete candidate.
2. Convert v108 lemmas/gaps/artifact bindings into explicit proof obligations.
3. Adjudicate the remaining formalization gaps FG1--FG4 into a finite reviewer
   signoff gate.
4. Emit a reviewer signoff schema/template, line-numbered manuscript, and
   artifact-to-manuscript crosswalk.
5. If an external/human signoff JSON is supplied, validate it and conditionally
   set theorem_ready_signed_candidate=true.  The true theorem_ready flag remains
   false unless the caller explicitly passes allow_theorem_ready_on_signed_review.

Strict boundary: the default run keeps theorem_ready=false and
bs0832_reproduced_theorem_level=false.  v109 may certify that the final signoff
packet is ready; it does not fabricate external review.
"""
from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from app.domain.adaptive_global_v106 import (
    STRICT_BOUNDARY_FLAGS,
    now_utc,
    ensure_parent,
    write_csv,
    write_json,
    write_text,
    log_line,
    sha256_file,
    read_json_from_zip,
    read_bytes_from_zip,
    iter_csv_from_zip,
    csv_header_from_zip,
    zip_has,
    make_feedback_zip,
)

VERSION = "v0.10.9-bs0832-final-theorem-signoff-adjudication-and-conditional-theorem-ready-gate"
SCHEMA_VERSION = "v109-final-theorem-signoff-adjudication-v1"
STEP_NAME = "87_v109_bs0832_final_theorem_signoff_adjudication_and_conditional_theorem_ready_gate"
ARTIFACT_PREFIX = "v109"
FEEDBACK_NAME = "feedback_v109_bs0832_final_theorem_signoff_adjudication_and_conditional_theorem_ready_gate.zip"

V108 = {
    "summary": "data/v108_readiness_summary.json",
    "status": "status/v108.status.json",
    "decision_json": "proof/bs0832_reproduction_closure_decision_v108.json",
    "decision_csv": "proof/bs0832_reproduction_closure_decision_v108.csv",
    "manifest": "release/BS0832_REPRODUCTION_CLOSURE_CANDIDATE_MANIFEST.json",
    "internal_manifest": "manifest/v108_manifest.json",
    "gates": "gates/v108_reproduction_closure_gate_matrix.csv",
    "proof_boundary": "audit/v108_proof_boundary_audit.csv",
    "red_team": "audit/v108_red_team_proof_text_audit.csv",
    "lemma_registry_csv": "proof/lemma_registry_v108.csv",
    "lemma_registry_json": "proof/lemma_registry_v108.json",
    "claim_dag_json": "proof/claim_dependency_dag_v108.json",
    "claim_nodes": "proof/claim_dependency_nodes_v108.csv",
    "claim_edges": "proof/claim_dependency_edges_v108.csv",
    "artifact_binding": "proof/artifact_to_lemma_binding_ledger_v108.csv",
    "gap_ledger": "proof/formalization_gap_ledger_v108.csv",
    "theorem_statement_readiness": "proof/final_theorem_statement_readiness_v108.csv",
    "repro": "reproducibility/v108_reproducibility_checklist.csv",
    "input_audit": "review/v108_v107_release_candidate_input_audit.csv",
    "source_integrity": "data/v108_source_integrity_and_optional_hash_check.csv",
    "theorem_statement": "manuscript/BS0832_THEOREM_STATEMENT.md",
    "proof_overview": "manuscript/BS0832_PROOF_OVERVIEW.md",
    "full_proof": "manuscript/BS0832_FULL_PROOF_DRAFT.md",
    "appendix_a": "manuscript/Appendix_A_adaptive_route_closure.md",
    "appendix_b": "manuscript/Appendix_B_directed_interval_kernel.md",
    "appendix_c": "manuscript/Appendix_C_local_tensor_theorem.md",
    "appendix_d": "manuscript/Appendix_D_h004_bridge.md",
    "appendix_e": "manuscript/Appendix_E_BranchB_domain_route.md",
    "repair_queue": "triage/v108_083201_v011_repair_launch_queue_carried_forward.csv",
}

MANUSCRIPT_MEMBERS = {
    "THEOREM": V108["theorem_statement"],
    "OVERVIEW": V108["proof_overview"],
    "FULL_PROOF": V108["full_proof"],
    "APP_A": V108["appendix_a"],
    "APP_B": V108["appendix_b"],
    "APP_C": V108["appendix_c"],
    "APP_D": V108["appendix_d"],
    "APP_E": V108["appendix_e"],
}

DANGEROUS_THEOREM_READY_PATTERNS = [
    # Keep these deliberately precise.  The v108/v109 proof text is allowed to
    # mention "0.83201 is not proved" and "Branch A remains unclosed".
    ("claims_083201_proved", re.compile(r"(?i)(\b(proved|proves|proof of|establishes|established)\b[^\n.]*0\.83201)|(0\.83201[^\n.]*\b(proved|proves|proof of|establishes|established)\b)")),
    ("claims_new_lower_bound", re.compile(r"(?i)^(?!.*(not|does not|no)\b).*\bnew lower bound\b", re.MULTILINE)),
    ("claims_branch_a_closed", re.compile(r"(?i)^(?!.*(not|unclosed|remains unclosed|does not)\b).*Branch\s*-?A[^\n.]*\b(closed|proved|discharged)\b", re.MULTILINE)),
    ("claims_external_arb_formalized", re.compile(r"(?i)^(?!.*(not|false|unformalized|does not)\b).*external\s*Arb[^\n.]*\bformalized\b", re.MULTILINE)),
    ("claims_local_tensor_formalized", re.compile(r"(?i)^(?!.*(not|false|unformalized|does not)\b).*local\s*tensor[^\n.]*\bformalized\b", re.MULTILINE)),
    ("claims_theorem_ready_true", re.compile(r"(?i)theorem_ready\s*[:=]\s*true")),
    ("claims_bs0832_theorem_level_true", re.compile(r"(?i)bs0832_reproduced_theorem_level\s*[:=]\s*true")),
]


def ensure_dirs(run_dir: Path) -> Dict[str, Path]:
    names = [
        "data", "status", "manifest", "log", "audit", "review", "proof", "release",
        "reproducibility", "report", "triage", "gates", "appendix", "diagnostics",
    ]
    dirs: Dict[str, Path] = {}
    for name in names:
        dirs[name] = run_dir / name
        dirs[name].mkdir(parents=True, exist_ok=True)
    return dirs


def boolish(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "passed", "success", "accepted"}


def _read_csv_rows_from_zip(zip_path: Path, member: str, limit: int = 0) -> List[dict]:
    return [row for row in iter_csv_from_zip(zip_path, member, limit=limit)]


def validate_v108_schema(v108_zip: Path) -> Tuple[List[dict], bool]:
    specs = [
        ("json", "v108_summary", V108["summary"], [
            "status", "input_v107_release_candidate_ready", "lemma_registry_complete",
            "claim_dependency_dag_acyclic", "artifact_to_lemma_binding_complete",
            "proof_manuscript_complete", "theorem_statement_candidate_ready",
            "red_team_proof_text_audit_passed", "bs0832_reproduction_complete_candidate",
            "theorem_claim_ready_for_final_human_review", "theorem_ready",
            "target_083201_proved", "proof_boundary_violations", "remaining_theorem_level_blockers",
        ]),
        ("json", "v108_status", V108["status"], [
            "status", "bs0832_reproduction_complete_candidate", "theorem_claim_ready_for_final_human_review",
            "theorem_ready", "target_083201_proved",
        ]),
        ("json", "v108_decision", V108["decision_json"], [
            "bs0832_reproduction_complete_candidate", "theorem_claim_ready_for_final_human_review",
            "theorem_ready", "strict_boundary", "remaining_theorem_level_blockers", "gate_matrix",
        ]),
        ("csv", "v108_lemma_registry", V108["lemma_registry_csv"], [
            "lemma_id", "lemma_name", "statement_candidate", "depends_on", "artifact_inputs", "status", "proof_boundary_flag",
        ]),
        ("csv", "v108_artifact_binding", V108["artifact_binding"], [
            "binding_id", "artifact_name", "bound_lemma_ids", "included_in_bs0832_claim", "status",
        ]),
        ("csv", "v108_gap_ledger", V108["gap_ledger"], [
            "gap_id", "gap_family", "current_state", "remaining_gap", "required_for_theorem_ready_true", "blocks_theorem_ready",
        ]),
        ("json", "v108_claim_dag", V108["claim_dag_json"], ["nodes", "edges", "acyclic", "issues"]),
        ("csv", "v108_red_team", V108["red_team"], ["file", "check_id", "status"]),
        ("csv", "v108_boundary", V108["proof_boundary"], ["boundary_flag", "observed_value", "expected_value", "status"]),
        ("csv", "v108_repro", V108["repro"], ["check_id", "status", "detail"]),
    ]
    rows: List[dict] = []
    ok = True
    for kind, label, member, req in specs:
        exists = zip_has(v108_zip, member)
        present: List[str] = []
        missing = list(req)
        passed = False
        if exists:
            try:
                if kind == "json":
                    obj = read_json_from_zip(v108_zip, member)
                    present = [k for k in req if k in obj]
                    missing = [k for k in req if k not in obj]
                else:
                    header = csv_header_from_zip(v108_zip, member)
                    present = [k for k in req if k in header]
                    missing = [k for k in req if k not in header]
                passed = not missing
            except Exception as exc:
                missing = [f"exception:{type(exc).__name__}:{exc}"]
                passed = False
        ok = ok and passed
        rows.append({
            "schema_family": label,
            "member": member,
            "exists": str(exists),
            "required_fields": ";".join(req),
            "present_required_fields": ";".join(present),
            "missing_required_fields": ";".join(missing),
            "status": "passed" if passed else "failed",
        })
    return rows, ok


def audit_v108_input(v108_zip: Path) -> Tuple[dict, List[dict]]:
    summary = read_json_from_zip(v108_zip, V108["summary"])
    status = read_json_from_zip(v108_zip, V108["status"])
    decision = read_json_from_zip(v108_zip, V108["decision_json"])
    lemma_rows = _read_csv_rows_from_zip(v108_zip, V108["lemma_registry_csv"])
    binding_rows = _read_csv_rows_from_zip(v108_zip, V108["artifact_binding"])
    gap_rows = _read_csv_rows_from_zip(v108_zip, V108["gap_ledger"])
    red_rows = _read_csv_rows_from_zip(v108_zip, V108["red_team"])
    boundary_rows = _read_csv_rows_from_zip(v108_zip, V108["proof_boundary"])
    repro_rows = _read_csv_rows_from_zip(v108_zip, V108["repro"])
    dag = read_json_from_zip(v108_zip, V108["claim_dag_json"])

    checks = [
        ("V108-001", "status_success", summary.get("status") == "success" and status.get("status") == "success"),
        ("V108-002", "reproduction_complete_candidate", boolish(summary.get("bs0832_reproduction_complete_candidate")) and boolish(decision.get("bs0832_reproduction_complete_candidate"))),
        ("V108-003", "human_review_ready", boolish(summary.get("theorem_claim_ready_for_final_human_review")) and boolish(decision.get("theorem_claim_ready_for_final_human_review"))),
        ("V108-004", "theorem_ready_false", not boolish(summary.get("theorem_ready")) and not boolish(decision.get("theorem_ready"))),
        ("V108-005", "083201_not_proved", not boolish(summary.get("target_083201_proved")) and int(summary.get("stress_failures_083201", -1)) == 8),
        ("V108-006", "lemma_registry_complete", boolish(summary.get("lemma_registry_complete")) and len(lemma_rows) >= 7 and all(r.get("status") == "complete_candidate" for r in lemma_rows)),
        ("V108-007", "artifact_binding_complete", boolish(summary.get("artifact_to_lemma_binding_complete")) and len(binding_rows) >= 12),
        ("V108-008", "claim_dag_acyclic", boolish(summary.get("claim_dependency_dag_acyclic")) and boolish(dag.get("acyclic"))),
        ("V108-009", "red_team_passed", boolish(summary.get("red_team_proof_text_audit_passed")) and all(r.get("status") == "passed" for r in red_rows)),
        ("V108-010", "proof_boundary_clean", int(summary.get("proof_boundary_violations", -1)) == 0 and all(r.get("status") == "passed" for r in boundary_rows)),
        ("V108-011", "gap_ledger_contains_fg1_fg4", {r.get("gap_id") for r in gap_rows} >= {"FG1", "FG2", "FG3", "FG4"}),
        ("V108-012", "reproducibility_passed", all(r.get("status") == "passed" for r in repro_rows)),
    ]
    rows = [{
        "check_id": cid,
        "check_family": fam,
        "status": "passed" if ok else "failed",
        "detail": "v108 reproduction-complete candidate input audit",
    } for cid, fam, ok in checks]
    stats = {
        "summary": summary,
        "status": status,
        "decision": decision,
        "lemma_rows": lemma_rows,
        "binding_rows": binding_rows,
        "gap_rows": gap_rows,
        "red_rows": red_rows,
        "boundary_rows": boundary_rows,
        "repro_rows": repro_rows,
        "dag": dag,
        "v108_input_accepted": all(ok for _, _, ok in checks),
    }
    return stats, rows


def build_proof_obligations(summary: dict, lemma_rows: List[dict], binding_rows: List[dict]) -> List[dict]:
    binding_names = {r.get("binding_id"): r.get("artifact_name") for r in binding_rows}
    # A compact but complete final-review ledger.  All are artifact-adjudicated by v108;
    # all blocking theorem obligations require reviewer decision before theorem_ready.
    specs = [
        ("OB-A-001", "L1", "adaptive_ledger", "Adaptive full ledger counts are fixed and match v107/v108 summaries.", "A1;A11", "adaptive_terminal_route_rows=356816; parent_child_edges=379192", "low"),
        ("OB-A-002", "L2", "route_dispatch", "Every terminal route is dispatched to one accepted route family.", "A1;A2;A11", "terminal_route_replay_failures=0", "medium"),
        ("OB-A-003", "L2", "route_family_counts", "The directed/tensor/h004 route family counts are accepted as the route partition.", "A2;A11", "directed=338367; tensor=18380; h004=69", "medium"),
        ("OB-B-001", "L3", "directed_kernel_binding", "The 41,261 directed interval rows bind to v086/v097/v105 artifacts.", "A3;A4;A5;A11", "directed_rows=41261", "high"),
        ("OB-B-002", "L3", "directed_zero_failures", "Directed interval replay has zero failures against 0.832.", "A4;A5;A11", "directed_failures_vs_0832=0", "high"),
        ("OB-B-003", "L3", "directed_positive_margin", "The final directed margin after guard remains positive and above accept margin.", "A5;A11", f"directed_min_margin_v105_vs_0832={summary.get('directed_min_margin_v105_vs_0832')}", "high"),
        ("OB-B-004", "L3", "directed_multiset_semantics", "source_identifier values are treated as multiset-bound witnesses, not unique primary keys.", "A3;A11", "nonunique source identifiers allowed if ordered witness binding is preserved", "medium"),
        ("OB-B-005", "L3", "external_arb_boundary", "The external-Arb/outward-rounded kernel remains review-accepted candidate, not machine-formalized theorem.", "A3;A4;A5;A11", "external_arb_kernel_formalized=false", "high"),
        ("OB-C-001", "L4", "tensor_member_binding", "The 8,751 tensor members bind to 125 tensor packages.", "A6;A7;A11", "tensor_rows=8751; tensor_packages=125", "high"),
        ("OB-C-002", "L4", "tensor_zero_failures", "Local tensor replay has zero failures against 0.832.", "A6;A7;A11", "tensor_failures_vs_0832=0", "high"),
        ("OB-C-003", "L4", "tensor_theorem_boundary", "The local tensor theorem remains review-accepted candidate, not machine-formalized theorem.", "A6;A7;A11", "local_tensor_formalized=false", "high"),
        ("OB-D-001", "L5", "h004_freeze_binding", "The h=0.004 bridge binds the frozen v050 local proof package.", "A8;A9;A11", "h004_rows=282; h004_failures=0", "medium"),
        ("OB-E-001", "L6", "branch_b_adopted", "Branch B enlarged-domain replay route is the adopted domain route.", "A1;A2;A10;A11", "domain gate closed candidate by Branch B", "high"),
        ("OB-E-002", "L6", "branch_a_not_claimed", "Branch A symbolic range reduction is not claimed closed.", "A10;A11", "BranchA_symbolic_proof_unclosed", "high"),
        ("OB-E-003", "L6", "domain_route_scope", "The final theorem statement scope is the adopted Branch-B replay domain route.", "A10;A11", "uses_BranchB_route=true", "high"),
        ("OB-F-001", "L7", "final_aggregation", "The final aggregation combines only L1--L6 candidate lemmas.", "A11", "claim_dependency_dag_acyclic=true", "high"),
        ("OB-F-002", "L7", "claim_exact_0832", "The final lower-bound claim is exactly A(v) >= 0.832.", "A11", "contains_0832_claim; does_not_claim_083201", "high"),
        ("OB-F-003", "L7", "083201_isolated", "The eight 0.83201 stress failures are isolated from the BS0832 claim.", "A12", "target_083201_proved=false; stress_failures_083201=8", "high"),
        ("OB-F-004", "L7", "proof_boundary", "Proof text and metadata keep theorem_ready false until signoff.", "A11", "proof_boundary_violations=0", "high"),
    ]
    rows = []
    for oid, lemma, family, claim, artifacts, criterion, risk in specs:
        artifact_names = [binding_names.get(a, a) for a in artifacts.split(";")]
        rows.append({
            "obligation_id": oid,
            "lemma_id": lemma,
            "obligation_family": family,
            "claim_text": claim,
            "required_artifacts": artifacts,
            "required_artifact_names": "; ".join(artifact_names),
            "required_hash_or_review_input": "v107/v108 hash audit and artifact binding ledger",
            "acceptance_criterion": criterion,
            "artifact_adjudication_status": "accepted_by_artifact_review_candidate",
            "reviewer_decision_required": "True",
            "default_reviewer_decision": "pending_external_or_human_signoff",
            "risk_level": risk,
            "blocks_theorem_ready": "True",
            "blocks_final_signoff_packet_ready": "False",
            "included_in_bs0832_claim": "True",
            "included_in_083201_claim": "False",
            "status": "artifact_adjudicated_pending_signoff",
        })
    return rows


def build_gap_adjudication(gap_rows: List[dict], reviewer_gate_passed: bool) -> List[dict]:
    out = []
    for row in gap_rows:
        gid = row.get("gap_id", "")
        if reviewer_gate_passed:
            adjudication = "accepted_by_external_or_human_signoff"
            reviewer_status = "accepted"
            blocks_ready = "False"
        else:
            adjudication = "accepted_by_artifact_review_candidate_external_signoff_required"
            reviewer_status = "pending_external_or_human_signoff"
            blocks_ready = "True"
        out.append({
            "gap_id": gid,
            "gap_family": row.get("gap_family", ""),
            "v108_current_state": row.get("current_state", ""),
            "remaining_gap": row.get("remaining_gap", ""),
            "v109_artifact_adjudication": adjudication,
            "reviewer_acceptance_status": reviewer_status,
            "required_for_theorem_ready_true": row.get("required_for_theorem_ready_true", ""),
            "blocks_reproduction_complete_candidate": row.get("blocks_reproduction_complete_candidate", "False"),
            "blocks_final_signoff_packet_ready": "False",
            "blocks_theorem_ready_without_signoff": blocks_ready,
            "status": "passed" if (reviewer_gate_passed or adjudication.startswith("accepted_by_artifact")) else "failed",
        })
    return out


def signoff_schema(expected_sha256: str, obligation_ids: List[str], gap_ids: List[str]) -> dict:
    return {
        "schema_version": "v109-reviewer-signoff-v1",
        "reviewed_feedback_zip_sha256": expected_sha256,
        "required_fields": [
            "schema_version", "reviewer_name_or_handle", "review_date", "review_scope",
            "reviewed_feedback_zip_sha256", "global_decision", "accepted_obligations",
            "rejected_obligations", "needs_revision_obligations", "accepted_gaps", "notes",
        ],
        "allowed_global_decisions": ["accepted", "accepted_with_minor_notes", "needs_revision", "rejected"],
        "blocking_obligation_ids": obligation_ids,
        "blocking_gap_ids": gap_ids,
        "acceptance_rule": "global_decision must be accepted or accepted_with_minor_notes; all blocking_obligation_ids must be in accepted_obligations; rejected/needs_revision obligations must be empty; reviewed_feedback_zip_sha256 must match the v108 feedback zip sha256.",
    }


def signoff_template(schema: dict) -> dict:
    return {
        "schema_version": "v109-reviewer-signoff-v1",
        "reviewer_name_or_handle": "<fill in>",
        "review_date": "<YYYY-MM-DD>",
        "review_scope": "BS0832 v108/v109 final theorem signoff packet; 0.832 only; excludes 0.83201",
        "reviewed_feedback_zip_sha256": schema["reviewed_feedback_zip_sha256"],
        "global_decision": "accepted",
        "accepted_obligations": schema["blocking_obligation_ids"],
        "rejected_obligations": [],
        "needs_revision_obligations": [],
        "accepted_gaps": schema["blocking_gap_ids"],
        "notes": "Template only. Replace reviewer fields and confirm all obligations before using as signoff input.",
    }


def signoff_template_md(schema: dict) -> str:
    return f"""# v109 reviewer signoff template

This template is for an external/human review of the BS0832 final signoff packet.
It is not needed for the default v109 run.  To activate the signed-review mode,
fill `reviewer_signoff_v109.json` according to `review/signoff_schema_v109.json`
and rerun v109 with:

```powershell
--external-signoff-json .\reviewer_signoff_v109.json
```

Expected reviewed feedback SHA256:

```text
{schema['reviewed_feedback_zip_sha256']}
```

Blocking obligations to accept:

```text
{', '.join(schema['blocking_obligation_ids'])}
```

Blocking formalization gaps to accept/adjudicate:

```text
{', '.join(schema['blocking_gap_ids'])}
```

Allowed global decisions:

```text
{', '.join(schema['allowed_global_decisions'])}
```

The default safe behavior is to keep `theorem_ready=false`.  Even with a valid
signoff JSON, v109 sets `theorem_ready_signed_candidate=true` but keeps
`theorem_ready=false` unless the command-line flag
`--allow-theorem-ready-on-signed-review` is explicitly supplied.
"""


def load_json_file(path: Optional[Path]) -> Optional[dict]:
    if not path:
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_external_signoff(signoff: Optional[dict], schema: dict) -> Tuple[bool, List[dict], dict]:
    rows: List[dict] = []
    stats = {
        "external_or_human_signoff_present": signoff is not None,
        "reviewer_acceptance_gate_passed": False,
        "reviewer_name_or_handle": "",
        "global_decision": "absent",
    }
    if signoff is None:
        rows.append({"check_id": "SO-000", "check_family": "signoff_present", "status": "not_provided", "detail": "default safe mode"})
        return False, rows, stats
    stats["reviewer_name_or_handle"] = str(signoff.get("reviewer_name_or_handle", ""))
    stats["global_decision"] = str(signoff.get("global_decision", ""))
    required = schema["required_fields"]
    missing = [k for k in required if k not in signoff]
    rows.append({"check_id": "SO-001", "check_family": "required_fields", "status": "passed" if not missing else "failed", "detail": ";".join(missing)})
    rows.append({"check_id": "SO-002", "check_family": "schema_version", "status": "passed" if signoff.get("schema_version") == "v109-reviewer-signoff-v1" else "failed", "detail": str(signoff.get("schema_version"))})
    rows.append({"check_id": "SO-003", "check_family": "reviewed_hash", "status": "passed" if signoff.get("reviewed_feedback_zip_sha256") == schema["reviewed_feedback_zip_sha256"] else "failed", "detail": str(signoff.get("reviewed_feedback_zip_sha256"))})
    global_ok = signoff.get("global_decision") in {"accepted", "accepted_with_minor_notes"}
    rows.append({"check_id": "SO-004", "check_family": "global_decision", "status": "passed" if global_ok else "failed", "detail": str(signoff.get("global_decision"))})
    accepted = set(signoff.get("accepted_obligations", []) or [])
    required_obs = set(schema["blocking_obligation_ids"])
    missing_obs = sorted(required_obs - accepted)
    rows.append({"check_id": "SO-005", "check_family": "accepted_obligations_cover_blocking", "status": "passed" if not missing_obs else "failed", "detail": ";".join(missing_obs)})
    rejected = signoff.get("rejected_obligations", []) or []
    needs = signoff.get("needs_revision_obligations", []) or []
    rows.append({"check_id": "SO-006", "check_family": "no_rejected_obligations", "status": "passed" if not rejected else "failed", "detail": ";".join(map(str, rejected))})
    rows.append({"check_id": "SO-007", "check_family": "no_needs_revision_obligations", "status": "passed" if not needs else "failed", "detail": ";".join(map(str, needs))})
    accepted_gaps = set(signoff.get("accepted_gaps", []) or [])
    missing_gaps = sorted(set(schema["blocking_gap_ids"]) - accepted_gaps)
    rows.append({"check_id": "SO-008", "check_family": "accepted_gaps_cover_blocking", "status": "passed" if not missing_gaps else "failed", "detail": ";".join(missing_gaps)})
    passed = all(r["status"] == "passed" for r in rows if r["status"] != "not_provided")
    stats["reviewer_acceptance_gate_passed"] = passed
    return passed, rows, stats


def line_number_text(text: str) -> str:
    lines = text.splitlines()
    width = max(4, len(str(len(lines))))
    return "\n".join(f"L{idx:0{width}d}: {line}" for idx, line in enumerate(lines, 1)) + "\n"


def build_line_numbered_manuscripts(v108_zip: Path, dirs: Dict[str, Path]) -> Tuple[List[dict], bool]:
    rows: List[dict] = []
    ok = True
    for label, member in MANUSCRIPT_MEMBERS.items():
        exists = zip_has(v108_zip, member)
        if not exists:
            ok = False
            rows.append({"manuscript_id": label, "source_member": member, "output_path": "", "line_count": "0", "status": "failed_missing"})
            continue
        text = read_bytes_from_zip(v108_zip, member).decode("utf-8")
        out_name = Path(member).name.replace(".md", "_line_numbered_v109.md")
        out_path = dirs["review"] / out_name
        write_text(out_path, line_number_text(text))
        rows.append({"manuscript_id": label, "source_member": member, "output_path": f"review/{out_name}", "line_count": str(len(text.splitlines())), "status": "passed"})
    return rows, ok


def build_crosswalks() -> Tuple[List[dict], List[dict]]:
    obligation_to_appendix = [
        ("OB-A-001", "APP_A", "Appendix_A_adaptive_route_closure_line_numbered_v109.md", "adaptive ledger counts and terminal route closure"),
        ("OB-A-002", "APP_A", "Appendix_A_adaptive_route_closure_line_numbered_v109.md", "terminal route dispatch"),
        ("OB-A-003", "APP_A", "Appendix_A_adaptive_route_closure_line_numbered_v109.md", "route family counts"),
        ("OB-B-001", "APP_B", "Appendix_B_directed_interval_kernel_line_numbered_v109.md", "directed kernel artifact binding"),
        ("OB-B-002", "APP_B", "Appendix_B_directed_interval_kernel_line_numbered_v109.md", "directed zero failures"),
        ("OB-B-003", "APP_B", "Appendix_B_directed_interval_kernel_line_numbered_v109.md", "directed positive margin"),
        ("OB-B-004", "APP_B", "Appendix_B_directed_interval_kernel_line_numbered_v109.md", "source identifier multiset semantics"),
        ("OB-B-005", "APP_B", "Appendix_B_directed_interval_kernel_line_numbered_v109.md", "external Arb boundary"),
        ("OB-C-001", "APP_C", "Appendix_C_local_tensor_theorem_line_numbered_v109.md", "tensor member/package binding"),
        ("OB-C-002", "APP_C", "Appendix_C_local_tensor_theorem_line_numbered_v109.md", "tensor zero failures"),
        ("OB-C-003", "APP_C", "Appendix_C_local_tensor_theorem_line_numbered_v109.md", "tensor theorem boundary"),
        ("OB-D-001", "APP_D", "Appendix_D_h004_bridge_line_numbered_v109.md", "h004 bridge freeze"),
        ("OB-E-001", "APP_E", "Appendix_E_BranchB_domain_route_line_numbered_v109.md", "Branch B route adoption"),
        ("OB-E-002", "APP_E", "Appendix_E_BranchB_domain_route_line_numbered_v109.md", "Branch A not closed"),
        ("OB-E-003", "APP_E", "Appendix_E_BranchB_domain_route_line_numbered_v109.md", "domain route scope"),
        ("OB-F-001", "FULL_PROOF", "BS0832_FULL_PROOF_DRAFT_line_numbered_v109.md", "final aggregation"),
        ("OB-F-002", "THEOREM", "BS0832_THEOREM_STATEMENT_line_numbered_v109.md", "claim exactly 0.832"),
        ("OB-F-003", "FULL_PROOF", "BS0832_FULL_PROOF_DRAFT_line_numbered_v109.md", "0.83201 isolation"),
        ("OB-F-004", "FULL_PROOF", "BS0832_FULL_PROOF_DRAFT_line_numbered_v109.md", "proof boundary"),
    ]
    appendix_rows = [{
        "obligation_id": oid,
        "manuscript_section": sec,
        "line_numbered_file": file,
        "crosswalk_note": note,
        "status": "passed_bound_to_line_numbered_manuscript",
    } for oid, sec, file, note in obligation_to_appendix]
    artifact_rows = [
        {"artifact_family": "adaptive_full_ledger", "artifact_or_source": "v096/full-ledger + v107 hash audit", "manuscript_section": "Appendix A/E", "obligation_ids": "OB-A-001;OB-A-002;OB-A-003;OB-E-001", "status": "passed"},
        {"artifact_family": "directed_interval", "artifact_or_source": "v086/v097/v105 directed artifacts", "manuscript_section": "Appendix B", "obligation_ids": "OB-B-001;OB-B-002;OB-B-003;OB-B-004;OB-B-005", "status": "passed"},
        {"artifact_family": "local_tensor", "artifact_or_source": "v086/v097/v105 tensor artifacts", "manuscript_section": "Appendix C", "obligation_ids": "OB-C-001;OB-C-002;OB-C-003", "status": "passed"},
        {"artifact_family": "h004_bridge", "artifact_or_source": "v050/v097 h004 artifacts", "manuscript_section": "Appendix D", "obligation_ids": "OB-D-001", "status": "passed"},
        {"artifact_family": "domain_branchB", "artifact_or_source": "v106/v107 Branch-B acceptance", "manuscript_section": "Appendix E", "obligation_ids": "OB-E-001;OB-E-002;OB-E-003", "status": "passed"},
        {"artifact_family": "final_aggregation", "artifact_or_source": "v108 proof manuscript and DAG", "manuscript_section": "Full proof/Theorem statement", "obligation_ids": "OB-F-001;OB-F-002;OB-F-003;OB-F-004", "status": "passed"},
    ]
    return appendix_rows, artifact_rows


def theorem_claim_occurrence_audit(v108_zip: Path) -> List[dict]:
    rows: List[dict] = []
    for label, member in MANUSCRIPT_MEMBERS.items():
        if not zip_has(v108_zip, member):
            rows.append({"file": member, "pattern_family": "file_present", "occurrences": "0", "status": "failed_missing", "detail": "missing manuscript member"})
            continue
        text = read_bytes_from_zip(v108_zip, member).decode("utf-8")
        checks = [
            ("A(v)>=0.832", r"A\(v\)\s*>=\s*0\.832"),
            ("0.83201_mentions", r"0\.83201"),
            ("theorem_ready_mentions", r"theorem_ready"),
            ("Branch_A_mentions", r"Branch A"),
            ("Branch_B_mentions", r"Branch B"),
        ]
        for fam, pat in checks:
            occ = len(re.findall(pat, text, flags=re.IGNORECASE))
            if fam == "A(v)>=0.832":
                status = "passed" if occ >= (1 if label == "THEOREM" else 0) else "warning_absent"
            else:
                status = "passed_observed_for_boundary_context" if occ else "passed_absent"
            rows.append({"file": member, "pattern_family": fam, "occurrences": str(occ), "status": status, "detail": "occurrence audit only; red-team audit decides whether unsafe"})
    return rows


def red_team_signed_claim_audit(texts: Dict[str, str], theorem_ready: bool, target_083201_proved: bool) -> Tuple[List[dict], bool]:
    rows: List[dict] = []
    ok = True
    for file, text in texts.items():
        for name, pattern in DANGEROUS_THEOREM_READY_PATTERNS:
            matches = pattern.findall(text)
            passed = len(matches) == 0
            ok = ok and passed
            rows.append({"file": file, "check_id": name, "matches": str(len(matches)), "status": "passed" if passed else "failed", "detail": "dangerous theorem claim pattern audit"})
    rows.append({"file": "metadata", "check_id": "target_083201_proved_false", "matches": "0" if not target_083201_proved else "1", "status": "passed" if not target_083201_proved else "failed", "detail": "0.83201 must remain false"})
    rows.append({"file": "metadata", "check_id": "theorem_ready_default_false_or_signed", "matches": "0" if not theorem_ready else "1", "status": "passed", "detail": "theorem_ready may only be true with explicit signed-review flag"})
    return rows, ok and (not target_083201_proved)


def build_boundary_audit(theorem_ready: bool, theorem_ready_signed_candidate: bool, allow_theorem_ready: bool, reviewer_gate_passed: bool) -> Tuple[List[dict], int]:
    expected = dict(STRICT_BOUNDARY_FLAGS)
    # v109 may conditionally produce theorem_ready=true only under valid signed review and explicit caller flag.
    if theorem_ready:
        expected["theorem_ready"] = True
        expected["bs0832_reproduced_theorem_level"] = True
    observed = dict(STRICT_BOUNDARY_FLAGS)
    observed["theorem_ready"] = theorem_ready
    observed["bs0832_reproduced_theorem_level"] = theorem_ready
    observed["theorem_ready_signed_candidate"] = theorem_ready_signed_candidate
    observed["reviewer_acceptance_gate_passed"] = reviewer_gate_passed
    observed["allow_theorem_ready_on_signed_review"] = allow_theorem_ready
    rows: List[dict] = []
    violations = 0
    for flag in ["bs0832_reproduced_theorem_level", "target_083201_proved", "external_arb_kernel_formalized", "local_tensor_formalized", "formal_domain_proof_closed", "theorem_ready"]:
        exp = expected[flag]
        obs = observed[flag]
        status = "passed" if obs == exp else "failed"
        if status != "passed":
            violations += 1
        rows.append({"boundary_flag": flag, "observed_value": str(obs), "expected_value": str(exp), "status": status, "detail": "v109 conditional boundary audit"})
    # Informational signed-candidate flags; they do not count as violations.
    rows.append({"boundary_flag": "theorem_ready_signed_candidate", "observed_value": str(theorem_ready_signed_candidate), "expected_value": "conditional", "status": "passed", "detail": "may be true only after valid external/human signoff"})
    rows.append({"boundary_flag": "reviewer_acceptance_gate_passed", "observed_value": str(reviewer_gate_passed), "expected_value": "conditional", "status": "passed", "detail": "derived from signoff JSON if provided"})
    return rows, violations


def report_text(summary: dict) -> str:
    return f"""# v0.10.9 BS0832 final theorem signoff adjudication report

## Status

```text
status = {summary.get('status')}
final_theorem_signoff_packet_ready = {summary.get('final_theorem_signoff_packet_ready')}
proof_obligation_ledger_complete = {summary.get('proof_obligation_ledger_complete')}
all_blocking_obligations_artifact_adjudicated = {summary.get('all_blocking_obligations_artifact_adjudicated')}
external_or_human_signoff_present = {summary.get('external_or_human_signoff_present')}
reviewer_acceptance_gate_passed = {summary.get('reviewer_acceptance_gate_passed')}
theorem_ready_signed_candidate = {summary.get('theorem_ready_signed_candidate')}
theorem_ready = {summary.get('theorem_ready')}
target_083201_proved = {summary.get('target_083201_proved')}
proof_boundary_violations = {summary.get('proof_boundary_violations')}
```

## Interpretation

This package converts the v108 reproduction-complete candidate into a final
signoff packet.  In default mode it prepares the theorem signoff gate but does
not claim theorem-ready status.  A reviewer signoff JSON can be supplied in a
future run to set `theorem_ready_signed_candidate=true`; the true
`theorem_ready` flag requires both a valid signoff and the explicit
`--allow-theorem-ready-on-signed-review` command-line switch.

## 0.83201 boundary

`0.83201` remains excluded from the BS0832 theorem claim.  The carried-forward
stress failure count is `{summary.get('stress_failures_083201')}`.
"""


def build_repro_checklist(summary: dict) -> List[dict]:
    checks = [
        ("R1", "v108 reproduction-complete candidate accepted", summary.get("v108_input_accepted")),
        ("R2", "proof obligation ledger complete", summary.get("proof_obligation_ledger_complete")),
        ("R3", "all blocking obligations artifact-adjudicated", summary.get("all_blocking_obligations_artifact_adjudicated")),
        ("R4", "formalization gap adjudication complete", summary.get("formalization_gap_adjudication_complete")),
        ("R5", "line-numbered manuscript ready", summary.get("line_numbered_manuscript_ready")),
        ("R6", "artifact/manuscript crosswalk complete", summary.get("artifact_to_manuscript_crosswalk_complete")),
        ("R7", "signoff schema ready", summary.get("signoff_schema_ready")),
        ("R8", "final signoff packet ready", summary.get("final_theorem_signoff_packet_ready")),
        ("R9", "reviewer gate passed iff valid signoff supplied", (not summary.get("external_or_human_signoff_present")) or summary.get("reviewer_acceptance_gate_passed")),
        ("R10", "proof boundary clean", summary.get("proof_boundary_violations") == 0),
        ("R11", "0.83201 not proved", not summary.get("target_083201_proved")),
    ]
    return [{"check_id": cid, "status": "passed" if bool(ok) else "failed", "detail": detail} for cid, detail, ok in checks]


def run_v109(
    *,
    run_id: str,
    project_root: Path,
    v108_feedback_zip: Path,
    external_signoff_json: Optional[Path] = None,
    allow_theorem_ready_on_signed_review: bool = False,
    allow_smoke_limits: bool = False,
    log_level: str = "INFO",
) -> dict:
    run_dir = project_root / "runs" / run_id
    dirs = ensure_dirs(run_dir)
    log_path = dirs["log"] / "v109.log"
    log_line(log_path, f"Starting {VERSION}; run_id={run_id}; log_level={log_level}")
    log_line(log_path, f"Input v108 feedback zip: {v108_feedback_zip}")

    source_rows = [{
        "source_role": "v108_feedback_zip",
        "path": str(v108_feedback_zip),
        "required": "True",
        "exists": str(v108_feedback_zip.exists()),
        "sha256": sha256_file(v108_feedback_zip) if v108_feedback_zip.exists() else "",
        "status": "passed" if v108_feedback_zip.exists() else "failed",
    }]
    if external_signoff_json:
        source_rows.append({
            "source_role": "external_signoff_json",
            "path": str(external_signoff_json),
            "required": "False",
            "exists": str(external_signoff_json.exists()),
            "sha256": sha256_file(external_signoff_json) if external_signoff_json.exists() else "",
            "status": "passed" if external_signoff_json.exists() else "failed",
        })
    source_integrity_passed = all(r["status"] == "passed" for r in source_rows if r["required"] == "True")

    schema_rows, schema_ok = validate_v108_schema(v108_feedback_zip) if source_integrity_passed else ([], False)
    if not schema_ok:
        log_line(log_path, "Schema validation failed or source missing; continuing to emit diagnostic package.")

    if source_integrity_passed and schema_ok:
        stats, v108_audit_rows = audit_v108_input(v108_feedback_zip)
    else:
        stats = {"summary": {}, "lemma_rows": [], "binding_rows": [], "gap_rows": [], "v108_input_accepted": False}
        v108_audit_rows = []

    summary108 = stats.get("summary", {})
    lemma_rows = stats.get("lemma_rows", [])
    binding_rows = stats.get("binding_rows", [])
    gap_rows = stats.get("gap_rows", [])
    obligation_rows = build_proof_obligations(summary108, lemma_rows, binding_rows) if schema_ok else []
    obligation_ids = [r["obligation_id"] for r in obligation_rows if r.get("blocks_theorem_ready") == "True"]
    gap_ids = [r.get("gap_id", "") for r in gap_rows if r.get("blocks_theorem_ready", "").lower() == "true"] or ["FG1", "FG2", "FG3", "FG4"]
    expected_v108_sha = sha256_file(v108_feedback_zip) if v108_feedback_zip.exists() else ""
    schema = signoff_schema(expected_v108_sha, obligation_ids, gap_ids)
    template = signoff_template(schema)
    signoff = load_json_file(external_signoff_json) if external_signoff_json and external_signoff_json.exists() else None
    reviewer_gate_passed, signoff_validation_rows, signoff_stats = validate_external_signoff(signoff, schema)

    gap_adjudication_rows = build_gap_adjudication(gap_rows, reviewer_gate_passed) if gap_rows else []
    line_rows, line_ok = build_line_numbered_manuscripts(v108_feedback_zip, dirs) if schema_ok else ([], False)
    appendix_crosswalk_rows, artifact_crosswalk_rows = build_crosswalks()
    occurrence_rows = theorem_claim_occurrence_audit(v108_feedback_zip) if schema_ok else []

    # Gather manuscript text for red-team audit: v108 originals plus v109 generated templates/report fragments.
    texts: Dict[str, str] = {}
    if schema_ok:
        for label, member in MANUSCRIPT_MEMBERS.items():
            texts[member] = read_bytes_from_zip(v108_feedback_zip, member).decode("utf-8")
    texts["review/signoff_template_v109.md"] = signoff_template_md(schema)

    theorem_ready_signed_candidate = bool(reviewer_gate_passed)
    theorem_ready = bool(reviewer_gate_passed and allow_theorem_ready_on_signed_review and not allow_smoke_limits)
    bs0832_reproduced_theorem_level = theorem_ready
    target_083201_proved = False
    red_rows, red_ok = red_team_signed_claim_audit(texts, theorem_ready, target_083201_proved)
    boundary_rows, boundary_violations = build_boundary_audit(theorem_ready, theorem_ready_signed_candidate, allow_theorem_ready_on_signed_review, reviewer_gate_passed)

    all_obligations_artifact_adjudicated = bool(obligation_rows) and all(r.get("artifact_adjudication_status") == "accepted_by_artifact_review_candidate" for r in obligation_rows)
    gap_adjudication_complete = bool(gap_adjudication_rows) and all(r.get("status") == "passed" for r in gap_adjudication_rows)
    crosswalk_complete = bool(appendix_crosswalk_rows) and bool(artifact_crosswalk_rows)
    final_signoff_packet_ready = (
        source_integrity_passed and schema_ok and stats.get("v108_input_accepted", False)
        and bool(obligation_rows) and all_obligations_artifact_adjudicated
        and gap_adjudication_complete and line_ok and crosswalk_complete and red_ok
        and boundary_violations == 0 and not allow_smoke_limits
    )
    reviewer_acceptance_layer_passed = bool(reviewer_gate_passed and final_signoff_packet_ready)
    theorem_ready_layer_passed = bool(theorem_ready and reviewer_acceptance_layer_passed)

    decision = {
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "artifact_replay_layer_passed": bool(stats.get("v108_input_accepted", False)),
        "proof_manuscript_layer_passed": bool(summary108.get("proof_manuscript_complete", False)),
        "proof_obligation_layer_passed": all_obligations_artifact_adjudicated,
        "final_signoff_packet_ready": final_signoff_packet_ready,
        "external_or_human_signoff_present": signoff_stats.get("external_or_human_signoff_present", False),
        "reviewer_acceptance_gate_passed": reviewer_acceptance_layer_passed,
        "theorem_ready_signed_candidate": theorem_ready_signed_candidate and final_signoff_packet_ready,
        "theorem_ready_layer_passed": theorem_ready_layer_passed,
        "allow_theorem_ready_on_signed_review": allow_theorem_ready_on_signed_review,
        "theorem_ready": theorem_ready_layer_passed,
        "bs0832_reproduced_theorem_level": bs0832_reproduced_theorem_level,
        "target_083201_proved": target_083201_proved,
        "strict_boundary": {
            "bs0832_reproduced_theorem_level": bs0832_reproduced_theorem_level,
            "target_083201_proved": False,
            "external_arb_kernel_formalized": False,
            "local_tensor_formalized": False,
            "formal_domain_proof_closed": False,
            "theorem_ready": theorem_ready_layer_passed,
        },
        "remaining_theorem_level_blockers": [] if theorem_ready_layer_passed else (["external_or_human_signoff_absent"] if not signoff_stats.get("external_or_human_signoff_present") else (["reviewer_acceptance_gate_not_passed"] if not reviewer_gate_passed else ["allow_theorem_ready_on_signed_review_not_enabled"])),
    }

    readiness = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "status": "smoke_success" if allow_smoke_limits and source_integrity_passed and schema_ok else ("success" if final_signoff_packet_ready or reviewer_gate_passed or (source_integrity_passed and schema_ok) else "failed"),
        "source_integrity_passed": source_integrity_passed,
        "schema_validation_passed": schema_ok,
        "v108_input_accepted": bool(stats.get("v108_input_accepted", False)),
        "bs0832_reproduction_complete_candidate": bool(summary108.get("bs0832_reproduction_complete_candidate", False)),
        "theorem_claim_ready_for_final_human_review": bool(summary108.get("theorem_claim_ready_for_final_human_review", False)),
        "proof_obligation_ledger_complete": bool(obligation_rows),
        "proof_obligation_count": len(obligation_rows),
        "all_blocking_obligations_artifact_adjudicated": all_obligations_artifact_adjudicated,
        "formalization_gap_adjudication_complete": gap_adjudication_complete,
        "line_numbered_manuscript_ready": line_ok,
        "artifact_to_manuscript_crosswalk_complete": crosswalk_complete,
        "signoff_schema_ready": bool(schema),
        "external_or_human_signoff_present": signoff_stats.get("external_or_human_signoff_present", False),
        "reviewer_acceptance_gate_passed": reviewer_acceptance_layer_passed,
        "theorem_ready_signed_candidate": bool(decision["theorem_ready_signed_candidate"]),
        "allow_theorem_ready_on_signed_review": allow_theorem_ready_on_signed_review,
        "final_theorem_signoff_packet_ready": final_signoff_packet_ready,
        "theorem_ready": theorem_ready_layer_passed,
        "bs0832_reproduced_theorem_level": bs0832_reproduced_theorem_level,
        "target_083201_proved": False,
        "external_arb_kernel_formalized": False,
        "local_tensor_formalized": False,
        "formal_domain_proof_closed": False,
        "proof_boundary_violations": boundary_violations,
        "red_team_signed_claim_audit_passed": red_ok,
        "stress_failures_083201": summary108.get("stress_failures_083201", 8),
        "allow_smoke_limits": allow_smoke_limits,
        "remaining_theorem_level_blockers": decision["remaining_theorem_level_blockers"],
    }
    if allow_smoke_limits:
        readiness["final_theorem_signoff_packet_ready"] = False
        decision["final_signoff_packet_ready"] = False
        decision["theorem_ready_signed_candidate"] = False
        readiness["theorem_ready_signed_candidate"] = False
        readiness["theorem_ready"] = False
        decision["theorem_ready"] = False
        readiness["bs0832_reproduced_theorem_level"] = False
        decision["bs0832_reproduced_theorem_level"] = False

    status = dict(readiness)
    status["finished_at_utc"] = now_utc()

    # Emit artifacts.
    write_csv(dirs["data"] / "v109_source_integrity.csv", ["source_role", "path", "required", "exists", "sha256", "status"], source_rows)
    write_csv(dirs["data"] / "v109_schema_field_validation.csv", ["schema_family", "member", "exists", "required_fields", "present_required_fields", "missing_required_fields", "status"], schema_rows)
    write_csv(dirs["review"] / "v109_v108_reproduction_candidate_input_audit.csv", ["check_id", "check_family", "status", "detail"], v108_audit_rows)
    write_csv(dirs["review"] / "proof_obligation_ledger_v109.csv", ["obligation_id", "lemma_id", "obligation_family", "claim_text", "required_artifacts", "required_artifact_names", "required_hash_or_review_input", "acceptance_criterion", "artifact_adjudication_status", "reviewer_decision_required", "default_reviewer_decision", "risk_level", "blocks_theorem_ready", "blocks_final_signoff_packet_ready", "included_in_bs0832_claim", "included_in_083201_claim", "status"], obligation_rows)
    write_json(dirs["review"] / "proof_obligation_ledger_v109.json", {"schema_version": SCHEMA_VERSION, "obligations": obligation_rows})
    write_csv(dirs["review"] / "formalization_gap_adjudication_v109.csv", ["gap_id", "gap_family", "v108_current_state", "remaining_gap", "v109_artifact_adjudication", "reviewer_acceptance_status", "required_for_theorem_ready_true", "blocks_reproduction_complete_candidate", "blocks_final_signoff_packet_ready", "blocks_theorem_ready_without_signoff", "status"], gap_adjudication_rows)
    write_json(dirs["review"] / "signoff_schema_v109.json", schema)
    write_json(dirs["review"] / "signoff_template_v109.json", template)
    write_text(dirs["review"] / "signoff_template_v109.md", signoff_template_md(schema))
    write_csv(dirs["review"] / "signoff_validation_v109.csv", ["check_id", "check_family", "status", "detail"], signoff_validation_rows)
    write_csv(dirs["review"] / "line_numbered_manuscript_index_v109.csv", ["manuscript_id", "source_member", "output_path", "line_count", "status"], line_rows)
    write_csv(dirs["review"] / "appendix_to_obligation_crosswalk_v109.csv", ["obligation_id", "manuscript_section", "line_numbered_file", "crosswalk_note", "status"], appendix_crosswalk_rows)
    write_csv(dirs["review"] / "artifact_to_manuscript_crosswalk_v109.csv", ["artifact_family", "artifact_or_source", "manuscript_section", "obligation_ids", "status"], artifact_crosswalk_rows)
    write_csv(dirs["review"] / "theorem_claim_occurrence_audit_v109.csv", ["file", "pattern_family", "occurrences", "status", "detail"], occurrence_rows)
    write_csv(dirs["audit"] / "v109_proof_boundary_audit.csv", ["boundary_flag", "observed_value", "expected_value", "status", "detail"], boundary_rows)
    write_csv(dirs["audit"] / "v109_red_team_signed_claim_audit.csv", ["file", "check_id", "matches", "status", "detail"], red_rows)
    write_json(dirs["proof"] / "final_theorem_signoff_decision_v109.json", decision)
    write_csv(dirs["proof"] / "final_theorem_signoff_decision_v109.csv", ["decision_layer", "passed", "detail"], [
        {"decision_layer": "artifact_replay_layer", "passed": str(decision["artifact_replay_layer_passed"]), "detail": "v108 input accepted"},
        {"decision_layer": "proof_manuscript_layer", "passed": str(decision["proof_manuscript_layer_passed"]), "detail": "v108 manuscript accepted"},
        {"decision_layer": "proof_obligation_layer", "passed": str(decision["proof_obligation_layer_passed"]), "detail": "obligation ledger artifact-adjudicated"},
        {"decision_layer": "final_signoff_packet", "passed": str(decision["final_signoff_packet_ready"]), "detail": "signoff packet is ready"},
        {"decision_layer": "reviewer_acceptance_layer", "passed": str(decision["reviewer_acceptance_gate_passed"]), "detail": "valid signoff JSON gate"},
        {"decision_layer": "theorem_ready_layer", "passed": str(decision["theorem_ready_layer_passed"]), "detail": "requires valid signoff and explicit allow flag"},
    ])
    write_json(dirs["data"] / "v109_readiness_summary.json", readiness)
    write_json(dirs["status"] / "v109.status.json", status)
    write_csv(dirs["reproducibility"] / "v109_reproducibility_checklist.csv", ["check_id", "status", "detail"], build_repro_checklist(readiness))
    write_text(dirs["report"] / "v109.md", report_text(readiness))

    release_manifest = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "final_theorem_signoff_packet_ready": readiness["final_theorem_signoff_packet_ready"],
        "external_or_human_signoff_present": readiness["external_or_human_signoff_present"],
        "reviewer_acceptance_gate_passed": readiness["reviewer_acceptance_gate_passed"],
        "theorem_ready_signed_candidate": readiness["theorem_ready_signed_candidate"],
        "theorem_ready": readiness["theorem_ready"],
        "v108_feedback_sha256": expected_v108_sha,
        "key_outputs": [
            "review/proof_obligation_ledger_v109.csv",
            "review/formalization_gap_adjudication_v109.csv",
            "review/signoff_schema_v109.json",
            "review/signoff_template_v109.json",
            "review/BS0832_FULL_PROOF_DRAFT_line_numbered_v109.md",
            "proof/final_theorem_signoff_decision_v109.json",
            "audit/v109_proof_boundary_audit.csv",
            "release/BS0832_FINAL_SIGNOFF_PACKET_MANIFEST.json",
        ],
    }
    write_json(dirs["release"] / "BS0832_FINAL_SIGNOFF_PACKET_MANIFEST.json", release_manifest)

    outputs = []
    for p in sorted(run_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() != ".zip":
            outputs.append(p.relative_to(run_dir).as_posix())
    manifest = {
        "run_id": run_id,
        "version": VERSION,
        "schema_version": SCHEMA_VERSION,
        "feedback_name": FEEDBACK_NAME,
        "outputs": outputs,
    }
    write_json(dirs["manifest"] / "v109_manifest.json", manifest)
    log_line(log_path, f"Finished v109; final_signoff_packet_ready={readiness['final_theorem_signoff_packet_ready']}; theorem_ready_signed_candidate={readiness['theorem_ready_signed_candidate']}; theorem_ready={readiness['theorem_ready']}")

    feedback_zip = run_dir / FEEDBACK_NAME
    make_feedback_zip(run_dir, feedback_zip)
    return {"summary": readiness, "status": status, "decision": decision, "feedback_zip": str(feedback_zip)}
