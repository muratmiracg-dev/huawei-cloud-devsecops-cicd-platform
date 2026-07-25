from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from orders_service import repository
from orders_service.catalog_client import CatalogDependency, CatalogServiceError
from orders_service.database import get_db
from orders_service.metrics import ORDER_COUNT
from orders_service.schemas import OrderCreate, OrderRead

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
Database = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[OrderRead])
def orders(database: Database) -> list[OrderRead]:
    return repository.list_orders(database)


@router.get("/{order_id}", response_model=OrderRead)
def order(order_id: str, database: Database) -> OrderRead:
    order_record = repository.get_order(database, order_id)
    if order_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order_record


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def add_order(
    payload: OrderCreate,
    response: Response,
    database: Database,
    catalog: CatalogDependency,
    idempotency_key: Annotated[
        str | None,
        Header(alias="X-Idempotency-Key", min_length=8, max_length=128),
    ] = None,
) -> OrderRead:
    request_key = idempotency_key or str(uuid4())
    existing = repository.get_by_idempotency_key(database, request_key)
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return existing

    try:
        reservation = await catalog.reserve(payload.product_id, payload.quantity)
    except CatalogServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    created = repository.create_order(
        database,
        idempotency_key=request_key,
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit_price=reservation.unit_price,
    )
    ORDER_COUNT.inc()
    return created
