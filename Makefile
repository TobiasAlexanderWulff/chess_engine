PYTHON := python3
DEPTH ?= 3
FEN ?=

.PHONY: build run test lint format format-check hooks hooks-run ci

build:
	@echo "Nothing to build (Python project)."

run:
	uvicorn src.protocol.http.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

uci:
	$(PYTHON) -m src.cli.uci

test:
	$(PYTHON) -m pytest -q

lint:
	ruff check .
	black --check .

format:
	black .

format-check:
	black --check .

hooks:
	pre-commit install --install-hooks

hooks-run:
	pre-commit run --all-files

ci:
	$(MAKE) build
	$(MAKE) lint
	$(MAKE) test

.PHONY: perft
perft:
	$(PYTHON) scripts/perft.py --depth $(DEPTH) $(if $(FEN),--fen "$(FEN)",)
