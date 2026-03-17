"""A minimal web API for MoviemetaDb."""

from __future__ import annotations

from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:
    raise ImportError(
        "FastAPI is not installed. Install with `pip install 'moviemetadb[web]'` to use the web API."
    ) from exc

from .storage import JsonMovieStore, MovieNotFoundError


class MovieIn(BaseModel):
    title: str
    year: int
    rating: float = 0.0


app = FastAPI(title="MoviemetaDb API")

store: JsonMovieStore | None = None


def get_store() -> JsonMovieStore:
    if store is None:
        raise RuntimeError("Movie store not configured")
    return store


@app.on_event("startup")
def _startup() -> None:
    global store
    store = JsonMovieStore(Path("moviemetadb.json"))


@app.get("/movies")
def list_movies() -> list[MovieIn]:
    return get_store().list()


@app.post("/movies", status_code=201)
def create_movie(movie: MovieIn) -> MovieIn:
    get_store().add(movie)
    return movie


@app.get("/movies/search")
def search_movies(q: str) -> list[MovieIn]:
    return get_store().search(q)


@app.delete("/movies")
def delete_movie(title: str, year: int | None = None) -> MovieIn:
    try:
        removed = get_store().remove(title, year)
        return removed
    except MovieNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
