PYTHON := python3
DEPTH ?= 3
FEN ?=

# Extract project version from pyproject.toml (simple grep/sed)
PROJECT_VERSION := $(shell grep -E '^version *= *"' pyproject.toml | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')

# Bench configuration (override via environment/CLI)
BENCH_POSITIONS ?= assets/benchmarks/positions.json
BENCH_MOVETIME_MS ?= 2000
BENCH_DEPTH ?=
BENCH_HASH_MB ?= 16
BENCH_ITERATIONS ?= 3
BENCH_OUT ?= assets/benchmarks/baseline-$(PROJECT_VERSION).json
BENCH_PRETTY ?= 1
BENCH_PROGRESS ?= 1
BENCH_PROFILING ?=

.PHONY: build run test lint format format-check hooks hooks-run ci bench

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

# Run engine benchmarks over a positions suite and write a baseline JSON
bench:
	$(PYTHON) scripts/bench.py \
		--positions $(BENCH_POSITIONS) \
		$(if $(BENCH_MOVETIME_MS),--movetime-ms $(BENCH_MOVETIME_MS),) \
		$(if $(BENCH_DEPTH),--depth $(BENCH_DEPTH),) \
		$(if $(BENCH_HASH_MB),--hash-mb $(BENCH_HASH_MB),) \
		$(if $(BENCH_ITERATIONS),--iterations $(BENCH_ITERATIONS),) \
		$(if $(BENCH_OUT),--out $(BENCH_OUT),) \
		$(if $(BENCH_PRETTY),--pretty,) \
		$(if $(BENCH_PROGRESS),--progress,) \
		$(if $(BENCH_PROFILING),--profiling,)
