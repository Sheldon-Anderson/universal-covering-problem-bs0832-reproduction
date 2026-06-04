"""Run the public v106 staged replay."""
from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from app.domain.stage_v106 import run_stage_v106
from ._logging import configure_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the v106 staged replay."""
    parser = argparse.ArgumentParser(description="Replay the v106 BS0832 certificate stage.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root; defaults to current directory.")
    parser.add_argument("--run-id", default="stage_v106", help="Run identifier under runs/.")
    parser.add_argument("--log-level", default="INFO", help="Loguru log level.")
    return parser.parse_args()


def main() -> int:
    """Run the v106 stage and return an OS process exit code."""
    args = parse_args()
    root = args.root.resolve()
    configure_logging(root / "runs" / args.run_id / "public_stage.log", args.log_level)
    try:
        run_stage_v106(root=root, run_id=args.run_id, log_level=args.log_level)
        return 0
    except Exception:
        logger.exception("v106 staged replay failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
