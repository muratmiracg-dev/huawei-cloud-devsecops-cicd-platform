from sqlalchemy import select
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


def list_products(database: Session) -> list[Product]:
    return list(database.scalars(select(Product).order_by(Product.id)))


def get_product(database: Session, product_id: int) -> Product:
    product = database.get(Product, product_id)
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
    product = get_product(database, product_id)
    if product.stock < quantity:
        raise InsufficientStockError(
            f"Requested {quantity} units but only {product.stock} are available"
        )
    product.stock -= quantity
    database.commit()
    database.refresh(product)
    return product
