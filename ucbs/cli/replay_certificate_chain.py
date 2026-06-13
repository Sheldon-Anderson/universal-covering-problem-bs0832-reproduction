"""Replay the four certificate-chain components."""
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ucbs.certificate.chain_replay import resolve_default_inputs, write_chain_replay
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
    add_run_id_argument(parser, "certificate_chain_replay")
    add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run certificate-chain replay and return a process exit code.

    The command replays the four bundled certificate components without
    running repository-layout, Markdown, or claim-boundary checks.
    """
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    inputs = resolve_default_inputs(
        root,
        args.artifact_root,
        per_record_evidence_zip=args.per_record_evidence_zip,
        construction_audit_zip=args.construction_audit_zip,
        witness_construction_zip=args.witness_construction_zip,
        final_adjudication_zip=args.final_adjudication_zip,
    )
    feedback = write_chain_replay(
        root=root,
        inputs=inputs,
        run_id=args.run_id,
        log_level=args.log_level,
    )
    status_path = root / "runs" / args.run_id / "status" / "certificate_chain_replay.status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    emit_summary(
        {
            "status": status["status"],
            "failed_component_count": status["failed_component_count"],
            "feedback": str(feedback),
        }
    )
    return 0 if status["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
