"""Public entry point for repository release checks."""
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from ucbs.cli.common import (
    add_artifact_root_argument,
    add_certificate_archive_arguments,
    add_log_level_argument,
    add_root_argument,
    add_run_id_argument,
)
from ucbs.cli.output import emit_summary
from ucbs.verification.repository_checks import run_repository_check


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_root_argument(parser)
    add_artifact_root_argument(parser)
    add_certificate_archive_arguments(parser)
    add_run_id_argument(parser, "repository_check")
    add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run public repository checks and return a process exit code.

    The command checks the public release layout, Markdown policy, claim
    boundaries, artifact hashes, Python compilation, and the main certificate
    verification. A compact JSON summary is written to standard output.
    """
    args = build_parser().parse_args(argv)
    result = run_repository_check(
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
            "failed_step_count": result.failed_step_count,
            "feedback": str(result.feedback),
        }
    )
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
