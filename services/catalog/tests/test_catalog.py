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


def test_product_listing_has_bounded_pagination(client: TestClient) -> None:
    existing_count = len(client.get("/api/v1/products", params={"limit": 100}).json())
    create_product(client, sku="PAGE-001")
    second = create_product(client, sku="PAGE-002")
    response = client.get("/api/v1/products", params={"limit": 1, "offset": existing_count + 1})
    assert response.status_code == 200
    assert [product["id"] for product in response.json()] == [second["id"]]
    assert client.get("/api/v1/products", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/products", params={"offset": -1}).status_code == 422


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


def test_invalid_reservation_types_do_not_change_stock(client: TestClient) -> None:
    product = create_product(client, sku="STRICT-RESERVE", stock=8)
    for quantity in (True, False, "2", 1.5, 2.0):
        response = client.post(
            f"/api/v1/products/{product['id']}/reserve", json={"quantity": quantity}
        )
        assert response.status_code == 422
        assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 8


def test_invalid_stock_types_are_rejected(client: TestClient) -> None:
    for stock in (True, False, "2", 1.5, 2.0):
        response = client.post(
            "/api/v1/products",
            json={"sku": "STRICT-STOCK", "name": "Product", "price": "12.50", "stock": stock},
        )
        assert response.status_code == 422


def test_product_names_are_trimmed_and_blank_names_rejected(client: TestClient) -> None:
    blank = client.post(
        "/api/v1/products",
        json={"sku": "BLANK-NAME", "name": "   ", "price": "12.50", "stock": 2},
    )
    assert blank.status_code == 422

    created = client.post(
        "/api/v1/products",
        json={"sku": "TRIMMED-NAME", "name": "  Test Product  ", "price": "12.50", "stock": 2},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Test Product"


def test_concurrent_reservations_cannot_oversell(client: TestClient) -> None:
    """A reservation committed between another request's read and write must count.

    The second session reserves 3 of 5 units at the moment the first session is about
    to write its own reservation of 3. Read-modify-write code overwrote the stock with
    a stale value (both succeeded, stock 2 instead of an oversell refusal).
    """
    from catalog_service import repository
    from catalog_service.database import SessionLocal, engine
    from sqlalchemy import event

    product = create_product(client, sku="RACE-001", stock=5)
    concurrent_done = {"value": False}

    def reserve_concurrently(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("UPDATE") and not concurrent_done["value"]:
            concurrent_done["value"] = True
            other = SessionLocal()
            try:
                repository.reserve_inventory(other, product["id"], 3)
            finally:
                other.close()

    first = SessionLocal()
    # The first request has already read the product, as a concurrent request would.
    assert repository.get_product(first, product["id"]).stock == 5
    event.listen(engine, "before_cursor_execute", reserve_concurrently)
    try:
        try:
            repository.reserve_inventory(first, product["id"], 3)
            first_succeeded = True
        except repository.InsufficientStockError:
            first_succeeded = False
    finally:
        event.remove(engine, "before_cursor_execute", reserve_concurrently)
        first.close()

    assert concurrent_done["value"]
    assert not first_succeeded
    assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 2


def test_release_returns_reserved_units(client: TestClient) -> None:
    product = create_product(client, sku="RELEASE-001", stock=4)
    client.post(f"/api/v1/products/{product['id']}/reserve", json={"quantity": 3})
    response = client.post(f"/api/v1/products/{product['id']}/release", json={"quantity": 3})
    assert response.status_code == 200
    assert response.json()["stock"] == 4
    missing = client.post("/api/v1/products/999999/release", json={"quantity": 1})
    assert missing.status_code == 404
