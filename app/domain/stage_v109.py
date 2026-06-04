"""Public wrapper for the v109 final signoff-adjudication stage."""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from .adaptive_global_v109 import run_v109
from .stage_common import require_files, resolve_output_dir, summarize_stage_result


def run_stage_v109(
    root: Path,
    v108_feedback_zip: Path | None = None,
    signoff_json: Path | None = None,
    run_id: str = "stage_v109",
    log_level: str = "INFO",
    mode: str = "reference-signed",
) -> dict:
    """Replay the v109 signoff-adjudication stage.

    Parameters
    ----------
    root:
        Repository root.
    v108_feedback_zip:
        Optional v108 archive.  In ``reference-signed`` mode, the default is the
        reference v108 archive under ``certificate/intermediate`` because the
        bundled author self-review signoff is SHA-bound to that file.  In
        ``generated-chain`` mode, callers may pass a freshly generated v108
        archive; no bundled signoff is applied unless a matching signoff JSON is
        explicitly supplied.
    signoff_json:
        Optional structured signoff JSON.
    mode:
        ``reference-signed`` validates the bundled author self-review signoff
        against the reference v108 archive.  ``generated-chain`` replays v109 on
        a generated v108 archive without assuming that the reference signoff is
        valid for the regenerated outer ZIP file.
    """
    if mode not in {"reference-signed", "generated-chain"}:
        raise ValueError("mode must be either 'reference-signed' or 'generated-chain'")

    root = root.resolve()
    reference_v108 = root / "certificate" / "intermediate" / "feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip"
    reference_v109 = root / "certificate" / "feedback_v109_signed_author_self_review.zip"

    if mode == "reference-signed":
        v108_zip = v108_feedback_zip or reference_v108
        signoff = signoff_json or root / "certificate" / "reviewer_signoff_v109.json"
        require_files([v108_zip, signoff])
        logger.info("Starting reference-signed v109 replay using v108 feedback {}", v108_zip)
    else:
        v108_zip = v108_feedback_zip or reference_v108
        signoff = signoff_json
        require_files([v108_zip])
        if signoff is not None:
            require_files([signoff])
            logger.info("Starting generated-chain v109 replay with an explicit signoff: {}", signoff)
        else:
            logger.info("Starting generated-chain v109 replay without a signoff JSON")

    result = run_v109(
        run_id=run_id,
        project_root=root,
        v108_feedback_zip=v108_zip,
        external_signoff_json=signoff,
        allow_theorem_ready_on_signed_review=False,
        log_level=log_level,
    )
    out = resolve_output_dir(root, f"runs/{run_id}/public_stage")
    summary = summarize_stage_result("v109", Path(result["feedback_zip"]), reference_v109, out)
    summary["mode"] = mode
    summary["signoff_json"] = str(signoff) if signoff else ""
    summary["signoff_applied"] = bool(signoff)
    # Rewrite the summary after adding public-mode fields.
    from .io_utils import write_json
    write_json(out / "v109_stage_summary.json", summary)
    return summary
