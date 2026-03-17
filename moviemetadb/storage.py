"""Storage backend for MoviemetaDb."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional

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


__all__ = ["JsonMovieStore", "MovieNotFoundError"]
