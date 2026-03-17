"""Tests for the `moviemetadb` CLI."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from moviemetadb import __version__


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(__file__).resolve().parent / "tmp"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.db_path = self.tmp / "movies.db"

    def tearDown(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()

    def _run_cli(self, args: list[str]) -> str:
        """Run the installed `moviemetadb` CLI using the current Python environment."""
        # Use `python -m moviemetadb.cli` to avoid relying on console_scripts entrypoints in tests
        proc = subprocess.run(
            [sys.executable, "-m", "moviemetadb.cli", "--db", str(self.db_path)] + args,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
        return proc.stdout

    def test_add_list_search_remove_update(self):
        out = self._run_cli(["add", "Inception", "2010", "--rating", "8.8"])
        self.assertIn("Added Inception (2010)", out)

        out = self._run_cli(["list"])
        self.assertIn("Inception (2010)", out)

        out = self._run_cli(["search", "Inception"])
        self.assertIn("Inception (2010)", out)

        out = self._run_cli(["update-rating", "Inception", "2010", "9.2"])
        self.assertIn("Updated Inception (2010) rating to 9.2", out)

        out = self._run_cli(["remove", "Inception", "--year", "2010"])
        self.assertIn("Removed Inception (2010)", out)

        out = self._run_cli(["list"])
        self.assertIn("No movies found.", out)


if __name__ == "__main__":
    unittest.main()
