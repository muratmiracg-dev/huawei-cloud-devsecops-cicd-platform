from typing import Annotated

import httpx
from fastapi import Depends
from pydantic import ValidationError

from orders_service.config import get_settings
from orders_service.schemas import ReservationResult


class CatalogServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _error_detail(response: httpx.Response, default: str) -> str:
    """Return the catalog's string `detail`, or `default` for non-JSON or other shapes.

    A 404 can come from an ingress or gateway as HTML rather than from the catalog API.
    """
    try:
        payload = response.json()
    except ValueError:
        return default
    detail = payload.get("detail") if isinstance(payload, dict) else None
    return detail if isinstance(detail, str) and detail.strip() else default


class CatalogClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    async def reserve(self, product_id: int, quantity: int) -> ReservationResult:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    f"/api/v1/products/{product_id}/reserve",
                    json={"quantity": quantity},
                )
        except httpx.RequestError as exc:
            raise CatalogServiceError("Catalog service is unavailable") from exc

        if response.status_code in {404, 409}:
            detail = _error_detail(response, "Catalog reservation failed")
            raise CatalogServiceError(detail, status_code=response.status_code)
        if response.is_error:
            raise CatalogServiceError("Unexpected response from catalog service")
        try:
            reservation = ReservationResult.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise CatalogServiceError("Invalid reservation response from catalog service") from exc
        if reservation.product_id != product_id or reservation.quantity != quantity:
            # Never price an order from a reservation for a different product or quantity.
            raise CatalogServiceError("Catalog reservation does not match the requested item")
        return reservation


def get_catalog_client() -> CatalogClient:
    settings = get_settings()
    return CatalogClient(settings.catalog_base_url, settings.catalog_timeout_seconds)


CatalogDependency = Annotated[CatalogClient, Depends(get_catalog_client)]
