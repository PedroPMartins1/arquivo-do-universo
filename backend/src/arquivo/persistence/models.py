import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSTZRANGE, Range
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from arquivo.core.epistemics import EpistemicClass, KnowledgeDomain
from arquivo.core.provenance import ProvenanceOrigin
from arquivo.temporal.precision import TemporalPrecision

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def _enum(enum_cls: type[Any], name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda members: [m.value for m in members],
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(Text)
    uri: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Statement(Base):
    """Afirmação versionada e bitemporal. Cada revisão é uma nova linha; o passado não se reescreve.

    Tempo de sistema: [recorded_at, superseded_at). Tempo de validade: valid_period.
    """

    __tablename__ = "statements"
    __table_args__ = (
        UniqueConstraint("lineage_id", "version", name="uq_statements_lineage_version"),
        CheckConstraint(
            "superseded_at IS NULL OR superseded_at >= recorded_at", name="system_time_order"
        ),
        CheckConstraint("version >= 1", name="version_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lineage_id: Mapped[uuid.UUID] = mapped_column(index=True)
    version: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    domain: Mapped[KnowledgeDomain] = mapped_column(_enum(KnowledgeDomain, "knowledge_domain"))
    epistemic_class: Mapped[EpistemicClass] = mapped_column(
        _enum(EpistemicClass, "epistemic_class")
    )
    summary: Mapped[str] = mapped_column(Text)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    provenance_origin: Mapped[ProvenanceOrigin] = mapped_column(
        _enum(ProvenanceOrigin, "provenance_origin")
    )
    provided_by: Mapped[str] = mapped_column(String(200))
    confirmed_by: Mapped[str | None] = mapped_column(String(200))
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True
    )
    method: Mapped[str | None] = mapped_column(Text)
    method_version: Mapped[str | None] = mapped_column(String(100))

    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    event_precision: Mapped[TemporalPrecision] = mapped_column(
        _enum(TemporalPrecision, "temporal_precision")
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_period: Mapped[Range[datetime] | None] = mapped_column(TSTZRANGE)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("statements.id"))


class AuditEvent(Base):
    """Trilho de auditoria só de acrescento. Não guarda conteúdo pessoal, só referências."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(64))
    correlation_id: Mapped[uuid.UUID] = mapped_column(index=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
