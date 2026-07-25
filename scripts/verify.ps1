$ErrorActionPreference = "Stop"

& .\.venv\Scripts\ruff.exe check .
& .\.venv\Scripts\ruff.exe format --check .
& .\.venv\Scripts\pytest.exe
docker compose config --quiet

