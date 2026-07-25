.PHONY: install format lint test verify compose-up compose-down smoke

PYTHON ?= .venv/bin/python
RUFF ?= .venv/bin/ruff
PYTEST ?= .venv/bin/pytest

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.lock

format:
	$(RUFF) format .
	$(RUFF) check --fix .

lint:
	$(RUFF) check .
	$(RUFF) format --check .

test:
	$(PYTEST)

verify: lint test

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

smoke:
	$(PYTHON) scripts/smoke_test.py
