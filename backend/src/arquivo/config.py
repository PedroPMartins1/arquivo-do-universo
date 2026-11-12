from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARQUIVO_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://arquivo:arquivo@localhost:5432/arquivo"
    cors_origins: list[str] = ["http://localhost:5173"]
    ephemeris_path: Path = Path(__file__).resolve().parents[3] / "data" / "ephe"


@lru_cache
def get_settings() -> Settings:
    return Settings()
