"""Markdown math rendering checks for README and public documentation files."""
from __future__ import annotations

import re
from pathlib import Path

BAD_TEXT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\\\([^\n]*?\\\)"), "non-GitHub inline math delimiter"),
    (re.compile(r"\\\[[\s\S]*?\\\]"), "non-GitHub display math delimiter"),
    (re.compile(r"\$\$"), "display math should use fenced math block"),
    (re.compile(r"\$`"), "backtick math marker"),
    (re.compile(r"`\$"), "backtick math marker"),
    (re.compile(r"\bOmega_(adm|B|r)\b"), "plain-text Omega symbol"),
    (re.compile(r"\balpha_cvx\b"), "plain-text alpha symbol"),
    (re.compile(r"\bconv\s+Q\b"), "plain-text convex hull expression"),
    (re.compile(r"\bunion_r\b"), "plain-text union expression"),
    (re.compile(r"(?<!\\)\bsubset\b"), "plain-text subset relation"),
]

BAD_MATH_BLOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\\operatorname\b"), "operatorname is not GitHub-safe in README math"),
    (re.compile(r"\$\$"), "nested display math marker inside fenced math block"),
    (re.compile(r"\\mathcal\s+[A-Za-z]"), "mathcal should use braces in README math"),
    (re.compile(r"\\mathrm\{[^}]*\s+[^}]*\}"), "mathrm should not contain spaced letters in README math"),
]

FENCE_PATTERN = re.compile(r"(^```([^\n`]*)\n)(.*?)(^```\s*$)", re.DOTALL | re.MULTILINE)
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")


def markdown_files(root: Path) -> list[Path]:
    """Return public Markdown files checked by the repository audit."""
    candidates = [root / "README.md", root / "README.zh-CN.md"]
    for folder in [root / "docs", root / "certificate" / "public"]:
        if folder.exists():
            candidates.extend(folder.rglob("*.md"))
    return sorted(path for path in candidates if path.exists())


def _line_number(text: str, position: int) -> int:
    """Return the one-based line number for a character offset."""
    return text.count("\n", 0, position) + 1


def _blank_span(text: str, start: int, end: int) -> str:
    """Return whitespace preserving line count for a removed span."""
    span = text[start:end]
    return "\n" * span.count("\n") + " " * (len(span) - span.count("\n"))


def _strip_non_text_regions(text: str) -> str:
    """Remove fenced blocks and inline code while preserving line numbering."""
    pieces: list[str] = []
    last = 0
    for match in FENCE_PATTERN.finditer(text):
        pieces.append(text[last:match.start()])
        pieces.append(_blank_span(text, match.start(), match.end()))
        last = match.end()
    pieces.append(text[last:])
    stripped = "".join(pieces)
    return INLINE_CODE_PATTERN.sub(lambda match: " " * len(match.group(0)), stripped)


def _math_block_rows(path: Path, root: Path, text: str) -> list[dict[str, object]]:
    """Check fenced math blocks for GitHub-safe math syntax."""
    rows: list[dict[str, object]] = []
    for fence in FENCE_PATTERN.finditer(text):
        language = fence.group(2).strip().lower()
        if language != "math":
            continue
        body = fence.group(3)
        body_start = fence.start(3)
        for pattern, label in BAD_MATH_BLOCK_PATTERNS:
            for match in pattern.finditer(body):
                rows.append({
                    "check": "readme_math",
                    "file": str(path.relative_to(root)),
                    "line": _line_number(text, body_start + match.start()),
                    "issue": label,
                    "fragment": match.group(0),
                    "position": body_start + match.start(),
                    "passed": False,
                    "summary": "markdown math lint issue found",
                })
    return rows


def check_markdown_math(root: Path) -> list[dict[str, object]]:
    """Detect mathematical fragments that are likely not rendered by GitHub."""
    rows: list[dict[str, object]] = []
    for path in markdown_files(root):
        original = path.read_text(encoding="utf-8", errors="replace")
        rows.extend(_math_block_rows(path, root, original))
        text = _strip_non_text_regions(original)
        for pattern, label in BAD_TEXT_PATTERNS:
            for match in pattern.finditer(text):
                rows.append({
                    "check": "readme_math",
                    "file": str(path.relative_to(root)),
                    "line": _line_number(original, match.start()),
                    "issue": label,
                    "fragment": match.group(0),
                    "position": match.start(),
                    "passed": False,
                    "summary": "markdown math lint issue found",
                })
    return rows
