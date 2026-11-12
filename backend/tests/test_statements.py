import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from arquivo.core.epistemics import EpistemicClass, EpistemicViolation, KnowledgeDomain
from arquivo.core.provenance import Provenance, ProvenanceOrigin
from arquivo.persistence.models import AuditEvent, Source, Statement, User
from arquivo.persistence.statements import (
    ChronologyError,
    StatementDraft,
    StatementNotFoundError,
    StatementRepository,
)
from arquivo.temporal.intervals import Interval
from arquivo.temporal.precision import TemporalPrecision

pytestmark = pytest.mark.db

T0 = datetime(2026, 1, 1, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs: float) -> datetime:
        self.now += timedelta(**kwargs)
        return self.now


def make_user(session: Session, name: str) -> User:
    user = User(email=f"{name}-{uuid.uuid4().hex[:6]}@example.test", display_name=name)
    session.add(user)
    session.flush()
    return user


def hypothesis(summary: str = "Prefere trabalhar de manhã") -> StatementDraft:
    return StatementDraft(
        domain=KnowledgeDomain.PERSONAL,
        epistemic_class=EpistemicClass.HYPOTHESIS,
        summary=summary,
        provenance=Provenance(origin=ProvenanceOrigin.SYSTEM_DERIVED, provided_by="sistema"),
    )


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def repo_for(session: Session, clock: Clock) -> Callable[[User], StatementRepository]:
    def build(user: User) -> StatementRepository:
        return StatementRepository(session, owner_id=user.id, actor="teste", clock=clock)

    return build


def test_record_and_revise_keeps_history(
    session: Session, clock: Clock, repo_for: Callable[[User], StatementRepository]
) -> None:
    repo = repo_for(make_user(session, "ana"))
    first = repo.record(hypothesis())
    clock.advance(days=1)
    second = repo.revise(first.lineage_id, hypothesis("Prefere trabalhar à tarde"))

    history = repo.history(first.lineage_id)
    assert [s.version for s in history] == [1, 2]
    assert history[0].summary == "Prefere trabalhar de manhã"
    assert history[0].superseded_by == second.id
    assert repo.current(first.lineage_id) == second
    assert repo.as_known_at(first.lineage_id, T0 + timedelta(hours=1)) == first
    assert repo.as_known_at(first.lineage_id, clock.now) == second
    assert repo.as_known_at(first.lineage_id, T0 - timedelta(seconds=1)) is None


def test_users_are_isolated(
    session: Session, repo_for: Callable[[User], StatementRepository]
) -> None:
    ana = repo_for(make_user(session, "ana"))
    rui = repo_for(make_user(session, "rui"))
    statement = ana.record(hypothesis())

    assert rui.current(statement.lineage_id) is None
    assert rui.history(statement.lineage_id) == []
    with pytest.raises(StatementNotFoundError):
        rui.revise(statement.lineage_id, hypothesis("intrusão"))
    with pytest.raises(StatementNotFoundError):
        rui.erase(statement.lineage_id)
    assert ana.current(statement.lineage_id) is not None


def test_inference_cannot_become_fact_without_new_source(
    session: Session, repo_for: Callable[[User], StatementRepository]
) -> None:
    user = make_user(session, "ana")
    repo = repo_for(user)
    inference = repo.record(
        StatementDraft(
            domain=KnowledgeDomain.PERSONAL,
            epistemic_class=EpistemicClass.INFERENCE,
            summary="Mudou de emprego em 2020",
            provenance=Provenance(
                origin=ProvenanceOrigin.SYSTEM_DERIVED, provided_by="sistema", method="cronologia"
            ),
            metadata={"assumptions": ["datas do CV estão corretas"]},
        )
    )
    as_fact = StatementDraft(
        domain=KnowledgeDomain.PERSONAL,
        epistemic_class=EpistemicClass.DOCUMENTED_FACT,
        summary="Mudou de emprego em 2020",
        provenance=Provenance(origin=ProvenanceOrigin.USER_REPORTED, provided_by="ana"),
    )
    with pytest.raises(EpistemicViolation):
        repo.revise(inference.lineage_id, as_fact)

    source = Source(owner_id=user.id, kind="document", title="Contrato de trabalho")
    session.add(source)
    session.flush()
    documented = StatementDraft(
        domain=as_fact.domain,
        epistemic_class=as_fact.epistemic_class,
        summary=as_fact.summary,
        provenance=Provenance(
            origin=ProvenanceOrigin.DOCUMENTED, provided_by="ana", source_id=str(source.id)
        ),
    )
    revised = repo.revise(inference.lineage_id, documented)
    assert revised.epistemic_class is EpistemicClass.DOCUMENTED_FACT


