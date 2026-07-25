from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from orders_service.models import Order


def list_orders(database: Session) -> list[Order]:
    return list(database.scalars(select(Order).order_by(Order.created_at.desc())))


def get_order(database: Session, order_id: str) -> Order | None:
    return database.get(Order, order_id)


def get_by_idempotency_key(database: Session, key: str) -> Order | None:
    return database.scalar(select(Order).where(Order.idempotency_key == key))


def create_order(
    database: Session,
    *,
    idempotency_key: str,
    product_id: int,
    quantity: int,
    unit_price: Decimal,
) -> Order:
    order = Order(
        id=str(uuid4()),
        idempotency_key=idempotency_key,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=unit_price * quantity,
        status="confirmed",
    )
    database.add(order)
    database.commit()
    database.refresh(order)
    return order
