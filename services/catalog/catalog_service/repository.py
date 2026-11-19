from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from catalog_service.models import Product
from catalog_service.schemas import ProductCreate


class DuplicateSkuError(ValueError):
    pass


class ProductNotFoundError(LookupError):
    pass


class InsufficientStockError(ValueError):
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


def reserve_inventory(database: Session, product_id: int, quantity: int) -> Product:
    """Decrement stock atomically in the database.

    Reading the product and writing ``stock - quantity`` back from Python let two
    concurrent reservations (several catalog replicas behind the HPA) read the same
    stock and both succeed, losing one decrement and overselling. A single
    conditional ``UPDATE ... WHERE stock >= quantity`` lets the database serialise
    the check and the write.
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
    database.commit()
    return get_product(database, product_id, refresh=True)


def release_inventory(database: Session, product_id: int, quantity: int) -> Product:
    """Return previously reserved units to stock (compensation for an unused reservation)."""

    result = database.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(stock=Product.stock + quantity)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        database.rollback()
        raise ProductNotFoundError(f"Product {product_id} was not found")
    database.commit()
    return get_product(database, product_id, refresh=True)