def test_astrology_cannot_be_stored_as_prediction(
    session: Session, repo_for: Callable[[User], StatementRepository]
) -> None:
    repo = repo_for(make_user(session, "ana"))
    with pytest.raises(EpistemicViolation):
        repo.record(
            StatementDraft(
                domain=KnowledgeDomain.ASTROLOGY,
                epistemic_class=EpistemicClass.PREDICTION,
                summary="Trânsito indica mudança",
                provenance=Provenance(origin=ProvenanceOrigin.SYSTEM_DERIVED, provided_by="s"),
                metadata={"horizon": "1y", "model": "x", "uncertainty": "y"},
            )
        )


def test_rejects_chronology_errors(
    session: Session, clock: Clock, repo_for: Callable[[User], StatementRepository]
) -> None:
    repo = repo_for(make_user(session, "ana"))
    future = hypothesis()
    object.__setattr__(future, "observed_at", clock.now + timedelta(days=2))
    with pytest.raises(ChronologyError):
        repo.record(future)


def test_valid_at_is_bitemporal(
    session: Session, clock: Clock, repo_for: Callable[[User], StatementRepository]
) -> None:
    repo = repo_for(make_user(session, "ana"))
    lived_in_porto = StatementDraft(
        domain=KnowledgeDomain.PERSONAL,
        epistemic_class=EpistemicClass.HYPOTHESIS,
        summary="Viveu no Porto",
        provenance=Provenance(origin=ProvenanceOrigin.USER_REPORTED, provided_by="ana"),
        event_time=datetime(2010, 1, 1, tzinfo=UTC),
        event_precision=TemporalPrecision.YEAR,
        valid=Interval(
            start=datetime(2010, 1, 1, tzinfo=UTC), end=datetime(2015, 1, 1, tzinfo=UTC)
        ),
    )
    statement = repo.record(lived_in_porto)
    assert repo.valid_at(datetime(2012, 6, 1, tzinfo=UTC)) == [statement]
    assert repo.valid_at(datetime(2016, 6, 1, tzinfo=UTC)) == []
    assert repo.valid_at(datetime(2012, 6, 1, tzinfo=UTC), known_at=T0 - timedelta(days=1)) == []


def test_database_forbids_rewriting_history(
    session: Session, clock: Clock, repo_for: Callable[[User], StatementRepository]
) -> None:
    repo = repo_for(make_user(session, "ana"))
    first = repo.record(hypothesis())
    clock.advance(days=1)
    repo.revise(first.lineage_id, hypothesis("nova versão"))

    with pytest.raises(DBAPIError, match="immutable"), session.begin_nested():
        session.execute(
            update(Statement).where(Statement.id == first.id).values(summary="reescrito")
        )
    current = repo.current(first.lineage_id)
    assert current is not None
    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(
            update(Statement).where(Statement.id == current.id).values(summary="reescrito")
        )


def test_erase_removes_all_versions_and_is_audited(
    session: Session, clock: Clock, repo_for: Callable[[User], StatementRepository]
) -> None:
    user = make_user(session, "ana")
    repo = repo_for(user)
    first = repo.record(hypothesis())
    clock.advance(days=1)
    repo.revise(first.lineage_id, hypothesis("v2"))

    assert repo.erase(first.lineage_id) == 2
    assert repo.history(first.lineage_id) == []
    actions = session.scalars(
        select(AuditEvent.action).where(AuditEvent.owner_id == user.id).order_by(AuditEvent.id)
    ).all()
    assert actions == ["statement.recorded", "statement.revised", "statement.erased"]


def test_audit_is_append_only_but_anonymised_on_user_deletion(
    session: Session, repo_for: Callable[[User], StatementRepository]
) -> None:
    user = make_user(session, "ana")
    repo_for(user).record(hypothesis())
    event = session.scalars(select(AuditEvent).where(AuditEvent.owner_id == user.id)).one()

    with pytest.raises(DBAPIError, match="append-only"), session.begin_nested():
        session.execute(
            update(AuditEvent).where(AuditEvent.id == event.id).values(action="falsificado")
        )

    session.delete(user)
    session.flush()
    session.expire_all()
    remaining = session.get(AuditEvent, event.id)
    assert remaining is not None and remaining.owner_id is None
    assert session.scalars(select(Statement).where(Statement.owner_id == user.id)).all() == []


def test_migrations_round_trip(alembic_config: Config, database_url: str) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    from sqlalchemy import create_engine

    engine = create_engine(database_url)
    with engine.connect() as connection:
        tables = connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        ).scalars()
        assert {"users", "sources", "statements", "audit_events"} <= set(tables)
    engine.dispose()
