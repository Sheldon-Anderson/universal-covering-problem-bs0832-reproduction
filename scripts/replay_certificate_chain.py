#!/usr/bin/env python3
"""Command-line entry point for ``ucbs.cli.replay_certificate_chain``."""
from __future__ import annotations

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from ucbs.cli.replay_certificate_chain import main


if __name__ == "__main__":
    raise SystemExit(main())
