"""Storage backends for MoviemetaDb."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional, Union

from . import Movie


class MovieNotFoundError(ValueError):
    pass


class JsonMovieStore:
    """A simple JSON-backed movie store."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _read(self) -> List[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: List[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list(self) -> List[Movie]:
        return [Movie(**d) for d in self._read()]

    def add(self, movie: Movie) -> None:
        movies = self._read()
        movies.append(asdict(movie))
        self._write(movies)

    def remove(self, title: str, year: Optional[int] = None) -> Movie:
        """Remove a movie by title (and optional year). Returns the removed movie."""
        title_norm = title.strip().lower()
        movies = self._read()
        remaining: List[dict] = []
        removed: Optional[dict] = None
        for entry in movies:
            if entry.get("title", "").strip().lower() == title_norm:
                if year is None or entry.get("year") == year:
                    if removed is None:
                        removed = entry
                        continue
            remaining.append(entry)

        if removed is None:
            raise MovieNotFoundError(f"Movie not found: {title} ({year if year else 'any year'})")

        self._write(remaining)
        return Movie(**removed)

    def search(self, query: str) -> List[Movie]:
        q = query.strip().lower()
        return [Movie(**d) for d in self._read() if q in d.get("title", "").lower()]

    def update_rating(self, title: str, year: int, rating: float) -> Movie:
        """Update rating for a specific title+year."""
        title_norm = title.strip().lower()
        movies = self._read()
        updated: Optional[dict] = None
        for entry in movies:
            if entry.get("title", "").strip().lower() == title_norm and entry.get("year") == year:
                entry["rating"] = rating
                updated = entry
                break

        if updated is None:
            raise MovieNotFoundError(f"Movie not found: {title} ({year})")

        self._write(movies)
        return Movie(**updated)


class SqliteMovieStore:
    """A SQLite-backed movie store."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path), isolation_level=None)

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    rating REAL NOT NULL DEFAULT 0.0,
                    UNIQUE(title, year)
                )
                """
            )

    def list(self) -> List[Movie]:
        with self._conn() as conn:
            cur = conn.execute("SELECT title, year, rating FROM movies ORDER BY title")
            return [Movie(title=row[0], year=row[1], rating=row[2]) for row in cur.fetchall()]

    def add(self, movie: Movie) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO movies (title, year, rating)
                VALUES (?, ?, ?)
                ON CONFLICT(title, year) DO UPDATE SET rating = excluded.rating
                """,
                (movie.title, movie.year, movie.rating),
            )

    def remove(self, title: str, year: Optional[int] = None) -> Movie:
        stmt = "SELECT id, title, year, rating FROM movies WHERE LOWER(title) = LOWER(?)"
        params: List[Union[str, int]] = [title]
        if year is not None:
            stmt += " AND year = ?"
            params.append(year)

        with self._conn() as conn:
            cur = conn.execute(stmt, params)
            row = cur.fetchone()
            if row is None:
                raise MovieNotFoundError(f"Movie not found: {title} ({year if year else 'any year'})")
            movie = Movie(title=row[1], year=row[2], rating=row[3])
            conn.execute("DELETE FROM movies WHERE id = ?", (row[0],))
            return movie

    def search(self, query: str) -> List[Movie]:
        q = f"%{query.strip().lower()}%"
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT title, year, rating FROM movies WHERE LOWER(title) LIKE ? ORDER BY title",
                (q,),
            )
            return [Movie(title=row[0], year=row[1], rating=row[2]) for row in cur.fetchall()]

    def update_rating(self, title: str, year: int, rating: float) -> Movie:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT id, title, year, rating FROM movies WHERE LOWER(title) = LOWER(?) AND year = ?",
                (title, year),
            )
            row = cur.fetchone()
            if row is None:
                raise MovieNotFoundError(f"Movie not found: {title} ({year})")
            conn.execute(
                "UPDATE movies SET rating = ? WHERE id = ?",
                (rating, row[0]),
            )
            return Movie(title=row[1], year=row[2], rating=rating)


def get_store(path: Path) -> Union[JsonMovieStore, SqliteMovieStore]:
    """Get the appropriate store based on the path extension."""
    if path.suffix in {".db", ".sqlite", ".sqlite3"}:
        return SqliteMovieStore(path)
    return JsonMovieStore(path)


__all__ = [
    "JsonMovieStore",
    "SqliteMovieStore",
    "MovieNotFoundError",
    "get_store",
]
