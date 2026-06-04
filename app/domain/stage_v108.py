"""Public wrapper for the v108 proof-manuscript closure stage."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from .adaptive_global_v108 import run_v108
from .stage_common import require_files, reference_zip, resolve_output_dir, summarize_stage_result

V108_REFERENCE = "feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip"


def run_stage_v108(
    root: Path,
    v107_feedback_zip: Path | None = None,
    v106_feedback_zip: Path | None = None,
    run_id: str = "stage_v108",
    log_level: str = "INFO",
) -> dict:
    """Replay the v108 proof-manuscript and reproduction-closure stage.

    When ``v107_feedback_zip`` is generated from a fresh v106 run, pass the
    same generated v106 archive through ``v106_feedback_zip``.  This keeps the
    generated-chain source-hash audit internally consistent.  If omitted, the
    bundled reference v106 archive is used.
    """
    root = root.resolve()
    v107_zip = v107_feedback_zip or root / "certificate" / "intermediate" / "feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip"
    v106_zip = v106_feedback_zip or root / "certificate" / "intermediate" / "feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip"
    require_files([v107_zip, v106_zip])
    logger.info("Starting staged v108 replay using v107 feedback {} and v106 source {}", v107_zip, v106_zip)
    optional_sources = {
        "v106_feedback_zip": v106_zip,
        "v105_feedback_zip": root / "inputs" / "feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip",
        "v096_feedback_zip": root / "inputs" / "feedback_v096_adaptive_full_ledger_rerun_executor.zip",
        "adaptive_full_ledger_zip": root / "inputs" / "adaptive_full_ledger_export_v096.zip",
        "v097_feedback_zip": root / "inputs" / "feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip",
        "v086_feedback_zip": root / "inputs" / "feedback_v086_true_arb_and_local_tensor_port_v1.zip",
        "v050_feedback_zip": root / "inputs" / "feedback_v050_h004_local_proof_freeze_main.zip",
    }
    result = run_v108(run_id=run_id, project_root=root, v107_feedback_zip=v107_zip, optional_sources=optional_sources, log_level=log_level)
    out = resolve_output_dir(root, f"runs/{run_id}/public_stage")
    return summarize_stage_result("v108", Path(result["feedback_zip"]), reference_zip(root, V108_REFERENCE), out)
