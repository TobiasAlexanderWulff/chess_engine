PYTHON := python3

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

