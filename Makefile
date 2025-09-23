PYTHON := python3
DEPTH ?= 3
FEN ?=

.PHONY: build run test lint format

build:
	@echo "Nothing to build (Python project)."

run:
	uvicorn src.protocol.http.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

test:
	$(PYTHON) -m pytest -q

lint:
	ruff check .

format:
	black .

.PHONY: perft
perft:
	$(PYTHON) scripts/perft.py --depth $(DEPTH) $(if $(FEN),--fen "$(FEN)",)
