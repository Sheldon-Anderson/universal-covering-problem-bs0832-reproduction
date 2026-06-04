"""Command-line entry point for the BS0832 final repository verifier."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from loguru import logger

from app.domain.final_verifier import verify_repository


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Verify the BS0832 reproduction repository.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root. Defaults to the current directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/final_verification"),
        help="Directory for logs and verification summary, relative to --root unless absolute.",
    )
    parser.add_argument("--log-level", default="INFO", help="Loguru log level, e.g. INFO or DEBUG.")
    return parser.parse_args()


def configure_logging(log_path: Path, level: str) -> None:
    """Configure console and file logging."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level=level, format="<level>{level}</level> | {message}")
    logger.add(log_path, level=level, rotation="10 MB", retention=3, encoding="utf-8")


def main() -> int:
    """Run the verifier and return a process exit code."""
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    configure_logging(output_dir / "final_verification.log", args.log_level)

    try:
        verify_repository(root=root, output_dir=output_dir)
        return 0
    except Exception:
        logger.exception("BS0832 final repository verification failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
