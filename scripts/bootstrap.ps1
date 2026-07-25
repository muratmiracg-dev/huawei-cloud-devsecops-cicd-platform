$ErrorActionPreference = "Stop"

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
Write-Host "Development environment is ready. Run .\scripts\verify.ps1"
