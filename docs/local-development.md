# Local Development

## Requirements

- Python 3.12
- Docker Desktop with Docker Compose
- Git

Optional tools:

- Helm
- Terraform
- k6

## Python-only test environment

Windows PowerShell:

```powershell
.\scripts\bootstrap.ps1
.\scripts\verify.ps1
```

Linux or macOS:

```bash
chmod +x scripts/*.sh
./scripts/bootstrap.sh
make verify
```

Tests use isolated SQLite databases and do not require Docker or Huawei Cloud.

## Full local stack

Copy the development environment template:

```bash
cp .env.example .env
docker compose up --build -d
```

Service URLs:

- Catalog OpenAPI: `http://localhost:8001/docs`
- Orders OpenAPI: `http://localhost:8002/docs`
- Catalog metrics: `http://localhost:8001/metrics`
- Orders metrics: `http://localhost:8002/metrics`

Run the end-to-end smoke test:

```bash
python scripts/smoke_test.py
```

Stop the stack:

```bash
docker compose down
```

Use `docker compose down --volumes` only when intentionally deleting local
database data.

