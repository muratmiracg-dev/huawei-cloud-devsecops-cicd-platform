from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from catalog_service.models import InventoryReservation, Product
from catalog_service.schemas import ProductCreate


class DuplicateSkuError(ValueError):
    pass


class ProductNotFoundError(LookupError):
    pass


class InsufficientStockError(ValueError):
    pass


class ReservationNotFoundError(LookupError):
    pass


def list_products(database: Session, *, limit: int, offset: int) -> list[Product]:
    return list(database.scalars(select(Product).order_by(Product.id).offset(offset).limit(limit)))


def get_product(database: Session, product_id: int, *, refresh: bool = False) -> Product:
    product = database.get(Product, product_id, populate_existing=refresh)
    if product is None:
        raise ProductNotFoundError(f"Product {product_id} was not found")
    return product


def create_product(database: Session, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    database.add(product)
    try:
        database.commit()
    except IntegrityError as exc:
        database.rollback()
        raise DuplicateSkuError(f"SKU {payload.sku} already exists") from exc
    database.refresh(product)
    return product


def reserve_inventory(
    database: Session, product_id: int, quantity: int
) -> tuple[Product, InventoryReservation]:
    """Decrement stock atomically in the database.

    Reading the product and writing ``stock - quantity`` back from Python let two
    concurrent reservations (several catalog replicas behind the HPA) read the same
    stock and both succeed, losing one decrement and overselling. A single
    conditional ``UPDATE ... WHERE stock >= quantity`` lets the database serialise
    the check and the write. The decrement and its reservation record commit together,
    so every unit taken out of stock has exactly one reservation that can return it.
    """

    result = database.execute(
        update(Product)
        .where(Product.id == product_id, Product.stock >= quantity)
        .values(stock=Product.stock - quantity)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        database.rollback()
        product = get_product(database, product_id, refresh=True)
        raise InsufficientStockError(
            f"Requested {quantity} units but only {product.stock} are available"
        )
    reservation = InventoryReservation(
        id=str(uuid4()), product_id=product_id, quantity=quantity, status="reserved"
    )
    database.add(reservation)
    database.commit()
    return get_product(database, product_id, refresh=True), reservation


def release_reservation(database: Session, reservation_id: str) -> Product:
    """Return the units of one reservation to stock, at most once.

    Releasing by product and quantity let any caller add arbitrary stock and turned a
    retried compensation into a double credit. Only the reservation that took the units
    can return them, exactly its quantity, and a repeated release is a no-op.
    """

    reservation = database.get(InventoryReservation, reservation_id)
    if reservation is None:
        raise ReservationNotFoundError(f"Reservation {reservation_id} was not found")
    claimed = database.execute(
        update(InventoryReservation)
        .where(
            InventoryReservation.id == reservation_id,
            InventoryReservation.status == "reserved",
        )
        .values(status="released")
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount == 1:
        database.execute(
            update(Product)
            .where(Product.id == reservation.product_id)
            .values(stock=Product.stock + reservation.quantity)
            .execution_options(synchronize_session=False)
        )
    database.commit()
    return get_product(database, reservation.product_id, refresh=True)
