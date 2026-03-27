.PHONY: setup lint format test serve ingest

## Install dependencies and activate git hooks (run once after cloning).
## Skips venv creation if .venv already exists.
setup:
	@[ -d .venv ] || python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	@command -v .venv/bin/pre-commit >/dev/null 2>&1 && .venv/bin/pre-commit install || true

## Start the development server (uses settings from .env)
serve:
	.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Run the document ingestion pipeline
ingest:
	.venv/bin/python -m app.rag.pipelines.run_ingestion

## Run ruff linter
lint:
	.venv/bin/ruff check app/ tests/

## Run ruff formatter
format:
	.venv/bin/ruff format app/ tests/

## Run test suite
test:
	.venv/bin/pytest -v
