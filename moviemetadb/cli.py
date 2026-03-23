"""Command-line interface for MoviemetaDb."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import Movie
from .storage import MovieNotFoundError, get_store


DEFAULT_DB = "moviemetadb.db"


def _run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="moviemetadb")
    parser.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB,
        help=(
            "Database to use (SQLite file by default). "
            "You can also specify a JSON file ("".json"") or a full SQLAlchemy URL "
            "(e.g., postgresql://user:pass@host:5432/db)."
        ),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a movie to the database")
    add.add_argument("title", type=str, help="Movie title")
    add.add_argument("year", type=int, help="Release year")
    add.add_argument("--rating", type=float, default=0.0, help="Movie rating")
    add.add_argument("--plot", type=str, default="", help="Plot / description")
    add.add_argument("--file-path", type=str, default="", help="Path to video file")
    add.add_argument("--duration", type=float, default=0.0, help="Duration in seconds")
    add.add_argument("--language", type=str, default="", help="Language (e.g. de, en)")
    add.add_argument("--preview-path", type=str, default="", help="Path to preview image")
    add.set_defaults(func=_cmd_add)

    list_cmd = sub.add_parser("list", help="List stored movies")
    list_cmd.add_argument("--sort", choices=["title", "year", "rating"], default="title")
    list_cmd.add_argument("--min-year", type=int, help="Filter by minimum release year")
    list_cmd.add_argument("--max-year", type=int, help="Filter by maximum release year")
    list_cmd.add_argument("--min-rating", type=float, help="Filter by minimum rating")
    list_cmd.add_argument("--max-rating", type=float, help="Filter by maximum rating")
    list_cmd.add_argument("--limit", type=int, help="Limit number of results")
    list_cmd.set_defaults(func=_cmd_list)

    search = sub.add_parser("search", help="Search movies by title")
    search.add_argument("query", type=str, help="Search query")
    search.add_argument("--sort", choices=["title", "year", "rating"], default="title")
    search.add_argument("--min-year", type=int, help="Filter by minimum release year")
    search.add_argument("--max-year", type=int, help="Filter by maximum release year")
    search.add_argument("--min-rating", type=float, help="Filter by minimum rating")
    search.add_argument("--max-rating", type=float, help="Filter by maximum rating")
    search.add_argument("--limit", type=int, help="Limit number of results")
    search.set_defaults(func=_cmd_search)

    remove = sub.add_parser("remove", help="Remove a movie")
    remove.add_argument("title", type=str, help="Movie title")
    remove.add_argument("--year", type=int, help="Release year (optional)")
    remove.set_defaults(func=_cmd_remove)

    update = sub.add_parser("update-rating", help="Update a movie rating")
    update.add_argument("title", type=str, help="Movie title")
    update.add_argument("year", type=int, help="Release year")
    update.add_argument("rating", type=float, help="New rating")
    update.set_defaults(func=_cmd_update_rating)

    serve = sub.add_parser("serve", help="Run the web API server (FastAPI)")
    serve.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve.add_argument("--port", type=int, default=8000, help="Port to listen on")
    serve.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


def _create_store(db_path: str) -> object:
    return get_store(db_path)


def _cmd_add(args: argparse.Namespace) -> int:
    store = _create_store(args.db)
    movie = Movie(
        title=args.title,
        year=args.year,
        rating=args.rating,
        plot=args.plot,
        file_path=args.file_path,
        duration_seconds=args.duration,
        language=args.language,
        preview_path=args.preview_path,
    )
    store.add(movie)
    print(f"Added {movie.title} ({movie.year}) to {args.db}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    store = _create_store(args.db)
    movies = store.list(
        min_year=args.min_year,
        max_year=args.max_year,
        min_rating=args.min_rating,
        max_rating=args.max_rating,
        sort=args.sort,
        limit=args.limit,
    )

    if not movies:
        print("No movies found.")
        return 0

    for m in movies:
        info = f"- {m.title} ({m.year}) — rating: {m.rating}"
        if m.language:
            info += f" | {m.language}"
        if m.duration_seconds:
            mins = int(m.duration_seconds // 60)
            info += f" | {mins} min"
        if m.file_path:
            info += f"\n  {m.file_path}"
        print(info)
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    store = _create_store(args.db)
    results = store.search(
        args.query,
        min_year=args.min_year,
        max_year=args.max_year,
        min_rating=args.min_rating,
        max_rating=args.max_rating,
        sort=args.sort,
        limit=args.limit,
    )
    if not results:
        print("No matches found.")
        return 0

    for m in results:
        info = f"- {m.title} ({m.year}) — rating: {m.rating}"
        if m.language:
            info += f" | {m.language}"
        if m.duration_seconds:
            mins = int(m.duration_seconds // 60)
            info += f" | {mins} min"
        if m.file_path:
            info += f"\n  {m.file_path}"
        print(info)
    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    store = _create_store(args.db)
    try:
        removed = store.remove(args.title, args.year)
        print(f"Removed {removed.title} ({removed.year})")
        return 0
    except MovieNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1


def _cmd_update_rating(args: argparse.Namespace) -> int:
    store = _create_store(args.db)
    try:
        updated = store.update_rating(args.title, args.year, args.rating)
        print(f"Updated {updated.title} ({updated.year}) rating to {updated.rating}")
        return 0
    except MovieNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed. Install it with `pip install 'moviemetadb[web]'`.")
        return 1

    try:
        from .web import app
    except ImportError as exc:
        print(exc)
        return 1

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    return _run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
