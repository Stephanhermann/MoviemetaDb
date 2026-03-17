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

Add a movie:

```bash
moviemetadb add "Inception" 2010 --rating 8.8
```

List stored movies:

```bash
moviemetadb list
```

The data is stored in a JSON file by default (`moviemetadb.json`).

## Development

Run the unit tests:

```bash
make test
```
