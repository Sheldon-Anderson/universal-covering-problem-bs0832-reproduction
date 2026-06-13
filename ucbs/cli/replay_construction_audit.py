"""Replay the construction audit component of the certificate chain."""
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ucbs.certificate.construction_audit import run_construction_audit_replay
from ucbs.cli.common import add_log_level_argument, add_root_argument, add_run_id_argument
from ucbs.cli.output import emit_summary
from ucbs.verification.artifact_checks import DEFAULT_ARTIFACT_ROOT, DEFAULT_CONSTRUCTION_AUDIT


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for this component replay."""
    parser = argparse.ArgumentParser(description=__doc__)
    add_root_argument(parser)
    parser.add_argument(
        "--construction-audit-zip",
        default=None,
        help="Explicit construction-audit archive.",
    )
    add_run_id_argument(parser, "construction_audit_replay")
    add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the component replay command and return a process exit code.

    Detailed diagnostics are written under ``runs/<run-id>/``. A compact JSON
    summary is emitted to standard output.
    """
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    archive = getattr(args, "construction_audit_zip") or DEFAULT_ARTIFACT_ROOT / DEFAULT_CONSTRUCTION_AUDIT
    feedback = run_construction_audit_replay(
        root,
        archive,
        run_id=args.run_id,
        log_level=args.log_level,
    )
    status_path = root / "runs" / args.run_id / "status" / "construction_audit_replay.status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    emit_summary(
        {
            "status": status["status"],
            "construction_audit_passed": status.get("construction_audit_passed"),
            "feedback": str(feedback),
        }
    )
    return 0 if status["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
