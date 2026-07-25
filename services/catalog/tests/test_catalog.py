from fastapi.testclient import TestClient


def create_product(client: TestClient, sku: str = "SKU-001", stock: int = 10) -> dict:
    response = client.post(
        "/api/v1/products",
        json={"sku": sku, "name": "Test Product", "price": "12.50", "stock": stock},
    )
    assert response.status_code == 201
    return response.json()


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").json()["status"] == "alive"
    assert client.get("/health/ready").json()["status"] == "ready"


def test_create_and_list_products(client: TestClient) -> None:
    created = create_product(client)
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert any(product["id"] == created["id"] for product in response.json())


def test_duplicate_sku_is_rejected(client: TestClient) -> None:
    create_product(client, sku="UNIQUE-001")
    response = client.post(
        "/api/v1/products",
        json={"sku": "UNIQUE-001", "name": "Duplicate", "price": "9.99", "stock": 2},
    )

    assert response.status_code == 409


def test_inventory_reservation_reduces_stock(client: TestClient) -> None:
    product = create_product(client, sku="RESERVE-001", stock=8)
    response = client.post(
        f"/api/v1/products/{product['id']}/reserve",
        json={"quantity": 3},
    )

    assert response.status_code == 200
    assert response.json()["remaining_stock"] == 5
    assert response.json()["unit_price"] == "12.50"


def test_insufficient_inventory_returns_conflict(client: TestClient) -> None:
    product = create_product(client, sku="LOW-STOCK-001", stock=1)
    response = client.post(
        f"/api/v1/products/{product['id']}/reserve",
        json={"quantity": 2},
    )

    assert response.status_code == 409


def test_unknown_product_returns_not_found(client: TestClient) -> None:
    assert client.get("/api/v1/products/999999").status_code == 404
    assert client.post("/api/v1/products/999999/reserve", json={"quantity": 1}).status_code == 404


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "catalog_http_requests_total" in response.text
