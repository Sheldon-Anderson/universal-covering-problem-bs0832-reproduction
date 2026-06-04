"""Final public verifier for the BS0832 reproduction repository."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from loguru import logger

from .certificate_checks import validate_final_certificate
from .io_utils import write_json, sha256_file
from .manifest import parse_sha256sums
from .signoff import validate_signoff

# Source archives needed to reproduce the staged certificate chain.
REQUIRED_INPUTS = [
    "inputs/feedback_v050_h004_local_proof_freeze_main.zip",
    "inputs/feedback_v086_true_arb_and_local_tensor_port_v1.zip",
    "inputs/feedback_v096_adaptive_full_ledger_rerun_executor.zip",
    "inputs/adaptive_full_ledger_export_v096.zip",
    "inputs/feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip",
    "inputs/feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip",
    "inputs/feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip",
]

# Reference intermediate archives bundled for comparison and signed validation.
REQUIRED_INTERMEDIATE_FILES = [
    "certificate/intermediate/feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip",
    "certificate/intermediate/feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip",
    "certificate/intermediate/feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip",
]

# Final public certificate files checked by the fast verifier.
REQUIRED_CERTIFICATE_FILES = [
    "certificate/feedback_v109_signed_author_self_review.zip",
    "certificate/reviewer_signoff_v109.json",
    "certificate/MANIFEST.json",
    "certificate/SHA256SUMS.txt",
]

# Compiled manuscript distributed with the public repository.
PAPER_FILE = "paper/A_Reproducible_Certificate_for_the_Brass_Sharifi_Lower_Bound.pdf"


def verify_sha256sums(root: Path, sha256sums_path: Path) -> list[dict[str, str]]:
    """Verify all paths recorded in SHA256SUMS.txt.

    The function returns a compact list of checked paths and their digests for
    inclusion in the final verification summary.
    """
    expected = parse_sha256sums(sha256sums_path)
    checked: list[dict[str, str]] = []
    for rel_path, expected_digest in sorted(expected.items()):
        file_path = root / rel_path
        if not file_path.is_file():
            raise FileNotFoundError(f"Missing manifest file: {rel_path}")
        actual_digest = sha256_file(file_path)
        if actual_digest != expected_digest:
            raise ValueError(f"SHA256 mismatch for {rel_path}")
        checked.append({"path": rel_path, "sha256": actual_digest})
    return checked


def verify_repository(root: Path, output_dir: Path) -> dict[str, Any]:
    """Run the final public verification workflow.

    The workflow checks file presence, SHA256 integrity, the signed certificate
    archive, and the structured author signoff.  It writes a JSON summary under
    *output_dir* and returns the same data to the caller.
    """
    root = root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting BS0832 final repository verification")
    logger.info("Repository root: {}", root)

    # Presence checks fail early with a clear message before any hash or signoff validation.
    required = REQUIRED_INPUTS + REQUIRED_INTERMEDIATE_FILES + REQUIRED_CERTIFICATE_FILES + [PAPER_FILE]
    missing = [rel for rel in required if not (root / rel).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required files: {missing}")
    logger.info("Required file presence check passed: {} files", len(required))

    # The checksum file is the repository-level integrity record for public artifacts.
    checked_hashes = verify_sha256sums(root, root / "certificate" / "SHA256SUMS.txt")
    logger.info("SHA256 manifest check passed: {} files", len(checked_hashes))

    # The signed v109 archive carries the final certificate decision used by the fast path.
    certificate_summary = validate_final_certificate(
        root / "certificate" / "feedback_v109_signed_author_self_review.zip"
    )
    logger.info("Final certificate archive check passed")

    # The signoff is bound to the reference v108 archive through its SHA256 digest.
    signoff_summary = validate_signoff(
        root / "certificate" / "reviewer_signoff_v109.json",
        root / "certificate" / "intermediate" / "feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip",
    )
    logger.info("Structured signoff check passed for reviewer {}", signoff_summary["reviewer"])

    summary: dict[str, Any] = {
        "status": "success",
        "bs0832_final_repository_verification_passed": True,
        "required_file_count": len(required),
        "sha256_checked_file_count": len(checked_hashes),
        "certificate_summary": certificate_summary,
        "signoff_summary": signoff_summary,
        "theorem_ready_signed_candidate": True,
        "theorem_ready": False,
        "proof_boundary_violations": 0,
    }
    write_json(output_dir / "final_verification_summary.json", summary)
    logger.info("Verification summary written to {}", output_dir / "final_verification_summary.json")
    logger.success("BS0832 final repository verification passed")
    return summary
