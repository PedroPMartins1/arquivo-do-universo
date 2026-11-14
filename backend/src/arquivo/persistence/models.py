import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    MetaData,
    SmallInteger,
    String,
    Text,
    Time,
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
    password_hash: Mapped[str | None] = mapped_column(String(255))
    residence_name: Mapped[str | None] = mapped_column(String(200))
    residence_zone: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthSession(Base):
    """Sessão de autenticação. Só se guarda o hash SHA-256 do token, nunca o token."""

    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Place(Base):
    """Localidade do GeoNames (CC BY 4.0). `search_text` = nomes normalizados entre `|`."""

    __tablename__ = "places"
    __table_args__ = (
        Index(
            "ix_places_search_text_trgm",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
    )

    geoname_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(200))
    region: Mapped[str | None] = mapped_column(String(200))
    country_code: Mapped[str] = mapped_column(String(2))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    zone: Mapped[str] = mapped_column(String(64))
    population: Mapped[int] = mapped_column(BigInteger)
    search_text: Mapped[str] = mapped_column(Text)


class BirthProfile(Base):
    """Dados de nascimento exatos (D-020). Um perfil por utilizador."""

    __tablename__ = "birth_profiles"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        CheckConstraint("occurrence IS NULL OR occurrence IN (0, 1)", name="occurrence_values"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    birth_date: Mapped[date] = mapped_column(Date)
    birth_time: Mapped[time] = mapped_column(Time)
    place_name: Mapped[str] = mapped_column(String(200))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    zone: Mapped[str] = mapped_column(String(64))
    occurrence: Mapped[int | None] = mapped_column(Integer)
    birth_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tzdata_version: Mapped[str | None] = mapped_column(String(32))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Interpretation(Base):
    __tablename__ = "interpretations"
    __table_args__ = (
        CheckConstraint("kind IN ('natal', 'day')", name="kind_values"),
        UniqueConstraint(
            "user_id",
            "kind",
            "day",
            "facts_hash",
            name="uq_interpretations_user_kind_day_facts_hash",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(8))
    day: Mapped[date | None] = mapped_column(Date)
    facts_hash: Mapped[str] = mapped_column(CHAR(64))
    prompt_version: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(200))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reflection(Base):
    __tablename__ = "reflections"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "day",
            "slot",
            name="uq_reflections_user_day_slot",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("slot IS NULL OR slot BETWEEN 0 AND 4", name="slot_range"),
        CheckConstraint("char_length(body) BETWEEN 1 AND 5000", name="body_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date)
    slot: Mapped[int | None] = mapped_column(SmallInteger)
    question: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


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
