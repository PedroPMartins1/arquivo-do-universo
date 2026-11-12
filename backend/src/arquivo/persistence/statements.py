"""Repositório de afirmações: isolamento por utilizador, histórico imutável e auditoria."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Select, cast, delete, or_, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from arquivo.core.epistemics import (
    EpistemicClass,
    EpistemicViolation,
    KnowledgeDomain,
    reclassification_issues,
    validate_classification,
)
from arquivo.core.provenance import Provenance
from arquivo.persistence.models import AuditEvent, Statement
from arquivo.temporal.intervals import Interval
from arquivo.temporal.precision import TemporalPrecision
from arquivo.temporal.stamps import Severity, TemporalStamp, check_chronology


class StatementNotFoundError(LookupError):
    pass


class ChronologyError(ValueError):
    pass


@dataclass(frozen=True)
class StatementDraft:
    domain: KnowledgeDomain
    epistemic_class: EpistemicClass
    summary: str
    provenance: Provenance
    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_time: datetime | None = None
    event_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    observed_at: datetime | None = None
    valid: Interval | None = None

    def satisfied_metadata(self) -> set[str]:
        present = {key for key, value in self.metadata.items() if value not in (None, "", [], {})}
        return present | self.provenance.metadata_keys()


def _utcnow() -> datetime:
    return datetime.now(UTC)


class StatementRepository:
    def __init__(
        self,
        session: Session,
        *,
        owner_id: uuid.UUID,
        actor: str,
        correlation_id: uuid.UUID | None = None,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._session = session
        self._owner_id = owner_id
        self._actor = actor
        self._correlation_id = correlation_id or uuid.uuid4()
        self._clock = clock

    def record(self, draft: StatementDraft) -> Statement:
        now = self._clock()
        self._validate(draft, now)
        statement = self._build(draft, lineage_id=uuid.uuid4(), version=1, recorded_at=now)
        self._session.add(statement)
        self._session.flush()
        self._audit("statement.recorded", statement, {"version": 1})
        return statement

    def revise(self, lineage_id: uuid.UUID, draft: StatementDraft) -> Statement:
        current = self.current(lineage_id)
        if current is None:
            raise StatementNotFoundError(lineage_id)
        now = self._clock()
        self._validate(draft, now)
        has_new_source = (
            draft.provenance.source_id is not None
            and draft.provenance.source_id != str(current.source_id)
        )
        issues = reclassification_issues(
            current.epistemic_class, draft.epistemic_class, has_new_source=has_new_source
        )
        if issues:
            raise EpistemicViolation(issues)

        revised = self._build(
            draft, lineage_id=lineage_id, version=current.version + 1, recorded_at=now
        )
        self._session.add(revised)
        self._session.flush()
        current.superseded_at = now
        current.superseded_by = revised.id
        self._session.flush()
        self._audit(
            "statement.revised",
            revised,
            {"version": revised.version, "previous_id": str(current.id)},
        )
        return revised

    def current(self, lineage_id: uuid.UUID) -> Statement | None:
        return self._session.scalar(
            self._owned().where(
                Statement.lineage_id == lineage_id, Statement.superseded_at.is_(None)
            )
        )

    def history(self, lineage_id: uuid.UUID) -> list[Statement]:
        query = self._owned().where(Statement.lineage_id == lineage_id).order_by(Statement.version)
        return list(self._session.scalars(query))

    def as_known_at(self, lineage_id: uuid.UUID, known_at: datetime) -> Statement | None:
        """A versão que o sistema conhecia num dado instante (tempo de sistema)."""
        return self._session.scalar(
            self._owned().where(Statement.lineage_id == lineage_id, *self._known_at(known_at))
        )

    def valid_at(self, instant: datetime, *, known_at: datetime | None = None) -> list[Statement]:
        """Afirmações válidas no mundo num instante, tal como conhecidas em `known_at`."""
        known = known_at or self._clock()
        query = self._owned().where(
            Statement.valid_period.op("@>")(cast(instant, DateTime(timezone=True))),
            *self._known_at(known),
        )
        return list(self._session.scalars(query.order_by(Statement.recorded_at)))

    def erase(self, lineage_id: uuid.UUID) -> int:
        """Eliminação a pedido do utilizador: remove todas as versões (§13.5)."""
        result = self._session.execute(
            delete(Statement).where(
                Statement.owner_id == self._owner_id, Statement.lineage_id == lineage_id
            )
        )
        count = int(result.rowcount)  # type: ignore[attr-defined]
        if count == 0:
            raise StatementNotFoundError(lineage_id)
        self._session.add(
            AuditEvent(
                owner_id=self._owner_id,
                actor=self._actor,
                action="statement.erased",
                entity_type="statement_lineage",
                entity_id=str(lineage_id),
                correlation_id=self._correlation_id,
                details={"versions": count},
            )
        )
        self._session.flush()
        return count

    def _owned(self) -> Select[Statement]:
        return select(Statement).where(Statement.owner_id == self._owner_id)

    @staticmethod
    def _known_at(known_at: datetime) -> tuple[Any, ...]:
        return (
            Statement.recorded_at <= known_at,
            or_(Statement.superseded_at.is_(None), Statement.superseded_at > known_at),
        )

    def _validate(self, draft: StatementDraft, now: datetime) -> None:
        validate_classification(draft.epistemic_class, draft.domain, draft.satisfied_metadata())
        stamp = TemporalStamp(
            event_time=draft.event_time,
            event_precision=draft.event_precision,
            observed_at=draft.observed_at,
            recorded_at=now,
            valid=draft.valid,
        )
        errors = [i for i in check_chronology(stamp, now=now) if i.severity is Severity.ERROR]
        if errors:
            raise ChronologyError("; ".join(i.message for i in errors))

    def _build(
        self,
        draft: StatementDraft,
        *,
        lineage_id: uuid.UUID,
        version: int,
        recorded_at: datetime,
    ) -> Statement:
        provenance = draft.provenance
        valid_period = (
            Range(draft.valid.start, draft.valid.end, bounds="[)") if draft.valid else None
        )
        return Statement(
            id=uuid.uuid4(),
            lineage_id=lineage_id,
            version=version,
            owner_id=self._owner_id,
            domain=draft.domain,
            epistemic_class=draft.epistemic_class,
            summary=draft.summary,
            content=draft.content,
            metadata_=draft.metadata,
            provenance_origin=provenance.origin,
            provided_by=provenance.provided_by,
            confirmed_by=provenance.confirmed_by,
            source_id=uuid.UUID(provenance.source_id) if provenance.source_id else None,
            method=provenance.method,
            method_version=provenance.method_version,
            event_time=draft.event_time,
            event_precision=draft.event_precision,
            observed_at=draft.observed_at,
            valid_period=valid_period,
            recorded_at=recorded_at,
        )

    def _audit(self, action: str, statement: Statement, details: dict[str, Any]) -> None:
        self._session.add(
            AuditEvent(
                owner_id=self._owner_id,
                actor=self._actor,
                action=action,
                entity_type="statement",
                entity_id=str(statement.id),
                correlation_id=self._correlation_id,
                details={"lineage_id": str(statement.lineage_id), **details},
            )
        )
        self._session.flush()
