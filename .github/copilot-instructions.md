# GitHub Copilot Chat Workspace Instructions

## About this repository
- **Name:** MoviemetaDb
- **Purpose:** A Python-based movie metadata tool with both a CLI and an optional web API.

## What Copilot Chat can help with
- Adding new features (data model, additional CLI commands, web API endpoints)
- Improving or adding persistence backends (SQLite, Postgres, etc.)
- Implementing tests and enhancing CI workflows
- Improving documentation and UX

## How to run / develop
This project uses a standard Python packaging layout.

- Install the project for development:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install -U pip
  python -m pip install -e .
  ```

- Run the CLI:
  ```bash
  moviemetadb add "Inception" 2010 --rating 8.8
  moviemetadb list
  ```

- Run the unit tests:
  ```bash
  make test
  ```

- Run the (optional) web API server:
  ```bash
  python -m pip install -e .[web]
  moviemetadb serve --host 0.0.0.0 --port 8000
  ```

## Conventions
- Keep changes small and focused
- Prefer clear, idiomatic code in Python
- Add or update documentation when adding functionality

## When to ask Copilot Chat
- If you want suggestions for architecture, file layout, or naming
- When you need help writing tests or automation (GitHub Actions)
- To generate or update documentation and README content

## Example prompts
- "Add a CLI for importing movie metadata from CSV, with tests." 
- "Create a GitHub Actions workflow that runs linters and unit tests." 
- "Refactor this repository into a small Python package with a `setup.py`."
