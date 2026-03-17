"""Storage backends for MoviemetaDb."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional, Union

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

    def list(
        self,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        sort: str = "title",
        limit: Optional[int] = None,
    ) -> List[Movie]:
        movies = [Movie(**d) for d in self._read()]

        if min_year is not None:
            movies = [m for m in movies if m.year >= min_year]
        if max_year is not None:
            movies = [m for m in movies if m.year <= max_year]
        if min_rating is not None:
            movies = [m for m in movies if m.rating >= min_rating]
        if max_rating is not None:
            movies = [m for m in movies if m.rating <= max_rating]

        movies.sort(key=lambda m: getattr(m, sort))
        if limit is not None:
            movies = movies[:limit]
        return movies

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

    def search(
        self,
        query: str,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        sort: str = "title",
        limit: Optional[int] = None,
    ) -> List[Movie]:
        q = query.strip().lower()
        movies = [Movie(**d) for d in self._read() if q in d.get("title", "").lower()]

        if min_year is not None:
            movies = [m for m in movies if m.year >= min_year]
        if max_year is not None:
            movies = [m for m in movies if m.year <= max_year]
        if min_rating is not None:
            movies = [m for m in movies if m.rating >= min_rating]
        if max_rating is not None:
            movies = [m for m in movies if m.rating <= max_rating]

        movies.sort(key=lambda m: getattr(m, sort))
        if limit is not None:
            movies = movies[:limit]
        return movies

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


try:
    from sqlalchemy import (
        Column,
        Float,
        Integer,
        String,
        create_engine,
        select,
        update as sqlalchemy_update,
        delete as sqlalchemy_delete,
    )
    from sqlalchemy.exc import NoResultFound
    from sqlalchemy.orm import declarative_base, Session

    SQLALCHEMY_AVAILABLE = True
except ImportError as exc:
    SQLALCHEMY_AVAILABLE = False
    _sqlalchemy_import_error = exc


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()


    class MovieRow(Base):
        __tablename__ = "movies"
        id = Column(Integer, primary_key=True)
        title = Column(String, nullable=False)
        year = Column(Integer, nullable=False)
        rating = Column(Float, nullable=False, default=0.0)

        __table_args__ = {"sqlite_autoincrement": True}


    class SqlAlchemyMovieStore:
        """A SQLAlchemy-backed movie store (SQLite/PostgreSQL)."""

        def __init__(self, url: str) -> None:
            if not SQLALCHEMY_AVAILABLE:
                raise RuntimeError(
                    "SQLAlchemy is not installed. Install with `pip install 'moviemetadb[db]'`"
                )
            self.engine = create_engine(url, future=True)
            Base.metadata.create_all(self.engine)

        def _session(self) -> Session:
            return Session(self.engine)

        def _apply_filters(
            self,
            stmt,
            min_year: Optional[int],
            max_year: Optional[int],
            min_rating: Optional[float],
            max_rating: Optional[float],
        ):
            if min_year is not None:
                stmt = stmt.where(MovieRow.year >= min_year)
            if max_year is not None:
                stmt = stmt.where(MovieRow.year <= max_year)
            if min_rating is not None:
                stmt = stmt.where(MovieRow.rating >= min_rating)
            if max_rating is not None:
                stmt = stmt.where(MovieRow.rating <= max_rating)
            return stmt

        def list(
            self,
            min_year: Optional[int] = None,
            max_year: Optional[int] = None,
            min_rating: Optional[float] = None,
            max_rating: Optional[float] = None,
            sort: str = "title",
            limit: Optional[int] = None,
        ) -> List[Movie]:
            stmt = select(MovieRow)
            stmt = self._apply_filters(stmt, min_year, max_year, min_rating, max_rating)

            order_col = {
                "title": MovieRow.title,
                "year": MovieRow.year,
                "rating": MovieRow.rating,
            }.get(sort, MovieRow.title)

            stmt = stmt.order_by(order_col)
            if limit is not None:
                stmt = stmt.limit(limit)

            with self._session() as session:
                rows = session.execute(stmt).scalars().all()
                return [Movie(title=r.title, year=r.year, rating=r.rating) for r in rows]

        def add(self, movie: Movie) -> None:
            with self._session() as session:
                existing = (
                    session.execute(
                        select(MovieRow)
                        .where(MovieRow.title == movie.title)
                        .where(MovieRow.year == movie.year)
                    )
                    .scalars()
                    .first()
                )
                if existing:
                    existing.rating = movie.rating
                else:
                    session.add(MovieRow(title=movie.title, year=movie.year, rating=movie.rating))
                session.commit()

        def remove(self, title: str, year: Optional[int] = None) -> Movie:
            stmt = select(MovieRow).where(MovieRow.title.ilike(title))
            if year is not None:
                stmt = stmt.where(MovieRow.year == year)
            with self._session() as session:
                row = session.execute(stmt).scalars().first()
                if row is None:
                    raise MovieNotFoundError(f"Movie not found: {title} ({year if year else 'any year'})")
                movie = Movie(title=row.title, year=row.year, rating=row.rating)
                session.execute(sqlalchemy_delete(MovieRow).where(MovieRow.id == row.id))
                session.commit()
                return movie

        def search(
            self,
            query: str,
            min_year: Optional[int] = None,
            max_year: Optional[int] = None,
            min_rating: Optional[float] = None,
            max_rating: Optional[float] = None,
            sort: str = "title",
            limit: Optional[int] = None,
        ) -> List[Movie]:
            q = f"%{query.strip().lower()}%"
            stmt = select(MovieRow).where(MovieRow.title.ilike(q))
            stmt = self._apply_filters(stmt, min_year, max_year, min_rating, max_rating)

            order_col = {
                "title": MovieRow.title,
                "year": MovieRow.year,
                "rating": MovieRow.rating,
            }.get(sort, MovieRow.title)

            stmt = stmt.order_by(order_col)
            if limit is not None:
                stmt = stmt.limit(limit)

            with self._session() as session:
                rows = session.execute(stmt).scalars().all()
                return [Movie(title=r.title, year=r.year, rating=r.rating) for r in rows]

        def update_rating(self, title: str, year: int, rating: float) -> Movie:
            with self._session() as session:
                row = (
                    session.execute(
                        select(MovieRow)
                        .where(MovieRow.title.ilike(title))
                        .where(MovieRow.year == year)
                    )
                    .scalars()
                    .first()
                )
                if row is None:
                    raise MovieNotFoundError(f"Movie not found: {title} ({year})")
                row.rating = rating
                session.commit()
                return Movie(title=row.title, year=row.year, rating=row.rating)


def get_store(path: Union[Path, str]) -> Union[JsonMovieStore, "SqlAlchemyMovieStore"]:
    """Get the appropriate store.

    The database may be:
    - a JSON file (`*.json`)
    - a sqlite file (`*.db`, `*.sqlite`, `*.sqlite3`) (uses SQLAlchemy)
    - a full SQLAlchemy URL (e.g., `postgresql://...` or `sqlite:///...`)
    """

    if isinstance(path, Path):
        path = str(path)

    # Use env override if provided
    path = os.getenv("MOVIEMETADB_DATABASE_URL", path)

    if path.lower().endswith(".json"):
        return JsonMovieStore(Path(path))

    # Treat as SQLAlchemy URL (SQLite or Postgres)
    if not SQLALCHEMY_AVAILABLE:
        raise RuntimeError(
            "SQLAlchemy is required for database storage. Install with `pip install 'moviemetadb[db]'`."
        )

    if path.startswith("sqlite://") or path.startswith("postgresql://") or path.startswith("postgres://"):
        return SqlAlchemyMovieStore(path)

    # Treat as path to local sqlite file
    return SqlAlchemyMovieStore(f"sqlite:///{Path(path).expanduser().resolve()}")


__all__ = [
    "JsonMovieStore",
    "MovieNotFoundError",
    "get_store",
]
