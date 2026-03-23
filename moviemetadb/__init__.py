"""MoviemetaDb - movie metadata library."""

__version__ = "0.2.0"

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Movie:
    title: str
    year: int
    rating: float = 0.0
    # Video file metadata
    file_path: str = ""
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    # Analysis results
    language: str = ""
    transcript: str = ""
    plot: str = ""
    preview_path: str = ""
    vision_model: str = ""
    whisper_model: str = ""
    analysed_at: str = ""


def normalize_title(title: str) -> str:
    """Normalize a movie title for consistent storage and lookup."""
    return title.strip().lower()


def to_dict(movie: Movie) -> Dict[str, object]:
    """Serialize a Movie to a simple dict."""
    return asdict(movie)
