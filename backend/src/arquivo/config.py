from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_ephemeris_path(module_file: Path = Path(__file__), cwd: Path | None = None) -> Path:
    """`data/ephe` na raiz do repositório quando se corre a partir do código-fonte.

    Num pacote instalado essa raiz não existe: usa-se `data/ephe` no diretório de trabalho.
    Em produção, definir `ARQUIVO_EPHEMERIS_PATH` explicitamente.
    """
    root = module_file.resolve().parents[3]
    if (root / "backend" / "pyproject.toml").is_file():
        return root / "data" / "ephe"
    return (cwd or Path.cwd()) / "data" / "ephe"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARQUIVO_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://arquivo:arquivo@localhost:5432/arquivo"
    cors_origins: list[str] = ["http://localhost:5173"]
    ephemeris_path: Path = Field(default_factory=default_ephemeris_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
