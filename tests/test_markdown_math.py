"""Regression tests for public Markdown math linting."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ucbs.verification.markdown_math import check_markdown_math


class MarkdownMathTests(unittest.TestCase):
    """Check that GitHub-unstable math syntax is rejected."""

    def test_parenthesized_tex_math_is_rejected(self) -> None:
        """The public README policy rejects ``\\(...\\)`` delimiters."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Bad math: \\(A(v)\\).\n", encoding="utf-8")
            rows = check_markdown_math(root)
            self.assertTrue(any(row.get("issue") == "non-GitHub inline math delimiter" for row in rows))

    def test_operatorname_in_fenced_math_is_rejected(self) -> None:
        """The public README policy rejects ``\\operatorname`` in math blocks."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("```math\n\\operatorname{area}(K)\n```\n", encoding="utf-8")
            rows = check_markdown_math(root)
            self.assertTrue(any("operatorname" in str(row.get("issue")) for row in rows))


if __name__ == "__main__":
    unittest.main()
