"""The real catalog HTTP client, exercised through httpx.MockTransport (no network)."""

import asyncio
import json
from collections.abc import Callable
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from orders_service.catalog_client import CatalogClient, CatalogServiceError, get_catalog_client
from orders_service.main import app

Handler = Callable[[httpx.Request], httpx.Response]

RESERVED = {
    "product_id": 7,
    "sku": "SKU-7",
    "quantity": 2,
    "unit_price": "12.50",
    "remaining_stock": 8,
}


def reserve(handler: Handler, product_id: int = 7, quantity: int = 2):
    catalog = CatalogClient("http://catalog.test", 2.5, transport=httpx.MockTransport(handler))
    return asyncio.run(catalog.reserve(product_id, quantity))


def test_successful_reservation_posts_expected_request() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=RESERVED)

    result = reserve(handler)

    assert result.unit_price == Decimal("12.50")
    assert result.remaining_stock == 8
    (request,) = seen
    assert request.method == "POST"
    assert str(request.url) == "http://catalog.test/api/v1/products/7/reserve"
    assert json.loads(request.content) == {"quantity": 2}


@pytest.mark.parametrize(
    ("status", "body", "expected_detail"),
    [
        (404, {"detail": "Product 7 was not found"}, "Product 7 was not found"),
        (409, {"detail": "Insufficient stock"}, "Insufficient stock"),
        (404, "<html>Not Found</html>", "Catalog reservation failed"),
        (409, {"detail": [{"msg": "structured"}]}, "Catalog reservation failed"),
        (404, ["not", "an", "object"], "Catalog reservation failed"),
    ],
)
def test_not_found_and_conflict_keep_status_and_safe_detail(status, body, expected_detail) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(body, str):
            return httpx.Response(status, text=body)
        return httpx.Response(status, json=body)

    with pytest.raises(CatalogServiceError) as error:
        reserve(handler)

    assert error.value.status_code == status
    assert str(error.value) == expected_detail


def test_other_error_statuses_map_to_bad_gateway() -> None:
    with pytest.raises(CatalogServiceError) as error:
        reserve(lambda request: httpx.Response(500, text="boom"))
    assert error.value.status_code == 502
    assert str(error.value) == "Unexpected response from catalog service"


@pytest.mark.parametrize(
    "exception",
    [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")],
)
def test_transport_failures_map_to_unavailable(exception) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exception

    with pytest.raises(CatalogServiceError) as error:
        reserve(handler)
    assert error.value.status_code == 502
    assert str(error.value) == "Catalog service is unavailable"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>maintenance</html>"),
        httpx.Response(200, json={"unexpected": True}),
        httpx.Response(200, json={**RESERVED, "unit_price": "not-a-number"}),
    ],
)
def test_malformed_success_payload_maps_to_bad_gateway(response) -> None:
    with pytest.raises(CatalogServiceError) as error:
        reserve(lambda request: response)
    assert error.value.status_code == 502
    assert str(error.value) == "Invalid reservation response from catalog service"


@pytest.mark.parametrize(
    "mismatch",
    [{"product_id": 8}, {"quantity": 3}],
)
def test_reservation_for_another_item_is_rejected(mismatch) -> None:
    with pytest.raises(CatalogServiceError) as error:
        reserve(lambda request: httpx.Response(200, json={**RESERVED, **mismatch}))
    assert error.value.status_code == 502
    assert "does not match" in str(error.value)


def test_order_api_returns_502_not_500_for_html_catalog_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>gateway page</html>")

    app.dependency_overrides[get_catalog_client] = lambda: CatalogClient(
        "http://catalog.test", 2.5, transport=httpx.MockTransport(handler)
    )
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/orders", json={"product_id": 7, "quantity": 2})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "Invalid reservation response from catalog service"}
