from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=160)]


class ProductCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: ProductName
    price: Decimal = Field(gt=0, decimal_places=2)
    stock: int = Field(ge=0, le=1_000_000, strict=True)


class ProductRead(ProductCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class InventoryReservation(BaseModel):
    quantity: int = Field(gt=0, le=10_000, strict=True)


class ReservationResult(BaseModel):
    product_id: int
    sku: str
    quantity: int
    unit_price: Decimal
    remaining_stock: int
