"""Command-line interface for MoviemetaDb."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import Movie, normalize_title, to_dict


DEFAULT_DB = Path("moviemetadb.json")


def load_db(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_db(path: Path, movies: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)


def add_movie(args: argparse.Namespace) -> int:
    movie = Movie(title=args.title, year=args.year, rating=args.rating)
    db = load_db(args.db)
    db.append(to_dict(movie))
    save_db(args.db, db)
    print(f"Added {movie.title} ({movie.year}) to {args.db}")
    return 0


def list_movies(args: argparse.Namespace) -> int:
    db = load_db(args.db)
    if not db:
        print("No movies found.")
        return 0

    for entry in db:
        print(f"- {entry['title']} ({entry['year']}) — rating: {entry.get('rating', 0)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="moviemetadb")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the movie metadata JSON database (default: moviemetadb.json)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a movie to the database")
    add.add_argument("title", type=str, help="Movie title")
    add.add_argument("year", type=int, help="Release year")
    add.add_argument("--rating", type=float, default=0.0, help="Movie rating")
    add.set_defaults(func=add_movie)

    list_cmd = sub.add_parser("list", help="List stored movies")
    list_cmd.set_defaults(func=list_movies)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
