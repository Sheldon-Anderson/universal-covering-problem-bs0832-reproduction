"""Clean-story checks for public Markdown and certificate notes."""
from __future__ import annotations

import re
from pathlib import Path

INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")

FORBIDDEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\blegacy\b", re.I), "legacy storyline wording"),
    (re.compile(r"\breproduction\b", re.I), "reproduction storyline wording"),
    (re.compile(r"\bbaseline\b", re.I), "baseline storyline wording"),
    (re.compile(r"\binherited\b", re.I), "inherited-component storyline wording"),
    (re.compile(r"\bold\s+(replay|certificate|threshold|project)\b", re.I), "old-certificate storyline wording"),
    (re.compile(r"\bprevious\s+(certificate|threshold|project|reproduction)\b", re.I), "previous-certificate storyline wording"),
    (re.compile(r"\bbs[-_]?0832\b", re.I), "BS0832 storyline label"),
    (re.compile(r"\btarget_083201\b", re.I), "threshold-specific directory name"),
    (re.compile(r"\bproof-ready\b", re.I), "nonstandard proof-ready wording"),
    (re.compile(r"\btheorem-ready\b", re.I), "internal theorem-ready wording"),
    (re.compile(r"\bkernel\b", re.I), "code-flavored kernel wording"),
    (re.compile(r"verify_theorem_ready\.py", re.I), "removed command name"),
    (re.compile(r"replay_inner_witness_certificate\.py", re.I), "removed command name"),
]


def checked_text_files(root: Path) -> list[Path]:
    """Return public text files checked for the clean certificate narrative."""
    paths = [root / "README.md", root / "README.zh-CN.md"]
    for folder in [root / "docs", root / "certificate" / "public"]:
        if folder.exists():
            paths.extend(folder.rglob("*.md"))
    return sorted(path for path in paths if path.exists())


def _strip_fenced_code(text: str) -> str:
    """Remove fenced code blocks and inline code from narrative checks."""
    stripped = re.sub(r"```.*?```", lambda match: "\n" * match.group(0).count("\n"), text, flags=re.DOTALL)
    return INLINE_CODE_PATTERN.sub(lambda match: " " * len(match.group(0)), stripped)


def check_narrative_lint(root: Path) -> list[dict[str, object]]:
    """Return forbidden wording found in public text."""
    rows: list[dict[str, object]] = []
    for path in checked_text_files(root):
        text = _strip_fenced_code(path.read_text(encoding="utf-8", errors="replace"))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern, issue in FORBIDDEN_PATTERNS:
                for match in pattern.finditer(line):
                    rows.append({
                        "check": "narrative_lint",
                        "file": str(path.relative_to(root)),
                        "line": line_number,
                        "issue": issue,
                        "fragment": match.group(0),
                        "passed": False,
                        "summary": "forbidden public wording found",
                    })
    return rows
