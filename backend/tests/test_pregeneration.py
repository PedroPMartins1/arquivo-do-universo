import json
from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from typing import cast
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from arquivo import pregeneration
from arquivo.api.deps import get_db, get_now, get_text_model
from arquivo.config import Settings
from arquivo.interpretation.model import InterpretationUnavailable
from arquivo.main import create_app
from arquivo.natal.settings import Body, Sign
from arquivo.persistence.models import (
    AuditEvent,
    AuthSession,
    BirthProfile,
    Interpretation,
    User,
)
from arquivo.transits.engine import DailySky, EventKind, Revelation, SkyEvent, TransitCalculation

pytestmark = pytest.mark.db

NOW = datetime(2026, 11, 17, 4, tzinfo=UTC)


def reading_response() -> str:
    return json.dumps(
        {
            "tema": "Ritmo do dia",
            "revelacoes": [
                {
                    "titulo": f"Leitura {index}",
                    "texto": f"Vale a pena olhar para esta ideia com atenção ({index}).",
                    "pergunta": "Que ideia merece atenção?",
                }
                for index in range(5)
            ],
            "amanha": None,
        }
    )


class FakeModel:
    name = "fake-claude"

    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.calls = 0

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        self.calls += 1
        return self.responses.pop(0)


class FailingModel:
    name = "fake-claude"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        self.calls += 1
        raise InterpretationUnavailable("transitório")


class FirstFailureModel(FakeModel):
    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        self.calls += 1
        if self.calls <= 3:
            raise InterpretationUnavailable("transitório")
        return reading_response()


@pytest.fixture
def test_sessionmaker(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> Iterator[sessionmaker[Session]]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(pregeneration, "get_sessionmaker", lambda: factory)
    with factory() as db, db.begin():
        db.execute(delete(AuditEvent))
        db.execute(delete(User).where(User.email.like("pregen-test-%")))
        db.execute(delete(User).where(User.email == "pregeneration@example.org"))
    yield factory
    with factory() as db, db.begin():
        db.execute(delete(AuditEvent))
        db.execute(delete(User).where(User.email.like("pregen-test-%")))
        db.execute(delete(User).where(User.email == "pregeneration@example.org"))


def create_user(
    factory: sessionmaker[Session],
    *,
    user_id: UUID | None = None,
    residence_zone: str | None = "Europe/Lisbon",
    birth: bool = True,
    expires_at: datetime = datetime(2026, 12, 1, tzinfo=UTC),
) -> UUID:
    user_id = user_id or uuid4()
    with factory() as db, db.begin():
        user = User(
            id=user_id,
            email=f"pregen-test-{user_id}@example.org",
            display_name="Teste",
            password_hash=None,
            residence_zone=residence_zone,
        )
        db.add(user)
        db.flush()
        if birth:
            db.add(
                BirthProfile(
                    user_id=user_id,
                    birth_date=date(1993, 5, 20),
                    birth_time=time(14, 35),
                    place_name="Lisboa",
                    latitude=38.7223,
                    longitude=-9.1393,
                    zone="Europe/Lisbon",
                    occurrence=None,
                    birth_utc=datetime(1993, 5, 20, 13, 35, tzinfo=UTC),
                )
            )
        db.add(
            AuthSession(
                user_id=user_id,
                token_hash=uuid4().hex + uuid4().hex,
                expires_at=expires_at,
            )
        )
    return user_id


def five_revelations(day: date, zone: str) -> DailySky:
    local_zone = ZoneInfo(zone)
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime.combine(day, time(9), tzinfo=local_zone),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    return DailySky(
        date=day,
        zone=zone,
        day_starts=datetime.combine(day, time.min, tzinfo=local_zone),
        day_ends=datetime.combine(day + timedelta(days=1), time.min, tzinfo=local_zone),
        revelations=[Revelation(weight=1, event=event) for _ in range(5)],
        tomorrow=None,
        active=[],
        upcoming=[],
        events=[],
        calculation=TransitCalculation(orbs={}, aspects=[]),
    )


def patch_daily_sky(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "arquivo.api.profile.daily_sky",
        lambda chart, day, zone: five_revelations(day, zone),
    )


def test_pregenerates_and_request_uses_cached_reading(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    now = NOW
    model = FakeModel(reading_response())
    app = create_app()

    def override_db() -> Iterator[Session]:
        with test_sessionmaker() as db, db.begin():
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_now] = lambda: now
    app.dependency_overrides[get_text_model] = lambda: model
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "pregeneration@example.org",
                    "password": "palavra-passe-longa",
                    "display_name": "Teste",
                },
            ).status_code
            == 201
        )
        assert (
            client.put(
                "/api/v1/me/birth",
                json={
                    "birth_date": "1993-05-20",
                    "birth_time": "14:35",
                    "place_name": "Lisboa",
                    "latitude": 38.7223,
                    "longitude": -9.1393,
                    "zone": "Europe/Lisbon",
                },
            ).status_code
            == 200
        )
        assert (
            client.put(
                "/api/v1/me/residence",
                json={"place_name": "Lisboa", "zone": "Europe/Lisbon"},
            ).status_code
            == 200
        )
        patch_daily_sky(monkeypatch)
        report = pregeneration.Pregenerator(Settings(pregeneration_workers=1)).run_pass(now, model)
        assert report == pregeneration.PassReport(generated=1, failed=0, skipped_after_failures=0)
        assert model.calls == 1

        with test_sessionmaker() as db:
            row = db.scalar(select(Interpretation).where(Interpretation.kind == "day"))
            audit = db.scalar(
                select(AuditEvent).where(AuditEvent.action == "interpretation.generated")
            )
            assert row is not None and row.day == date(2026, 11, 17)
            assert audit is not None and audit.details["trigger"] == "pregeneration"

        empty_model = FakeModel()
        cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: empty_model
        response = client.get("/api/v1/me/reading/today")
        assert response.status_code == 200
        assert empty_model.calls == 0


