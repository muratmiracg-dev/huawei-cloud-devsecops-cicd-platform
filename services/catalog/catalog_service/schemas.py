from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=160)
    price: Decimal = Field(gt=0, decimal_places=2)
    stock: int = Field(ge=0, le=1_000_000)


class ProductRead(ProductCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class InventoryReservation(BaseModel):
    quantity: int = Field(gt=0, le=10_000)


class ReservationResult(BaseModel):
    product_id: int
    sku: str
    quantity: int
    unit_price: Decimal
    remaining_stock: int
