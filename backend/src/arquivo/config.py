from datetime import time
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from arquivo.transits.constants import MAX_REVELATIONS


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
    revelation_unlock_times: list[time] = Field(
        default_factory=lambda: [
            time(9),
            time(11),
            time(13),
            time(15),
            time(17),
        ]
    )
    pregeneration_start: time = time(3)
    pregeneration_interval_seconds: int = Field(default=900, ge=60)
    pregeneration_workers: int = Field(default=4, ge=1)
    pregeneration_max_failures: int = Field(default=3, ge=1)
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ARQUIVO_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    )
    anthropic_model: str = "claude-sonnet-5-5"

    @field_validator("revelation_unlock_times")
    @classmethod
    def _validate_revelation_unlock_times(cls, values: list[time]) -> list[time]:
        if not values:
            raise ValueError("os horários de abertura não podem estar vazios")
        if len(values) < MAX_REVELATIONS:
            raise ValueError(f"são precisos pelo menos {MAX_REVELATIONS} horários de abertura")
        if any(first >= second for first, second in pairwise(values)):
            raise ValueError("os horários de abertura têm de ser estritamente crescentes")
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings()
