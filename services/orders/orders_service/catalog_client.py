from typing import Annotated

import httpx
from fastapi import Depends

from orders_service.config import get_settings
from orders_service.schemas import ReservationResult


class CatalogServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class CatalogClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    async def reserve(self, product_id: int, quantity: int) -> ReservationResult:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            ) as client:
                response = await client.post(
                    f"/api/v1/products/{product_id}/reserve",
                    json={"quantity": quantity},
                )
        except httpx.RequestError as exc:
            raise CatalogServiceError("Catalog service is unavailable") from exc

        if response.status_code in {404, 409}:
            detail = response.json().get("detail", "Catalog reservation failed")
            raise CatalogServiceError(detail, status_code=response.status_code)
        if response.is_error:
            raise CatalogServiceError("Unexpected response from catalog service")
        return ReservationResult.model_validate(response.json())


def get_catalog_client() -> CatalogClient:
    settings = get_settings()
    return CatalogClient(settings.catalog_base_url, settings.catalog_timeout_seconds)


CatalogDependency = Annotated[CatalogClient, Depends(get_catalog_client)]
