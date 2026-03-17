"""Tests for the `moviemetadb` CLI."""

import io
import json
import sys
import unittest
from pathlib import Path

from moviemetadb.cli import add_movie, list_movies


class CliTest(unittest.TestCase):
    def test_add_and_list_movie(self):
        tmp_dir = Path(__file__).resolve().parent / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        db_path = tmp_dir / "movies.json"

        # Add a movie
        args = type("A", (), {"title": "Inception", "year": 2010, "rating": 8.8, "db": db_path})
        self.assertEqual(add_movie(args), 0)

        # Validate file created
        data = json.loads(db_path.read_text(encoding="utf-8"))
        self.assertEqual(data[0]["title"], "Inception")

        # List movies and capture output
        args2 = type("B", (), {"db": db_path})
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.assertEqual(list_movies(args2), 0)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        self.assertIn("Inception (2010)", output)


if __name__ == "__main__":
    unittest.main()
