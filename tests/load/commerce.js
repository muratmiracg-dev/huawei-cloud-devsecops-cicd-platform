import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "60s", target: 25 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

const catalogUrl = __ENV.CATALOG_URL || "http://localhost:8001";
const ordersUrl = __ENV.ORDERS_URL || "http://localhost:8002";

export default function () {
  const productsResponse = http.get(`${catalogUrl}/api/v1/products`);
  check(productsResponse, {
    "catalog responds with 200": (response) => response.status === 200,
  });

  const products = productsResponse.json();
  if (products.length > 0) {
    const orderResponse = http.post(
      `${ordersUrl}/api/v1/orders`,
      JSON.stringify({ product_id: products[0].id, quantity: 1 }),
      {
        headers: {
          "Content-Type": "application/json",
          "X-Idempotency-Key": `k6-${__VU}-${__ITER}`,
        },
      },
    );
    check(orderResponse, {
      "order is confirmed": (response) => [200, 201].includes(response.status),
    });
  }

  sleep(1);
}

