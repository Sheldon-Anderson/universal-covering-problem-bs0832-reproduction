"""Smoke tests for public command-line entry points."""
from __future__ import annotations

import subprocess
import sys
import unittest


class CliHelpTests(unittest.TestCase):
    """Ensure core public scripts expose working help screens."""

    def test_verify_certificate_help(self) -> None:
        """The main certificate verifier must provide ``--root`` help."""
        proc = subprocess.run([sys.executable, "scripts/verify_certificate.py", "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("--root", proc.stdout)

    def test_check_repository_help(self) -> None:
        """The repository checker must provide ``--log-level`` help."""
        proc = subprocess.run([sys.executable, "scripts/check_repository.py", "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("--log-level", proc.stdout)


if __name__ == "__main__":
    unittest.main()
