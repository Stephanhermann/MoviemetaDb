"""MoviemetaDb - movie metadata library."""

__version__ = "0.1.0"

from dataclasses import dataclass
from typing import Dict


@dataclass
class Movie:
    title: str
    year: int
    rating: float = 0.0


def normalize_title(title: str) -> str:
    """Normalize a movie title for consistent storage and lookup."""
    return title.strip().lower()


def to_dict(movie: Movie) -> Dict[str, object]:
    """Serialize a Movie to a simple dict."""
    return {"title": movie.title, "year": movie.year, "rating": movie.rating}
