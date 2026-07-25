from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from catalog_service import repository
from catalog_service.database import get_db
from catalog_service.schemas import (
    InventoryReservation,
    ProductCreate,
    ProductRead,
    ReservationResult,
)

router = APIRouter(prefix="/api/v1/products", tags=["products"])
Database = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[ProductRead])
def products(database: Database) -> list[ProductRead]:
    return repository.list_products(database)


@router.get("/{product_id}", response_model=ProductRead)
def product(product_id: int, database: Database) -> ProductRead:
    try:
        return repository.get_product(database, product_id)
    except repository.ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def add_product(payload: ProductCreate, database: Database) -> ProductRead:
    try:
        return repository.create_product(database, payload)
    except repository.DuplicateSkuError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{product_id}/reserve", response_model=ReservationResult)
def reserve(
    product_id: int,
    payload: InventoryReservation,
    database: Database,
) -> ReservationResult:
    try:
        product_record = repository.reserve_inventory(database, product_id, payload.quantity)
    except repository.ProductNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except repository.InsufficientStockError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ReservationResult(
        product_id=product_record.id,
        sku=product_record.sku,
        quantity=payload.quantity,
        unit_price=product_record.price,
        remaining_stock=product_record.stock,
    )
