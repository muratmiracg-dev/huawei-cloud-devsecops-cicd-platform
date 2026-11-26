import os
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

TEST_DATABASE = Path(__file__).parent / "orders_test.db"
if TEST_DATABASE.exists():
    TEST_DATABASE.unlink()

os.environ["ORDERS_DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"

from orders_service.catalog_client import (  # noqa: E402
    CatalogServiceError,
    get_catalog_client,
)
from orders_service.main import app  # noqa: E402
from orders_service.schemas import ReservationResult  # noqa: E402


class FakeCatalogClient:
    reservations: list[ReservationResult] = []
    releases: list[UUID] = []

    async def release(self, reservation_id: UUID) -> None:
        FakeCatalogClient.releases.append(reservation_id)

    async def reserve(self, product_id: int, quantity: int) -> ReservationResult:
        if product_id == 404:
            raise CatalogServiceError("Product not found", status_code=404)
        if quantity > 10:
            raise CatalogServiceError("Insufficient stock", status_code=409)
        reservation = ReservationResult(
            reservation_id=uuid4(),
            product_id=product_id,
            sku=f"SKU-{product_id}",
            quantity=quantity,
            unit_price=Decimal("12.50"),
            remaining_stock=10 - quantity,
        )
        FakeCatalogClient.reservations.append(reservation)
        return reservation


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_catalog_client] = lambda: FakeCatalogClient()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
