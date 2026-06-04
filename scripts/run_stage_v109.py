"""Run the public v109 staged replay."""
from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from app.domain.stage_v109 import run_stage_v109
from ._logging import configure_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the v109 staged replay."""
    parser = argparse.ArgumentParser(description="Replay the v109 BS0832 certificate stage.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root; defaults to current directory.")
    parser.add_argument("--run-id", default="stage_v109", help="Run identifier under runs/.")
    parser.add_argument("--v108-feedback-zip", type=Path, default=None, help="Optional generated v108 feedback zip.")
    parser.add_argument("--signoff-json", type=Path, default=None, help="Optional author/reviewer signoff JSON.")
    parser.add_argument(
        "--mode",
        choices=["reference-signed", "generated-chain"],
        default="reference-signed",
        help="Use the bundled reference signoff, or replay v109 on a generated chain without assuming the bundled signoff applies.",
    )
    parser.add_argument("--log-level", default="INFO", help="Loguru log level.")
    return parser.parse_args()


def main() -> int:
    """Run the v109 stage and return an OS process exit code."""
    args = parse_args()
    root = args.root.resolve()
    configure_logging(root / "runs" / args.run_id / "public_stage.log", args.log_level)
    try:
        v108_zip = args.v108_feedback_zip.resolve() if args.v108_feedback_zip else None
        signoff_json = args.signoff_json.resolve() if args.signoff_json else None
        run_stage_v109(
            root=root,
            v108_feedback_zip=v108_zip,
            signoff_json=signoff_json,
            run_id=args.run_id,
            log_level=args.log_level,
            mode=args.mode,
        )
        return 0
    except Exception:
        logger.exception("v109 staged replay failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