def test_before_local_start_does_nothing(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    user_id = create_user(test_sessionmaker)
    model = FakeModel()
    patch_daily_sky(monkeypatch)
    report = pregeneration.Pregenerator().run_pass(datetime(2026, 11, 17, 2, 59, tzinfo=UTC), model)
    assert report == pregeneration.PassReport(0, 0, 0)
    assert model.calls == 0
    with test_sessionmaker() as db:
        assert (
            db.scalar(
                select(Interpretation.id).where(
                    Interpretation.user_id == user_id,
                    Interpretation.kind == "day",
                )
            )
            is None
        )


def test_residence_zone_determines_the_day(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    lisbon = create_user(test_sessionmaker, residence_zone="Europe/Lisbon")
    auckland = create_user(test_sessionmaker, residence_zone="Pacific/Auckland")
    model = FakeModel(reading_response(), reading_response())
    patch_daily_sky(monkeypatch)
    now = datetime(2026, 11, 17, 14, 30, tzinfo=UTC)
    report = pregeneration.Pregenerator(Settings(pregeneration_workers=1)).run_pass(now, model)
    assert report.generated == 2
    assert model.calls == 2
    with test_sessionmaker() as db:
        days = dict(
            db.execute(
                select(Interpretation.user_id, Interpretation.day).where(
                    Interpretation.kind == "day"
                )
            ).all()
        )
    assert days[lisbon] == date(2026, 11, 17)
    assert days[auckland] == date(2026, 11, 18)


def test_existing_day_row_is_not_regenerated(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    user_id = create_user(test_sessionmaker)
    with test_sessionmaker() as db, db.begin():
        db.add(
            Interpretation(
                user_id=user_id,
                kind="day",
                day=date(2026, 11, 17),
                facts_hash="a" * 64,
                prompt_version="old",
                model="old",
                content={},
            )
        )
    model = FakeModel()
    report = pregeneration.Pregenerator().run_pass(NOW, model)
    assert report == pregeneration.PassReport(0, 0, 0)
    assert model.calls == 0


def test_birth_profile_and_unexpired_session_are_required(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    create_user(test_sessionmaker, birth=False)
    create_user(test_sessionmaker, expires_at=datetime(2026, 11, 17, 3, tzinfo=UTC))
    model = FakeModel()
    patch_daily_sky(monkeypatch)
    report = pregeneration.Pregenerator().run_pass(NOW, model)
    assert report == pregeneration.PassReport(0, 0, 0)
    assert model.calls == 0


def test_failures_are_isolated_and_capped(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    user_a = create_user(test_sessionmaker, user_id=UUID(int=1))
    user_b = create_user(test_sessionmaker, user_id=UUID(int=2))
    model = FirstFailureModel()
    patch_daily_sky(monkeypatch)
    pregenerator_instance = pregeneration.Pregenerator(Settings(pregeneration_workers=1))
    report = pregenerator_instance.run_pass(NOW, model)
    assert report == pregeneration.PassReport(generated=1, failed=1, skipped_after_failures=0)
    with test_sessionmaker() as db:
        generated_user = db.scalar(
            select(Interpretation.user_id).where(Interpretation.kind == "day")
        )
    assert generated_user == user_b
    assert generated_user != user_a


def test_failure_cap_skips_user_after_max_attempts(
    test_sessionmaker: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    create_user(test_sessionmaker)
    patch_daily_sky(monkeypatch)
    failing_model = FailingModel()
    capped = pregeneration.Pregenerator(
        Settings(pregeneration_workers=1, pregeneration_max_failures=3)
    )
    for _ in range(3):
        assert capped.run_pass(NOW, failing_model).failed == 1
    final = capped.run_pass(NOW, failing_model)
    assert final == pregeneration.PassReport(0, 0, 1)
    assert failing_model.calls == 9


def test_main_continues_after_pass_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopLoop(Exception):
        pass

    model = FakeModel()
    monkeypatch.setattr(pregeneration, "get_text_model", lambda: model)
    pass_count = 0

    def run_pass(
        self: pregeneration.Pregenerator, now: datetime, model: FakeModel
    ) -> pregeneration.PassReport:
        nonlocal pass_count
        pass_count += 1
        if pass_count == 1:
            raise RuntimeError("pass failed")
        return pregeneration.PassReport(generated=1, failed=0, skipped_after_failures=0)

    sleep_count = 0

    def stop_after_second_sleep(seconds: int) -> None:
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count == 2:
            raise StopLoop

    monkeypatch.setattr(pregeneration.Pregenerator, "run_pass", run_pass)
    monkeypatch.setattr("arquivo.pregeneration.time_module.sleep", stop_after_second_sleep)
    with pytest.raises(StopLoop):
        pregeneration.main([])
    assert pass_count == 2
    assert sleep_count == 2


def test_main_once_returns_one_when_pass_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = FakeModel()
    monkeypatch.setattr(pregeneration, "get_text_model", lambda: model)

    def fail_pass(
        self: pregeneration.Pregenerator, now: datetime, model: FakeModel
    ) -> pregeneration.PassReport:
        raise RuntimeError("pass failed")

    monkeypatch.setattr(pregeneration.Pregenerator, "run_pass", fail_pass)
    assert pregeneration.main(["--once"]) == 1
