from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "catalog-service"
    environment: str = "development"
    database_url: str = "sqlite:///./catalog.db"
    log_level: str = "INFO"
    seed_data: bool = True

    model_config = SettingsConfigDict(
        env_prefix="CATALOG_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
