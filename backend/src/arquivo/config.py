import ipaddress
from datetime import time
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# As leituras históricas podem conter cinco revelações.
_MIN_UNLOCK_TIMES = 5

DEVELOPMENT_AUTH_RATE_LIMIT_KEY = "arquivo-development-only-rate-limit-key-not-for-production"


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
    model_config = SettingsConfigDict(
        env_prefix="ARQUIVO_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://arquivo:arquivo@localhost:5432/arquivo"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    trusted_proxies: list[str] = Field(default_factory=list)
    auth_rate_limit_key: SecretStr | None = None
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
    resend_api_key: SecretStr | None = None
    recovery_email_from: str = "Arquivo do Universo <onboarding@resend.dev>"
    public_url: str | None = None

    @field_validator("public_url")
    @classmethod
    def _validate_public_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("o endereço público exige uma origem HTTPS")
        return value.rstrip("/")

    @field_validator("cors_origins")
    @classmethod
    def _validate_cors_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            if not origin or "*" in origin or any(character.isspace() for character in origin):
                raise ValueError("cada origem CORS tem de ser uma origem explícita")
            if any(character in origin for character in "?#"):
                raise ValueError("as origens CORS não podem incluir caminho, consulta ou fragmento")
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.netloc
                or not parsed.hostname
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username is not None
                or parsed.password is not None
            ):
                raise ValueError("cada origem CORS tem de ser scheme://host[:port]")
            try:
                port = parsed.port
            except ValueError as error:
                raise ValueError("a porta de uma origem CORS é inválida") from error
            if parsed.netloc.endswith(":") and port is None:
                raise ValueError("a porta de uma origem CORS é inválida")
        return origins

    @field_validator("trusted_proxies")
    @classmethod
    def _validate_trusted_proxies(cls, proxies: list[str]) -> list[str]:
        for proxy in proxies:
            if not proxy or "*" in proxy:
                raise ValueError("cada proxy de confiança tem de ser um IP ou uma rede CIDR")
            try:
                network = ipaddress.ip_network(proxy, strict=False)
            except ValueError as error:
                raise ValueError(
                    "cada proxy de confiança tem de ser um IP ou uma rede CIDR"
                ) from error
            if network.prefixlen == 0:
                raise ValueError("a rede de proxies de confiança tem de ser específica")
        return proxies

    @model_validator(mode="after")
    def _validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if not self.cors_origins:
                raise ValueError("a produção exige pelo menos uma origem CORS")
            if any(urlsplit(origin).scheme != "https" for origin in self.cors_origins):
                raise ValueError("a produção só permite origens CORS HTTPS")
            secret = self.auth_rate_limit_key.get_secret_value() if self.auth_rate_limit_key else ""
            if len(secret.strip()) < 32 or secret.strip() == DEVELOPMENT_AUTH_RATE_LIMIT_KEY:
                raise ValueError(
                    "a produção exige uma chave própria com pelo menos 32 caracteres em "
                    "ARQUIVO_AUTH_RATE_LIMIT_KEY"
                )
        return self

    @field_validator("revelation_unlock_times")
    @classmethod
    def _validate_revelation_unlock_times(cls, values: list[time]) -> list[time]:
        if not values:
            raise ValueError("os horários de abertura não podem estar vazios")
        if len(values) < _MIN_UNLOCK_TIMES:
            raise ValueError(f"são precisos pelo menos {_MIN_UNLOCK_TIMES} horários de abertura")
        if any(first >= second for first, second in pairwise(values)):
            raise ValueError("os horários de abertura têm de ser estritamente crescentes")
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings()
