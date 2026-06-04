"""Shared Loguru configuration for public command-line scripts."""
from __future__ import annotations

from pathlib import Path
import sys

from loguru import logger


def configure_logging(log_path: Path, level: str) -> None:
    """Configure console and file logging for a command-line run."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level=level, format="<level>{level}</level> | {message}")
    logger.add(log_path, level=level, rotation="20 MB", retention=5, encoding="utf-8")
