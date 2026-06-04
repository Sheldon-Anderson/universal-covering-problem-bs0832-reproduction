"""Run the public v107 staged replay."""
from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from app.domain.stage_v107 import run_stage_v107
from ._logging import configure_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the v107 staged replay."""
    parser = argparse.ArgumentParser(description="Replay the v107 BS0832 certificate stage.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root; defaults to current directory.")
    parser.add_argument("--run-id", default="stage_v107", help="Run identifier under runs/.")
    parser.add_argument("--v106-feedback-zip", type=Path, default=None, help="Optional generated v106 feedback zip.")
    parser.add_argument("--log-level", default="INFO", help="Loguru log level.")
    return parser.parse_args()


def main() -> int:
    """Run the v107 stage and return an OS process exit code."""
    args = parse_args()
    root = args.root.resolve()
    configure_logging(root / "runs" / args.run_id / "public_stage.log", args.log_level)
    try:
        v106_zip = args.v106_feedback_zip.resolve() if args.v106_feedback_zip else None
        run_stage_v107(root=root, v106_feedback_zip=v106_zip, run_id=args.run_id, log_level=args.log_level)
        return 0
    except Exception:
        logger.exception("v107 staged replay failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
