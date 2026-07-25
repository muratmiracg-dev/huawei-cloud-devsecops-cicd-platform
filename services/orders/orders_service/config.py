from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "orders-service"
    environment: str = "development"
    database_url: str = "sqlite:///./orders.db"
    catalog_base_url: str = "http://localhost:8001"
    catalog_timeout_seconds: float = 3.0
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="ORDERS_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
