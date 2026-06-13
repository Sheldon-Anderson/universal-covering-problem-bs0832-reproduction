"""Replay the per-record evidence component of the certificate chain."""
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ucbs.certificate.per_record_evidence import run_per_record_evidence_replay
from ucbs.cli.common import add_log_level_argument, add_root_argument, add_run_id_argument
from ucbs.cli.output import emit_summary
from ucbs.verification.artifact_checks import DEFAULT_ARTIFACT_ROOT, DEFAULT_PER_RECORD_EVIDENCE


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for this component replay."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_root_argument(parser)
    parser.add_argument(
        "--per-record-evidence-zip",
        default=None,
        help="Explicit per-record evidence archive.",
    )
    add_run_id_argument(parser, "per_record_evidence_replay")
    add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the component replay command and return a process exit code.

    Detailed diagnostics are written under ``runs/<run-id>/``. A compact JSON
    summary is emitted to standard output.
    """
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    archive = getattr(args, "per_record_evidence_zip") or DEFAULT_ARTIFACT_ROOT / DEFAULT_PER_RECORD_EVIDENCE
    feedback = run_per_record_evidence_replay(
        root,
        archive,
        run_id=args.run_id,
        log_level=args.log_level,
    )
    status_path = root / "runs" / args.run_id / "status" / "per_record_evidence_replay.status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    emit_summary(
        {
            "status": status["status"],
            "failed_rows": status.get("failed_rows"),
            "feedback": str(feedback),
        }
    )
    return 0 if status["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
