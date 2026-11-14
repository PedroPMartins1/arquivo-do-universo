import json
from collections.abc import Iterator
from datetime import date, datetime, time, timedelta
from typing import cast
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from arquivo.api.deps import get_db, get_now, get_text_model
from arquivo.api.reading import _store
from arquivo.interpretation.prompts import NATAL_SECTIONS
from arquivo.main import create_app
from arquivo.natal.settings import Body, Sign
from arquivo.persistence.models import Interpretation, User
from arquivo.transits.engine import DailySky, EventKind, Revelation, SkyEvent, TransitCalculation

pytestmark = pytest.mark.db

BIRTH = {
    "birth_date": "1993-05-20",
    "birth_time": "14:35",
    "place_name": "Lisboa",
    "latitude": 38.7223,
    "longitude": -9.1393,
}


class FakeModel:
    name = "fake-claude"

    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.calls = 0

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        self.calls += 1
        return self.responses.pop(0)


def natal_response() -> str:
    return json.dumps(
        {"secoes": [{"id": identifier, "texto": "Sol"} for identifier, _, _ in NATAL_SECTIONS]}
    )


def today_response() -> str:
    return json.dumps(
        {
            "tema": "Ritmo do dia",
            "revelacoes": [
                {
                    "titulo": f"marcador_titulo_{index}",
                    "texto": f"marcador_texto_{index}",
                    "pergunta": f"marcador_pergunta_{index}",
                }
                for index in range(5)
            ],
            "amanha": None,
        }
    )


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


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app = create_app()

    def _db() -> Iterator[Session]:
        yield session
        session.flush()

    app.dependency_overrides[get_db] = _db
    yield TestClient(app)


def _register_and_save_birth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "leitura@example.org",
            "password": "palavra-passe-longa",
            "display_name": "Leitora",
        },
    )
    assert response.status_code == 201
    assert client.put("/api/v1/me/birth", json=BIRTH).status_code == 200


def test_natal_reading_is_unavailable_without_a_model(client: TestClient) -> None:
    _register_and_save_birth(client)
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: None
    response = client.get("/api/v1/me/reading/natal")
    assert response.status_code == 503
    assert response.json()["detail"] == "a interpretação por IA ainda não está configurada"


def test_natal_reading_is_cached_and_birth_change_generates_again(
    client: TestClient, session: Session
) -> None:
    _register_and_save_birth(client)
    model = FakeModel(natal_response(), natal_response())
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: model

    first = client.get("/api/v1/me/reading/natal")
    second = client.get("/api/v1/me/reading/natal")
    assert first.status_code == second.status_code == 200
    assert first.json()["epistemic_class"] == "interpretation"
    assert first.json()["note"].startswith("Interpretação simbólica")
    assert model.calls == 1

    updated = client.put("/api/v1/me/birth", json=BIRTH | {"birth_date": "1994-05-20"})
    assert updated.status_code == 200
    changed = client.get("/api/v1/me/reading/natal")
    assert changed.status_code == 200
    assert model.calls == 2
    rows = session.scalars(select(Interpretation)).all()
    assert len(rows) == 2


def test_store_returns_existing_row_after_unique_conflict(
    client: TestClient, session: Session
) -> None:
    _register_and_save_birth(client)
    user = session.scalar(select(User))
    assert user is not None
    facts_hash = "a" * 64
    existing = Interpretation(
        user_id=user.id,
        kind="natal",
        day=None,
        facts_hash=facts_hash,
        prompt_version="2026-11-14.2",
        model="fake-claude",
        content={"sections": []},
    )
    session.add(existing)
    session.flush()

    returned = _store(
        session,
        user,
        "natal",
        None,
        facts_hash,
        FakeModel(),
        {"sections": [{"id": "new"}]},
        generated=True,
    )
    assert returned.id == existing.id
    assert session.scalars(select(Interpretation)).all() == [existing]


def test_deleting_account_cascades_interpretations(client: TestClient, session: Session) -> None:
    _register_and_save_birth(client)
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: FakeModel(
        natal_response()
    )
    assert client.get("/api/v1/me/reading/natal").status_code == 200
    assert session.scalars(select(Interpretation)).all()
    assert client.delete("/api/v1/me").status_code == 204
    assert session.scalars(select(Interpretation)).all() == []


def test_today_reading_rejects_dates_outside_ephemeris_range(client: TestClient) -> None:
    _register_and_save_birth(client)
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: FakeModel()
    response = client.get("/api/v1/me/reading/today", params={"date": "1800-12-31"})
    assert response.status_code == 422


def test_today_and_reading_redact_revelations_until_unlock(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register_and_save_birth(client)
    now = datetime(2026, 11, 16, 11, tzinfo=ZoneInfo("Europe/Lisbon"))
    cast(FastAPI, client.app).dependency_overrides[get_now] = lambda: now
    monkeypatch.setattr(
        "arquivo.api.profile.daily_sky",
        lambda chart, day, zone: five_revelations(day, zone),
    )
    model = FakeModel(today_response())
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: model

    sky = client.get("/api/v1/me/today", params={"date": "2026-11-16"})
    assert sky.status_code == 200
    sky_json = sky.json()
    assert datetime.fromisoformat(sky_json["now"].replace("Z", "+00:00")).hour == 11
    revelation = sky_json["revelations"][0]["revelation"]
    assert revelation["focus"] is None
    assert revelation["supporting"] == []
    assert revelation["event"]["other_body"] is None
    assert revelation["event"]["aspect"] is None
    unlock_hours = [
        datetime.fromisoformat(slot["unlocks_at"].replace("Z", "+00:00")).hour
        for slot in sky_json["revelations"]
    ]
    assert unlock_hours == [7, 10, 13, 16, 19]
    assert [slot["revelation"] is not None for slot in sky_json["revelations"]] == [
        True,
        True,
        False,
        False,
        False,
    ]

    reading = client.get("/api/v1/me/reading/today", params={"date": "2026-11-16"})
    assert reading.status_code == 200, reading.text
    reading_json = reading.json()
    assert [revelation is not None for revelation in reading_json["revelations"]] == [
        True,
        True,
        False,
        False,
        False,
    ]
    for index in range(2, 5):
        assert f"marcador_titulo_{index}" not in reading.text
        assert f"marcador_texto_{index}" not in reading.text
        assert f"marcador_pergunta_{index}" not in reading.text
    assert model.calls == 1


def test_today_past_is_open_and_future_is_locked(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register_and_save_birth(client)
    now = datetime(2026, 11, 16, 11, tzinfo=ZoneInfo("Europe/Lisbon"))
    cast(FastAPI, client.app).dependency_overrides[get_now] = lambda: now
    monkeypatch.setattr(
        "arquivo.api.profile.daily_sky",
        lambda chart, day, zone: five_revelations(day, zone),
    )
    past = client.get("/api/v1/me/today", params={"date": "2026-11-15"}).json()
    future = client.get("/api/v1/me/today", params={"date": "2026-11-17"}).json()
    assert all(slot["revelation"] is not None for slot in past["revelations"])
    assert all(slot["revelation"] is None for slot in future["revelations"])
