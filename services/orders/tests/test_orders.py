from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json()["status"] == "alive"
    assert client.get("/health/ready").json()["status"] == "ready"


def test_create_order(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orders",
        headers={"X-Idempotency-Key": "checkout-0001"},
        json={"product_id": 1, "quantity": 2},
    )

    assert response.status_code == 201
    assert response.json()["total_amount"] == "25.00"
    assert response.json()["status"] == "confirmed"


def test_idempotency_key_returns_original_order(client: TestClient) -> None:
    payload = {"product_id": 2, "quantity": 1}
    headers = {"X-Idempotency-Key": "checkout-idempotent-0001"}

    first = client.post("/api/v1/orders", headers=headers, json=payload)
    second = client.post("/api/v1/orders", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


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
