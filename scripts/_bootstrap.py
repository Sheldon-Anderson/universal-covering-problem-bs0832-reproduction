#!/usr/bin/env python3
"""Bootstrap direct script execution from an unpacked source tree.

Editable installation and console scripts do not use this helper. It exists
only so commands such as ``python scripts/verify_certificate.py`` work before
the package is installed. The helper is intentionally confined to ``scripts/``;
package modules under ``ucbs/`` never modify ``sys.path``.
"""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_repo_root_on_path() -> None:
    """Make the repository root importable for direct script execution."""
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
