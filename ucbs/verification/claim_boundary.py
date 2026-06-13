"""Claim-boundary checks for public repository text."""
from __future__ import annotations

import re
from pathlib import Path

FORBIDDEN: list[re.Pattern[str]] = [
    re.compile(r"\bsolves?\s+the\s+(full\s+)?Lebesgue\s+universal\s+cover\s+problem\b", re.I),
    re.compile(r"\b(full\s+)?Lebesgue\s+universal\s+cover\s+problem\s+(is\s+)?(solved|resolved)\b", re.I),
    re.compile(r"\bunrestricted\s+nonconvex\s+lower\s+bound\s+(is\s+)?(proved|established|completed)\b", re.I),
    re.compile(r"\bnonconvex\s+lower\s+bound\s+(is\s+)?(proved|established|completed)\b", re.I),
    re.compile(r"\bbranch[- ]a\s+(is\s+)?closed\b", re.I),
    re.compile(r"\bproof[- ]assistant\s+formalization\s+(is\s+)?(completed|done|proved)\b", re.I),
    re.compile(r"\bindependent\s+external\s+verification\s+(is\s+)?(completed|done)\b", re.I),
    re.compile(r"\u89e3\u51b3.*\u975e\u51f8"),
    re.compile(r"\u975e\u51f8.*\u4e0b\u754c.*(\u8bc1\u660e|\u5b8c\u6210|\u89e3\u51b3)"),
    re.compile(r"Branch[- ]?A.*(\u95ed\u5408|\u5b8c\u6210)"),
    re.compile(r"\u5916\u90e8.*\u72ec\u7acb.*\u9a8c\u8bc1.*\u5b8c\u6210"),
    re.compile(r"\u5f62\u5f0f\u5316.*\u8bc1\u660e.*\u5b8c\u6210"),
    re.compile(r"\u5b8c\u6574.*Lebesgue.*\u4e07\u6709\u8986\u76d6.*(\u89e3\u51b3|\u5b8c\u6210)"),
    re.compile(r"\u5b8c\u6574.*\u52d2\u8d1d\u683c.*\u4e07\u6709\u8986\u76d6.*(\u89e3\u51b3|\u5b8c\u6210)"),
]

NEGATION_MARKERS = [
    "does not claim",
    "does not assert",
    "not claimed",
    "not assert",
    "not a claim",
    "no claim",
    "do not",
    "neither",
    "remain false",
    "\u4e0d\u58f0\u79f0",
    "\u6ca1\u6709",
    "\u5e76\u975e",
    "\u4e0d\u662f",
    "\u4e0d\u4e3b\u5f20",
    "\u4e0d\u5ba3\u79f0",
    "\u662f\u5426",
]


def checked_text_files(root: Path) -> list[Path]:
    """Return text files whose public claims should be linted."""
    paths = [root / "README.md", root / "README.zh-CN.md"]
    for folder in [root / "docs", root / "certificate" / "public"]:
        if folder.exists():
            paths.extend(folder.rglob("*.md"))
    return sorted(path for path in paths if path.exists())


def _is_negated_context(line: str) -> bool:
    """Return whether a line is explicitly recording a non-claim."""
    lower = line.lower()
    return any(marker in lower for marker in NEGATION_MARKERS) or any(marker in line for marker in NEGATION_MARKERS)


def check_claim_boundary(root: Path) -> list[dict[str, object]]:
    """Return forbidden public-claim matches found in repository text.

    The linter is claim-oriented.  It ignores lines that explicitly state a
    non-claim, so the repository can safely document its scope boundaries.
    """
    rows: list[dict[str, object]] = []
    for path in checked_text_files(root):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        offset = 0
        for line_number, line in enumerate(lines, start=1):
            if _is_negated_context(line):
                offset += len(line) + 1
                continue
            for pattern in FORBIDDEN:
                for match in pattern.finditer(line):
                    rows.append({
                        "check": "claim_boundary",
                        "file": str(path.relative_to(root)),
                        "line": line_number,
                        "match": match.group(0),
                        "position": offset + match.start(),
                        "passed": False,
                        "summary": "forbidden public-claim pattern found",
                    })
            offset += len(line) + 1
    return rows
