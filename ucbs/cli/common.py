"""Shared command-line parser helpers for UCBS entry points."""
from __future__ import annotations

import argparse

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]
"""Supported logging-level labels recorded in run logs."""


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add the repository-root argument used by all public commands."""
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root. Defaults to the current directory.",
    )


def add_log_level_argument(parser: argparse.ArgumentParser) -> None:
    """Add the log-level argument used in generated run logs."""
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=LOG_LEVELS,
        help="Logging level label recorded in output logs.",
    )


def add_run_id_argument(
    parser: argparse.ArgumentParser,
    default: str,
) -> None:
    """Add the run-id argument that selects the directory under ``runs``."""
    parser.add_argument(
        "--run-id",
        default=default,
        help="Output directory name under runs/.",
    )


def add_artifact_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add the optional certificate-archive directory argument."""
    parser.add_argument(
        "--artifact-root",
        default=None,
        help="Directory containing certificate-chain feedback archives.",
    )


def add_certificate_archive_arguments(parser: argparse.ArgumentParser) -> None:
    """Add explicit paths for the four bundled certificate archives."""
    parser.add_argument(
        "--per-record-evidence-zip",
        default=None,
        help="Explicit per-record evidence feedback archive.",
    )
    parser.add_argument(
        "--construction-audit-zip",
        default=None,
        help="Explicit construction-audit feedback archive.",
    )
    parser.add_argument(
        "--witness-construction-zip",
        default=None,
        help="Explicit witness-construction feedback archive.",
    )
    parser.add_argument(
        "--final-adjudication-zip",
        default=None,
        help="Explicit final-adjudication feedback archive.",
    )
