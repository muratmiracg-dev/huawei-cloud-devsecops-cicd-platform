from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import func, select, text

from catalog_service.api import router
from catalog_service.config import get_settings
from catalog_service.database import Base, SessionLocal, engine
from catalog_service.metrics import metrics_middleware
from catalog_service.models import Product

settings = get_settings()


def seed_products() -> None:
    with SessionLocal() as database:
        product_count = database.scalar(select(func.count()).select_from(Product))
        if product_count:
            return
        database.add_all(
            [
                Product(
                    sku="CLOUD-HOODIE",
                    name="Cloud Native Hoodie",
                    price=Decimal("79.90"),
                    stock=75,
                ),
                Product(
                    sku="DEVOPS-MUG",
                    name="DevOps Engineering Mug",
                    price=Decimal("19.90"),
                    stock=150,
                ),
            ]
        )
        database.commit()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    if settings.seed_data:
        seed_products()
    yield


app = FastAPI(
    title="Commerce Catalog Service",
    version="0.1.0",
    description="Product catalog and inventory reservation API.",
    lifespan=lifespan,
)
app.middleware("http")(metrics_middleware)
app.include_router(router)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive", "service": settings.service_name}


@app.get("/health/ready", tags=["health"])
def readiness(response: Response) -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not-ready", "service": settings.service_name}
    return {"status": "ready", "service": settings.service_name}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
