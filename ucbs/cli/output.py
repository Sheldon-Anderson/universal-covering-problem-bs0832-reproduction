"""Output helpers for command-line entry points."""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any


def emit_summary(summary: Mapping[str, Any]) -> None:
    """Write a stable JSON command summary to standard output.

    The detailed verification log is written under ``runs/<run-id>/log``.
    Standard output remains a compact JSON object so shell scripts and CI
    wrappers can parse command results without removing logging prefixes.
    """
    sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True))
    sys.stdout.write("\n")
