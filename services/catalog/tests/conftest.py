import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DATABASE = Path(__file__).parent / "catalog_test.db"
if TEST_DATABASE.exists():
    TEST_DATABASE.unlink()

os.environ["CATALOG_DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"
os.environ["CATALOG_SEED_DATA"] = "false"

from catalog_service.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
