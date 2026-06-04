"""Public wrapper for the v107 final release-candidate review stage."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from .adaptive_global_v107 import run_v107
from .stage_common import require_files, reference_zip, resolve_output_dir, summarize_stage_result

V107_REFERENCE = "feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip"


def run_stage_v107(root: Path, v106_feedback_zip: Path | None = None, run_id: str = "stage_v107", log_level: str = "INFO") -> dict:
    """Replay the v107 independent review and release-candidate stage."""
    root = root.resolve()
    v106_zip = v106_feedback_zip or root / "certificate" / "intermediate" / "feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip"
    required = [
        v106_zip,
        root / "inputs" / "feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip",
        root / "inputs" / "feedback_v096_adaptive_full_ledger_rerun_executor.zip",
        root / "inputs" / "adaptive_full_ledger_export_v096.zip",
        root / "inputs" / "feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip",
        root / "inputs" / "feedback_v086_true_arb_and_local_tensor_port_v1.zip",
        root / "inputs" / "feedback_v050_h004_local_proof_freeze_main.zip",
    ]
    require_files(required)
    logger.info("Starting staged v107 replay using v106 feedback {}", v106_zip)
    result = run_v107(
        run_id=run_id,
        project_root=root,
        v106_feedback_zip=required[0],
        v105_feedback_zip=required[1],
        v096_feedback_zip=required[2],
        adaptive_full_ledger_zip=required[3],
        v097_feedback_zip=required[4],
        v086_feedback_zip=required[5],
        v050_feedback_zip=required[6],
        optional_sources={"v104_feedback_zip": root / "inputs" / "feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip"},
        emit_kernel_witness_samples=False,
        log_level=log_level,
    )
    out = resolve_output_dir(root, f"runs/{run_id}/public_stage")
    return summarize_stage_result("v107", Path(result["feedback_zip"]), reference_zip(root, V107_REFERENCE), out)
