"""Public entry point for certificate verification."""
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from ucbs.certificate.chain_replay import verify_certificate
from ucbs.cli.common import (
    add_artifact_root_argument,
    add_certificate_archive_arguments,
    add_log_level_argument,
    add_root_argument,
    add_run_id_argument,
)
from ucbs.cli.output import emit_summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_root_argument(parser)
    add_artifact_root_argument(parser)
    add_certificate_archive_arguments(parser)
    add_run_id_argument(parser, "certificate_verification")
    add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run certificate verification and return a process exit code.

    The command writes detailed diagnostics under ``runs/<run-id>/`` and
    emits a compact JSON summary to standard output.
    """
    args = build_parser().parse_args(argv)
    result = verify_certificate(
        root=Path(args.root),
        artifact_root=args.artifact_root,
        per_record_evidence_zip=args.per_record_evidence_zip,
        construction_audit_zip=args.construction_audit_zip,
        witness_construction_zip=args.witness_construction_zip,
        final_adjudication_zip=args.final_adjudication_zip,
        run_id=args.run_id,
        log_level=args.log_level,
    )
    emit_summary(
        {
            "status": result.status,
            "certificate_verified": result.certificate_verified,
            "threshold_proved": result.threshold_proved,
            "failed_component_count": result.failed_component_count,
            "feedback": str(result.output_feedback),
        }
    )
    return 0 if result.certificate_verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
