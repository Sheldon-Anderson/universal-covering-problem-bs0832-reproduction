"""Public wrapper for the v106 Branch-B domain and kernel-closure stage."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from .adaptive_global_v106 import run_v106
from .stage_common import require_files, reference_zip, resolve_output_dir, summarize_stage_result

V106_REFERENCE = "feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip"


def run_stage_v106(root: Path, run_id: str = "stage_v106", log_level: str = "INFO") -> dict:
    """Replay the v106 stage from the published source archives.

    This stage starts from the v105 final signoff attempt, the v096 full ledger,
    the v097 external replay, and the v086/v050 local certificate sources.  It
    rebuilds the Branch-B enlarged-domain replay closure candidate.
    """
    root = root.resolve()
    required = [
        root / "inputs" / "feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip",
        root / "inputs" / "feedback_v096_adaptive_full_ledger_rerun_executor.zip",
        root / "inputs" / "adaptive_full_ledger_export_v096.zip",
        root / "inputs" / "feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip",
        root / "inputs" / "feedback_v086_true_arb_and_local_tensor_port_v1.zip",
        root / "inputs" / "feedback_v050_h004_local_proof_freeze_main.zip",
    ]
    require_files(required)
    logger.info("Starting staged v106 replay from {}", root)
    result = run_v106(
        run_id=run_id,
        project_root=root,
        v105_feedback_zip=required[0],
        v096_feedback_zip=required[1],
        adaptive_full_ledger_zip=required[2],
        v097_feedback_zip=required[3],
        v086_feedback_zip=required[4],
        v050_feedback_zip=required[5],
        optional_sources={"v104_feedback_zip": root / "inputs" / "feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip"},
        emit_full_route_audit=False,
        emit_full_external_bindings=False,
        emit_kernel_witness_tables=False,
        log_level=log_level,
    )
    out = resolve_output_dir(root, f"runs/{run_id}/public_stage")
    return summarize_stage_result("v106", Path(result["feedback_zip"]), reference_zip(root, V106_REFERENCE), out)
