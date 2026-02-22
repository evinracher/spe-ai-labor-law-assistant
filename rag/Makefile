.PHONY: setup lint format test

## Install dependencies and activate git hooks (run once after cloning)
setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/pre-commit install

## Run ruff linter
lint:
	ruff check app/ tests/

## Run ruff formatter
format:
	ruff format app/ tests/

## Run test suite
test:
	pytest -v
