from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


class OrderRead(OrderCreate):
    id: str
    unit_price: Decimal
    total_amount: Decimal
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReservationResult(BaseModel):
    product_id: int
    sku: str
    quantity: int
    unit_price: Decimal
    remaining_stock: int
