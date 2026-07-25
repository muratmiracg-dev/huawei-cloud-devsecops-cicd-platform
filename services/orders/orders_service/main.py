from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from orders_service.api import router
from orders_service.config import get_settings
from orders_service.database import Base, engine
from orders_service.metrics import metrics_middleware

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Commerce Orders Service",
    version="0.1.0",
    description="Idempotent order creation API backed by the catalog service.",
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
