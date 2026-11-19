import pytest
from fastapi.testclient import TestClient
from orders_service.config import Settings
from pydantic import ValidationError


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json()["status"] == "alive"
    assert client.get("/health/ready").json()["status"] == "ready"


@pytest.mark.parametrize("timeout", [0, -1, 61, float("inf"), float("nan")])
def test_catalog_timeout_rejects_unsafe_values(timeout: float) -> None:
    with pytest.raises(ValidationError):
        Settings(catalog_timeout_seconds=timeout)


def test_create_order(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orders",
        headers={"X-Idempotency-Key": "checkout-0001"},
        json={"product_id": 1, "quantity": 2},
    )

    assert response.status_code == 201
    assert response.json()["total_amount"] == "25.00"
    assert response.json()["status"] == "confirmed"


def test_order_rejects_coerced_identifiers_and_quantities(client: TestClient) -> None:
    for payload in (
        {"product_id": True, "quantity": 1},
        {"product_id": 1.0, "quantity": 1},
        {"product_id": 1, "quantity": True},
        {"product_id": 1, "quantity": 1.5},
    ):
        response = client.post("/api/v1/orders", json=payload)
        assert response.status_code == 422


def test_idempotency_key_returns_original_order(client: TestClient) -> None:
    payload = {"product_id": 2, "quantity": 1}
    headers = {"X-Idempotency-Key": "checkout-idempotent-0001"}

    first = client.post("/api/v1/orders", headers=headers, json=payload)
    second = client.post("/api/v1/orders", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_idempotency_key_is_trimmed_and_blank_values_are_rejected(client: TestClient) -> None:
    payload = {"product_id": 1, "quantity": 1}
    first = client.post(
        "/api/v1/orders", headers={"X-Idempotency-Key": "  checkout-trimmed-01  "}, json=payload
    )
    second = client.post(
        "/api/v1/orders", headers={"X-Idempotency-Key": "checkout-trimmed-01"}, json=payload
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert (
        client.post(
            "/api/v1/orders", headers={"X-Idempotency-Key": "        "}, json=payload
        ).status_code
        == 422
    )


def test_idempotency_key_rejects_different_order_payload(client: TestClient) -> None:
    headers = {"X-Idempotency-Key": "checkout-conflict-0001"}

    first = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"product_id": 1, "quantity": 1},
    )
    conflict = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"product_id": 2, "quantity": 3},
    )

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == (
        "Idempotency key has already been used with a different order payload"
    )
    orders = client.get("/api/v1/orders").json()
    matching_orders = [order for order in orders if order["id"] == first.json()["id"]]
    assert matching_orders == [first.json()]


def test_list_and_get_order(client: TestClient) -> None:
    created = client.post(
        "/api/v1/orders",
        headers={"X-Idempotency-Key": "checkout-list-0001"},
        json={"product_id": 3, "quantity": 1},
    ).json()

    assert any(order["id"] == created["id"] for order in client.get("/api/v1/orders").json())
    assert client.get(f"/api/v1/orders/{created['id']}").json()["id"] == created["id"]


def test_unknown_order_returns_not_found(client: TestClient) -> None:
    assert client.get("/api/v1/orders/unknown").status_code == 404


def test_catalog_error_is_propagated(client: TestClient) -> None:
    not_found = client.post(
        "/api/v1/orders",
        json={"product_id": 404, "quantity": 1},
    )
    insufficient = client.post(
        "/api/v1/orders",
        json={"product_id": 1, "quantity": 11},
    )

    assert not_found.status_code == 404
    assert insufficient.status_code == 409


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "orders_http_requests_total" in response.text


def test_concurrent_duplicate_key_returns_existing_order_and_releases_stock(
    client: TestClient, monkeypatch
) -> None:
    """Two requests with one key both pass the lookup before either stores its order."""
    from conftest import FakeCatalogClient
    from orders_service import repository

    headers = {"X-Idempotency-Key": "race-key-0001"}
    first = client.post("/api/v1/orders", json={"product_id": 7, "quantity": 2}, headers=headers)
    assert first.status_code == 201

    real_lookup = repository.get_by_idempotency_key
    calls = {"count": 0}

    def lookup_misses_once(database, key):
        calls["count"] += 1
        return None if calls["count"] == 1 else real_lookup(database, key)

    monkeypatch.setattr(repository, "get_by_idempotency_key", lookup_misses_once)
    FakeCatalogClient.releases.clear()
    second = client.post("/api/v1/orders", json={"product_id": 7, "quantity": 2}, headers=headers)

    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert FakeCatalogClient.releases == [(7, 2)]


def test_failed_order_write_releases_the_reservation(client: TestClient, monkeypatch) -> None:
    from conftest import FakeCatalogClient
    from orders_service import repository

    def broken_create(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(repository, "create_order", broken_create)
    FakeCatalogClient.releases.clear()
    with pytest.raises(RuntimeError):
        client.post("/api/v1/orders", json={"product_id": 8, "quantity": 1})
    assert FakeCatalogClient.releases == [(8, 1)]
