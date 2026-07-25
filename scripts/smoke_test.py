#!/usr/bin/env python3
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CATALOG_URL = os.getenv("CATALOG_URL", "http://localhost:8001")
ORDERS_URL = os.getenv("ORDERS_URL", "http://localhost:8002")


def request_json(url: str, *, method: str = "GET", payload: dict | None = None) -> dict | list:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if method == "POST" and url.endswith("/orders"):
        request.add_header("X-Idempotency-Key", "smoke-test-order-0001")
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read())


def main() -> int:
    try:
        catalog_health = request_json(f"{CATALOG_URL}/health/ready")
        orders_health = request_json(f"{ORDERS_URL}/health/ready")
        products = request_json(f"{CATALOG_URL}/api/v1/products")
        if not products:
            raise RuntimeError("Catalog does not contain a product for the smoke test")

        order = request_json(
            f"{ORDERS_URL}/api/v1/orders",
            method="POST",
            payload={"product_id": products[0]["id"], "quantity": 1},
        )
    except (HTTPError, URLError, RuntimeError) as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "catalog": catalog_health["status"],
                "orders": orders_health["status"],
                "order_id": order["id"],
                "result": "passed",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
