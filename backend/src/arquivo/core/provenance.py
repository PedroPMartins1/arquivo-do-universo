"""Proveniência obrigatória de cada informação (dossiê §13.5)."""

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict


class ProvenanceOrigin(StrEnum):
    USER_REPORTED = "user_reported"
    DOCUMENTED = "documented"
    SYSTEM_DERIVED = "system_derived"
    EXTERNAL = "external"


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    origin: ProvenanceOrigin
    provided_by: str
    source_id: str | None = None
    confirmed_by: str | None = None
    method: str | None = None
    method_version: str | None = None
    retrieved_at: AwareDatetime | None = None
    notes: str | None = None

    def metadata_keys(self) -> set[str]:
        """Chaves de metadados que esta proveniência satisfaz (ver REQUIRED_METADATA)."""
        keys: set[str] = set()
        if self.source_id is not None:
            keys.add("source")
        if self.method is not None:
            keys.add("method")
        return keys


def is_trusted_instruction_source(origin: ProvenanceOrigin) -> bool:
    """Conteúdo externo é dado não confiável e nunca altera instruções internas (§16, §28)."""
    return origin is not ProvenanceOrigin.EXTERNAL
