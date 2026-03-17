# MoviemetaDb

A small starter project for managing movie metadata with a minimal Python library + CLI.

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

The data is stored in a JSON file by default (`moviemetadb.json`).

## Development

Run the unit tests:

```bash
make test
```
