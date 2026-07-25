#!/usr/bin/env bash
set -euo pipefail

.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
docker compose config --quiet

