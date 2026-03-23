"""A minimal web API for MoviemetaDb."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

try:
    from fastapi import Depends, FastAPI, HTTPException, Security
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from pydantic import BaseModel
except ImportError as exc:
    raise ImportError(
        "FastAPI is not installed. Install with `pip install 'moviemetadb[web]'` to use the web API."
    ) from exc

from .storage import MovieNotFoundError, PhotoNotFoundError, get_store


class MovieIn(BaseModel):
    title: str
    year: int
    rating: float = 0.0
    file_path: str = ""
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    language: str = ""
    transcript: str = ""
    plot: str = ""
    preview_path: str = ""
    vision_model: str = ""
    whisper_model: str = ""
    analysed_at: str = ""


class PhotoIn(BaseModel):
    file_path: str
    width: int = 0
    height: int = 0
    taken_at: str = ""
    camera: str = ""
    description: str = ""
    tags: str = ""
    album: str = ""


app = FastAPI(title="MoviemetaDb API")

store = None

security = HTTPBearer(auto_error=False)


def _require_api_key(cred: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """Allow requests when no API key is configured, otherwise require Bearer token."""
    expected = os.getenv("MOVIEMETADB_API_KEY")
    if not expected:
        return True
    if not cred or cred.scheme.lower() != "bearer" or cred.credentials != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


def _get_store_instance() -> object:
    if store is None:
        raise RuntimeError("Movie store not configured")
    return store


@app.on_event("startup")
def _startup() -> None:
    global store
    store = get_store(os.getenv("MOVIEMETADB_DATABASE_URL", "moviemetadb.db"))


@app.get("/")
def root() -> dict:
    return {
        "name": "MoviemetaDb API",
        "status": "ok",
        "docs": "/docs",
        "movies": "/movies",
    }


@app.get("/movies", dependencies=[Depends(_require_api_key)])
def list_movies(
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    sort: str = "title",
    limit: Optional[int] = None,
) -> List[MovieIn]:
    return _get_store_instance().list(
        min_year=min_year,
        max_year=max_year,
        min_rating=min_rating,
        max_rating=max_rating,
        sort=sort,
        limit=limit,
    )


@app.get("/movie", dependencies=[Depends(_require_api_key)])
def list_movies_alias(
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    sort: str = "title",
    limit: Optional[int] = None,
) -> List[MovieIn]:
    return list_movies(min_year, max_year, min_rating, max_rating, sort, limit)


@app.post("/movies", status_code=201, dependencies=[Depends(_require_api_key)])
def create_movie(movie: MovieIn) -> MovieIn:
    from . import Movie as MovieModel
    payload = movie.model_dump() if hasattr(movie, "model_dump") else movie.dict()
    _get_store_instance().add(MovieModel(**payload))
    return movie


@app.post("/movie", status_code=201, dependencies=[Depends(_require_api_key)])
def create_movie_alias(movie: MovieIn) -> MovieIn:
    return create_movie(movie)


@app.get("/movies/search", dependencies=[Depends(_require_api_key)])
def search_movies(
    q: str,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    sort: str = "title",
    limit: Optional[int] = None,
) -> List[MovieIn]:
    return _get_store_instance().search(
        q,
        min_year=min_year,
        max_year=max_year,
        min_rating=min_rating,
        max_rating=max_rating,
        sort=sort,
        limit=limit,
    )


@app.delete("/movies", dependencies=[Depends(_require_api_key)])
def delete_movie(title: str, year: Optional[int] = None) -> MovieIn:
    try:
        removed = _get_store_instance().remove(title, year)
        return removed
    except MovieNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/movie", dependencies=[Depends(_require_api_key)])
def delete_movie_alias(title: str, year: Optional[int] = None) -> MovieIn:
    return delete_movie(title, year)


# ── Photo endpoints ─────────────────────────────────────────────────────────

@app.get("/photos", dependencies=[Depends(_require_api_key)])
def list_photos(
    album: Optional[str] = None,
    sort: str = "file_path",
    limit: Optional[int] = None,
) -> List[PhotoIn]:
    return _get_store_instance().list_photos(album=album, sort=sort, limit=limit)


@app.get("/photo", dependencies=[Depends(_require_api_key)])
def list_photos_alias(
    album: Optional[str] = None,
    sort: str = "file_path",
    limit: Optional[int] = None,
) -> List[PhotoIn]:
    return list_photos(album=album, sort=sort, limit=limit)


@app.post("/photos", status_code=201, dependencies=[Depends(_require_api_key)])
def create_photo(photo: PhotoIn) -> PhotoIn:
    from . import Photo as PhotoModel
    payload = photo.model_dump() if hasattr(photo, "model_dump") else photo.dict()
    _get_store_instance().add_photo(PhotoModel(**payload))
    return photo


@app.post("/photo", status_code=201, dependencies=[Depends(_require_api_key)])
def create_photo_alias(photo: PhotoIn) -> PhotoIn:
    return create_photo(photo)


@app.get("/photos/search", dependencies=[Depends(_require_api_key)])
def search_photos(
    q: str,
    album: Optional[str] = None,
    sort: str = "file_path",
    limit: Optional[int] = None,
) -> List[PhotoIn]:
    return _get_store_instance().search_photos(q, album=album, sort=sort, limit=limit)


@app.delete("/photos", dependencies=[Depends(_require_api_key)])
def delete_photo(file_path: str) -> PhotoIn:
    try:
        removed = _get_store_instance().remove_photo(file_path)
        return removed
    except PhotoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/photo", dependencies=[Depends(_require_api_key)])
def delete_photo_alias(file_path: str) -> PhotoIn:
    return delete_photo(file_path)
