"""Storage backends for MoviemetaDb."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional, Union

from . import Movie, Photo


class MovieNotFoundError(ValueError):
    pass


class PhotoNotFoundError(ValueError):
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

    # ── Photo methods ──────────────────────────────────────────────────────────

    @property
    def _photos_path(self) -> Path:
        return self.path.parent / (self.path.stem + ".photos.json")

    def _read_photos(self) -> List[dict]:
        if not self._photos_path.exists():
            return []
        with self._photos_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_photos(self, data: List[dict]) -> None:
        self._photos_path.parent.mkdir(parents=True, exist_ok=True)
        with self._photos_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_photo(self, photo: Photo) -> None:
        photos = self._read_photos()
        # upsert by file_path
        for i, entry in enumerate(photos):
            if entry.get("file_path") == photo.file_path:
                photos[i] = asdict(photo)
                self._write_photos(photos)
                return
        photos.append(asdict(photo))
        self._write_photos(photos)

    def list_photos(
        self,
        album: Optional[str] = None,
        sort: str = "file_path",
        limit: Optional[int] = None,
    ) -> List[Photo]:
        photos = [Photo(**d) for d in self._read_photos()]
        if album is not None:
            photos = [p for p in photos if p.album == album]
        try:
            photos.sort(key=lambda p: getattr(p, sort, "") or "")
        except Exception:
            pass
        if limit is not None:
            photos = photos[:limit]
        return photos

    def remove_photo(self, file_path: str) -> Photo:
        photos = self._read_photos()
        remaining: List[dict] = []
        removed: Optional[dict] = None
        for entry in photos:
            if entry.get("file_path") == file_path and removed is None:
                removed = entry
            else:
                remaining.append(entry)
        if removed is None:
            raise PhotoNotFoundError(f"Photo not found: {file_path}")
        self._write_photos(remaining)
        return Photo(**removed)

    def search_photos(
        self,
        query: str,
        album: Optional[str] = None,
        sort: str = "file_path",
        limit: Optional[int] = None,
    ) -> List[Photo]:
        q = query.strip().lower()
        photos = [
            Photo(**d)
            for d in self._read_photos()
            if q in (d.get("file_path") or "").lower()
            or q in (d.get("description") or "").lower()
            or q in (d.get("tags") or "").lower()
        ]
        if album is not None:
            photos = [p for p in photos if p.album == album]
        try:
            photos.sort(key=lambda p: getattr(p, sort, "") or "")
        except Exception:
            pass
        if limit is not None:
            photos = photos[:limit]
        return photos


try:
    from sqlalchemy import (
        Column,
        Float,
        Integer,
        String,
        Text,
        create_engine,
        select,
        text,
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
        file_path = Column(Text, nullable=True, default="")
        duration_seconds = Column(Float, nullable=True, default=0.0)
        width = Column(Integer, nullable=True, default=0)
        height = Column(Integer, nullable=True, default=0)
        fps = Column(Float, nullable=True, default=0.0)
        language = Column(String, nullable=True, default="")
        transcript = Column(Text, nullable=True, default="")
        plot = Column(Text, nullable=True, default="")
        preview_path = Column(String, nullable=True, default="")
        vision_model = Column(String, nullable=True, default="")
        whisper_model = Column(String, nullable=True, default="")
        analysed_at = Column(String, nullable=True, default="")

        __table_args__ = {"sqlite_autoincrement": True}


    class PhotoRow(Base):
        __tablename__ = "photos"
        id = Column(Integer, primary_key=True)
        file_path = Column(Text, nullable=False, default="")
        width = Column(Integer, nullable=True, default=0)
        height = Column(Integer, nullable=True, default=0)
        taken_at = Column(String, nullable=True, default="")
        camera = Column(String, nullable=True, default="")
        description = Column(Text, nullable=True, default="")
        tags = Column(Text, nullable=True, default="")
        album = Column(String, nullable=True, default="")

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
            self._migrate()
            self._migrate_photos()

        def _session(self) -> Session:
            return Session(self.engine)

        def _migrate(self) -> None:
            """Add any new columns to existing tables (forward migration)."""
            new_cols = [
                ("file_path", "TEXT DEFAULT ''"),
                ("duration_seconds", "REAL DEFAULT 0.0"),
                ("width", "INTEGER DEFAULT 0"),
                ("height", "INTEGER DEFAULT 0"),
                ("fps", "REAL DEFAULT 0.0"),
                ("language", "TEXT DEFAULT ''"),
                ("transcript", "TEXT DEFAULT ''"),
                ("plot", "TEXT DEFAULT ''"),
                ("preview_path", "TEXT DEFAULT ''"),
                ("vision_model", "TEXT DEFAULT ''"),
                ("whisper_model", "TEXT DEFAULT ''"),
                ("analysed_at", "TEXT DEFAULT ''"),
            ]
            with self.engine.connect() as conn:
                for col_name, col_def in new_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE movies ADD COLUMN {col_name} {col_def}"))
                        conn.commit()
                    except Exception:
                        pass  # Column already exists

        def _row_to_movie(self, r: "MovieRow") -> Movie:
            return Movie(
                title=r.title,
                year=r.year,
                rating=r.rating,
                file_path=r.file_path or "",
                duration_seconds=r.duration_seconds or 0.0,
                width=r.width or 0,
                height=r.height or 0,
                fps=r.fps or 0.0,
                language=r.language or "",
                transcript=r.transcript or "",
                plot=r.plot or "",
                preview_path=r.preview_path or "",
                vision_model=r.vision_model or "",
                whisper_model=r.whisper_model or "",
                analysed_at=r.analysed_at or "",
            )

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
                return [self._row_to_movie(r) for r in rows]

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
                    existing.file_path = getattr(movie, "file_path", "")
                    existing.duration_seconds = getattr(movie, "duration_seconds", 0.0)
                    existing.width = getattr(movie, "width", 0)
                    existing.height = getattr(movie, "height", 0)
                    existing.fps = getattr(movie, "fps", 0.0)
                    existing.language = getattr(movie, "language", "")
                    existing.transcript = getattr(movie, "transcript", "")
                    existing.plot = getattr(movie, "plot", "")
                    existing.preview_path = getattr(movie, "preview_path", "")
                    existing.vision_model = getattr(movie, "vision_model", "")
                    existing.whisper_model = getattr(movie, "whisper_model", "")
                    existing.analysed_at = getattr(movie, "analysed_at", "")
                else:
                    session.add(MovieRow(
                        title=movie.title,
                        year=movie.year,
                        rating=movie.rating,
                        file_path=getattr(movie, "file_path", ""),
                        duration_seconds=getattr(movie, "duration_seconds", 0.0),
                        width=getattr(movie, "width", 0),
                        height=getattr(movie, "height", 0),
                        fps=getattr(movie, "fps", 0.0),
                        language=getattr(movie, "language", ""),
                        transcript=getattr(movie, "transcript", ""),
                        plot=getattr(movie, "plot", ""),
                        preview_path=getattr(movie, "preview_path", ""),
                        vision_model=getattr(movie, "vision_model", ""),
                        whisper_model=getattr(movie, "whisper_model", ""),
                        analysed_at=getattr(movie, "analysed_at", ""),
                    ))
                session.commit()

        def remove(self, title: str, year: Optional[int] = None) -> Movie:
            stmt = select(MovieRow).where(MovieRow.title.ilike(title))
            if year is not None:
                stmt = stmt.where(MovieRow.year == year)
            with self._session() as session:
                row = session.execute(stmt).scalars().first()
                if row is None:
                    raise MovieNotFoundError(f"Movie not found: {title} ({year if year else 'any year'})")
                movie = self._row_to_movie(row)
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
                return [self._row_to_movie(r) for r in rows]

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
                return self._row_to_movie(row)

        # ── Photo methods ──────────────────────────────────────────────────────

        def _migrate_photos(self) -> None:
            """Add any new columns to photos table (forward migration)."""
            new_cols = [
                ("width", "INTEGER DEFAULT 0"),
                ("height", "INTEGER DEFAULT 0"),
                ("taken_at", "TEXT DEFAULT ''"),
                ("camera", "TEXT DEFAULT ''"),
                ("description", "TEXT DEFAULT ''"),
                ("tags", "TEXT DEFAULT ''"),
                ("album", "TEXT DEFAULT ''"),
            ]
            with self.engine.connect() as conn:
                for col_name, col_def in new_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE photos ADD COLUMN {col_name} {col_def}"))
                        conn.commit()
                    except Exception:
                        pass  # Column already exists

        def _row_to_photo(self, r: "PhotoRow") -> Photo:
            return Photo(
                file_path=r.file_path or "",
                width=r.width or 0,
                height=r.height or 0,
                taken_at=r.taken_at or "",
                camera=r.camera or "",
                description=r.description or "",
                tags=r.tags or "",
                album=r.album or "",
            )

        def add_photo(self, photo: Photo) -> None:
            with self._session() as session:
                existing = (
                    session.execute(
                        select(PhotoRow).where(PhotoRow.file_path == photo.file_path)
                    )
                    .scalars()
                    .first()
                )
                if existing:
                    existing.width = photo.width
                    existing.height = photo.height
                    existing.taken_at = photo.taken_at
                    existing.camera = photo.camera
                    existing.description = photo.description
                    existing.tags = photo.tags
                    existing.album = photo.album
                else:
                    session.add(PhotoRow(
                        file_path=photo.file_path,
                        width=photo.width,
                        height=photo.height,
                        taken_at=photo.taken_at,
                        camera=photo.camera,
                        description=photo.description,
                        tags=photo.tags,
                        album=photo.album,
                    ))
                session.commit()

        def list_photos(
            self,
            album: Optional[str] = None,
            sort: str = "file_path",
            limit: Optional[int] = None,
        ) -> List[Photo]:
            stmt = select(PhotoRow)
            if album is not None:
                stmt = stmt.where(PhotoRow.album == album)
            order_col = {
                "file_path": PhotoRow.file_path,
                "taken_at": PhotoRow.taken_at,
                "album": PhotoRow.album,
            }.get(sort, PhotoRow.file_path)
            stmt = stmt.order_by(order_col)
            if limit is not None:
                stmt = stmt.limit(limit)
            with self._session() as session:
                rows = session.execute(stmt).scalars().all()
                return [self._row_to_photo(r) for r in rows]

        def remove_photo(self, file_path: str) -> Photo:
            with self._session() as session:
                row = (
                    session.execute(
                        select(PhotoRow).where(PhotoRow.file_path == file_path)
                    )
                    .scalars()
                    .first()
                )
                if row is None:
                    raise PhotoNotFoundError(f"Photo not found: {file_path}")
                photo = self._row_to_photo(row)
                session.execute(sqlalchemy_delete(PhotoRow).where(PhotoRow.id == row.id))
                session.commit()
                return photo

        def search_photos(
            self,
            query: str,
            album: Optional[str] = None,
            sort: str = "file_path",
            limit: Optional[int] = None,
        ) -> List[Photo]:
            q = f"%{query.strip()}%"
            stmt = select(PhotoRow).where(
                PhotoRow.file_path.ilike(q)
                | PhotoRow.description.ilike(q)
                | PhotoRow.tags.ilike(q)
            )
            if album is not None:
                stmt = stmt.where(PhotoRow.album == album)
            order_col = {
                "file_path": PhotoRow.file_path,
                "taken_at": PhotoRow.taken_at,
                "album": PhotoRow.album,
            }.get(sort, PhotoRow.file_path)
            stmt = stmt.order_by(order_col)
            if limit is not None:
                stmt = stmt.limit(limit)
            with self._session() as session:
                rows = session.execute(stmt).scalars().all()
                return [self._row_to_photo(r) for r in rows]


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
    "PhotoNotFoundError",
    "get_store",
]
