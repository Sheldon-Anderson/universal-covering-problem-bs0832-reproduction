"""Regression tests for shared certificate validation helpers."""
from __future__ import annotations

import unittest

from ucbs.certificate.validation import require_columns, require_unique_keys


class CertificateValidationTests(unittest.TestCase):
    """Check validation helpers that guard against malformed diagnostics."""

    def test_empty_table_fails_schema(self) -> None:
        """An empty table must not satisfy a required-column schema."""
        rows = require_columns([], {"id"}, "sample")
        self.assertFalse(rows[0]["passed"])

    def test_duplicate_keys_are_detected(self) -> None:
        """Duplicate composite keys must be reported as validation failures."""
        rows = [{"id": "a"}, {"id": "a"}]
        diag = require_unique_keys(rows, ["id"], "sample")
        self.assertFalse(diag["passed"])


if __name__ == "__main__":
    unittest.main()
