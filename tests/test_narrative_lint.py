"""Regression tests for clean public narrative linting."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ucbs.verification.narrative_lint import check_narrative_lint


class NarrativeLintTests(unittest.TestCase):
    """Check that public prose avoids internal development wording."""

    def test_theorem_ready_prose_is_rejected(self) -> None:
        """Public prose must not use internal status wording."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("This is a theorem-ready package.\n", encoding="utf-8")
            rows = check_narrative_lint(root)
            self.assertTrue(any(row.get("issue") == "internal theorem-ready wording" for row in rows))

    def test_inline_code_is_ignored_for_raw_field_names(self) -> None:
        """Raw field names in inline code are treated as provenance labels."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("Raw field `theorem_ready` is provenance only.\n", encoding="utf-8")
            rows = check_narrative_lint(root)
            self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
