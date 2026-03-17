# MoviemetaDb

A small starter project for managing movie metadata with a minimal Python library + CLI.

This project uses SQLite by default (stored in `moviemetadb.db`).
You can also run it against PostgreSQL by setting `MOVIEMETADB_DATABASE_URL` or passing a SQLAlchemy URL via `--db`.

## Getting started

Install (recommended inside a virtualenv):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

## Usage

### CLI commands

- Add a movie:

```bash
moviemetadb add "Inception" 2010 --rating 8.8
```

- List stored movies:

```bash
moviemetadb list
```

- Search by title:

```bash
moviemetadb search inception
```

- Remove a movie:

```bash
moviemetadb remove "Inception" --year 2010
```

- Update a movie rating:

```bash
moviemetadb update-rating "Inception" 2010 9.0
```

### Web API (optional)

To run the FastAPI web server, install the `web` extras:

```bash
python -m pip install -e .[web]
```

Then start the server:

```bash
moviemetadb serve --host 0.0.0.0 --port 8000
```

The web API will be available at `http://127.0.0.1:8000`.

By default the web API uses SQLite (`moviemetadb.db`). To use a different database, set `MOVIEMETADB_DATABASE_URL` or pass `--db` to the CLI:

```bash
export MOVIEMETADB_DATABASE_URL="postgresql://moviemetadb:moviemetadb@localhost:5432/moviemetadb"
moviemetadb serve
```

If you want to keep using JSON storage:

```bash
moviemetadb --db moviemetadb.json serve
```

### API authentication

If `MOVIEMETADB_API_KEY` is set, the API will require an `Authorization: Bearer <key>` header on all requests.

```bash
export MOVIEMETADB_API_KEY="my-secret"
```

## Running with PostgreSQL (Docker)

A `docker-compose.yml` is included for local development. It starts a Postgres instance:

```bash
docker-compose up -d
```

Then configure the application to use it:

```bash
export MOVIEMETADB_DATABASE_URL="postgresql://moviemetadb:moviemetadb@localhost:5432/moviemetadb"
moviemetadb serve
```

## Development

Run the unit tests:

```bash
make test
```
