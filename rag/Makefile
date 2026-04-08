.PHONY: setup lint format test test-kg test-graphdb serve ingest ingest-test

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

## Run the full document ingestion pipeline (all PDFs in app/data/)
ingest:
	.venv/bin/python -m app.rag.pipelines.run_ingestion

## Run the lightweight test ingestion pipeline
## Reads only app/data/test/, uses RecursiveCharacterTextSplitter (no Gemini API for chunking),
## and writes to ./db_chroma_test. Set CHROMA_DIR=./db_chroma_test in .env before serving.
ingest-test:
	.venv/bin/python -m app.rag.pipelines.run_ingestion_test

## Run ruff linter
lint:
	.venv/bin/ruff check app/ tests/

## Run ruff formatter
format:
	.venv/bin/ruff format app/ tests/

## Run test suite
test:
	.venv/bin/pytest -v

## Run Knowledge Graph integration tests only
test-kg:
	.venv/bin/pytest tests/test_kg.py -v

## Test live GraphDB connection using .env settings
test-graphdb:
	.venv/bin/python -m scripts.test_graphdb_connection
