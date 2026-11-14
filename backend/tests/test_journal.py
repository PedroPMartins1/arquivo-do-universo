from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from typing import cast
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from arquivo.api.deps import get_db, get_now, get_text_model
from arquivo.interpretation.prompts import SYSTEM
from arquivo.interpretation.service import prompt_hash
from arquivo.main import create_app
from arquivo.natal.chart import NatalChart
from arquivo.natal.settings import Body, Sign
from arquivo.persistence.models import AuditEvent, BirthProfile, Interpretation, Reflection, User
from arquivo.transits.engine import DailySky, EventKind, Revelation, SkyEvent, TransitCalculation

pytestmark = pytest.mark.db

TODAY = date(2026, 11, 16)
NOW = datetime(2026, 11, 16, 11, tzinfo=UTC)
BIRTH = {
    "birth_date": "1993-05-20",
    "birth_time": "14:35",
    "place_name": "Lisboa",
    "latitude": 38.7223,
    "longitude": -9.1393,
    "zone": "Europe/Lisbon",
}


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app = create_app()

    def _db() -> Iterator[Session]:
        yield session
        session.flush()

    app.dependency_overrides[get_db] = _db
    yield TestClient(app)


def _set_now(client: TestClient, now: datetime) -> None:
    cast(FastAPI, client.app).dependency_overrides[get_now] = lambda: now


def _register(client: TestClient, email: str = "journal@example.org") -> UUID:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "palavra-passe-longa", "display_name": "Ana"},
    )
    assert response.status_code == 201, response.text
    user_id = UUID(client.get("/api/v1/me").json()["id"])
    assert client.put("/api/v1/me/birth", json=BIRTH).status_code == 200
    return user_id


def _content(count: int = 5) -> dict[str, object]:
    return {
        "theme": "Ritmo do dia",
        "revelations": [
            {
                "title": f"Título reservado {index}",
                "text": f"Texto reservado {index}.",
                "question": f"Pergunta guardada {index}?",
            }
            for index in range(count)
        ],
        "tomorrow": None,
    }


def _add_interpretation(
    session: Session,
    user_id: UUID,
    day: date,
    *,
    content: dict[str, object] | None = None,
    facts_hash: str | None = None,
    created_at: datetime | None = None,
) -> Interpretation:
    row = Interpretation(
        user_id=user_id,
        kind="day",
        day=day,
        facts_hash=facts_hash or f"{day:%Y%m%d}" + "0" * 56,
        prompt_version="2026-11-17.1",
        model="fake-claude",
        content=content or _content(),
        created_at=created_at,
    )
    session.add(row)
    session.flush()
    return row


def _sky(day: date, zone: str) -> DailySky:
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


def _patch_sky(monkeypatch: pytest.MonkeyPatch) -> str:
    def daily_sky(
        user: User,
        profile: BirthProfile,
        day: date | None = None,
        *,
        now: datetime | None = None,
    ) -> tuple[NatalChart, DailySky]:
        assert day is not None
        zone = user.residence_zone or profile.zone
        return cast(NatalChart, object()), _sky(day, zone)

    def day_prompt(sky: DailySky, chart: NatalChart) -> tuple[str, set[str]]:
        return f"prompt-{sky.zone}", set()

    monkeypatch.setattr("arquivo.api.journal._daily_sky", daily_sky)
    monkeypatch.setattr("arquivo.api.journal.day_prompt", day_prompt)
    return "prompt-Europe/Lisbon"


def _add_reflection(
    session: Session,
    user_id: UUID,
    day: date,
    slot: int | None,
    body: str,
) -> None:
    session.add(
        Reflection(
            user_id=user_id,
            day=day,
            slot=slot,
            question=None if slot is None else f"Pergunta guardada {slot}?",
            body=body,
        )
    )
    session.flush()


def test_note_can_be_saved_edited_listed_and_deleted(client: TestClient, session: Session) -> None:
    _register(client)
    _set_now(client, NOW)

    saved = client.put(
        f"/api/v1/me/reflections/{TODAY}/note", json={"body": "  O dia trouxe clareza.  "}
    )
    assert saved.status_code == 200
    assert saved.json()["body"] == "O dia trouxe clareza."
    assert saved.json()["slot"] is None
    assert saved.json()["question"] is None
    assert saved.json()["provenance"] == "user_reported"

    updated = client.put(
        f"/api/v1/me/reflections/{TODAY}/note", json={"body": "Escolhi avançar com calma."}
    )
    assert updated.status_code == 200
    assert updated.json()["body"] == "Escolhi avançar com calma."
    assert len(client.get(f"/api/v1/me/reflections/{TODAY}").json()) == 1

    events = session.scalars(
        select(AuditEvent).where(AuditEvent.action == "reflection.saved")
    ).all()
    assert len(events) == 2
    assert all(event.details == {"day": TODAY.isoformat(), "slot": None} for event in events)
    assert all("Escolhi" not in str(event.details) for event in events)

    assert client.delete(f"/api/v1/me/reflections/{TODAY}/note").status_code == 204
    assert client.delete(f"/api/v1/me/reflections/{TODAY}/note").status_code == 204
    assert client.get(f"/api/v1/me/reflections/{TODAY}").json() == []
    deleted = session.scalar(select(AuditEvent).where(AuditEvent.action == "reflection.deleted"))
    assert deleted is not None and deleted.details == {"day": TODAY.isoformat(), "slot": None}


@pytest.mark.parametrize("body", ["", "  \t  ", "x" * 5001])
def test_reflection_body_must_be_nonempty_and_at_most_5000_characters(
    client: TestClient, body: str
) -> None:
    _register(client)
    _set_now(client, NOW)
    response = client.put(f"/api/v1/me/reflections/{TODAY}/note", json={"body": body})
    assert response.status_code == 422


def test_reflection_body_rejects_nul_without_storing(client: TestClient, session: Session) -> None:
    _register(client)
    _set_now(client, NOW)

    response = client.put(f"/api/v1/me/reflections/{TODAY}/note", json={"body": "a\x00b"})
    assert response.status_code == 422
    assert session.scalars(select(Reflection)).all() == []


def test_future_day_cannot_be_saved(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _register(client)
    _set_now(client, NOW)
    tomorrow = TODAY + timedelta(days=1)
    note = client.put(f"/api/v1/me/reflections/{tomorrow}/note", json={"body": "Futuro"})
    revelation = client.put(
        f"/api/v1/me/reflections/{tomorrow}/revelations/0", json={"body": "Futuro"}
    )
    archive = client.get(f"/api/v1/me/archive/{tomorrow}")
    assert note.status_code == revelation.status_code == archive.status_code == 422


def test_revelation_reflection_waits_for_unlock_and_snapshots_question(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    user_id = _register(client)
    _add_interpretation(session, user_id, TODAY)
    before = datetime(2026, 11, 16, 10, 59, tzinfo=UTC)
    _set_now(client, before)
    locked = client.put(f"/api/v1/me/reflections/{TODAY}/revelations/1", json={"body": "Uma pausa"})
    assert locked.status_code == 409
    assert locked.json()["detail"] == "esta revelação ainda não abriu"

    _set_now(client, datetime(2026, 11, 16, 11, tzinfo=UTC))
    saved = client.put(f"/api/v1/me/reflections/{TODAY}/revelations/1", json={"body": "Uma pausa"})
    assert saved.status_code == 200
    assert saved.json()["question"] == "Pergunta guardada 1?"
    row = session.scalar(select(Reflection).where(Reflection.user_id == user_id))
    assert row is not None and row.slot == 1 and row.question == "Pergunta guardada 1?"

    updated = client.put(
        f"/api/v1/me/reflections/{TODAY}/revelations/1", json={"body": "Outra pausa"}
    )
    assert updated.status_code == 200
    assert updated.json()["body"] == "Outra pausa"
    listed = client.get(f"/api/v1/me/reflections/{TODAY}")
    assert listed.status_code == 200
    assert listed.json()[0]["body"] == "Outra pausa"


def test_revelation_reflection_is_404_without_reading_or_slot(
    client: TestClient, session: Session
) -> None:
    user_id = _register(client)
    _set_now(client, NOW)
    missing = client.put(f"/api/v1/me/reflections/{TODAY}/revelations/0", json={"body": "Nota"})
    assert missing.status_code == 404

    _add_interpretation(session, user_id, TODAY, content=_content(1))
    absent = client.put(f"/api/v1/me/reflections/{TODAY}/revelations/1", json={"body": "Nota"})
    assert absent.status_code == 404


def test_revelation_reflection_and_archive_prefer_current_facts_hash(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = _register(client)
    prompt = _patch_sky(monkeypatch)
    matching_hash = prompt_hash(SYSTEM, prompt)
    matching_content = _content()
    matching_content["theme"] = "Residência A"
    matching_content["revelations"] = [
        {
            "title": "Leitura da residência A",
            "text": "Texto da residência A.",
            "question": "Pergunta da residência A?",
        }
        for _ in range(5)
    ]
    newer_content = _content()
    newer_content["theme"] = "Residência B"
    newer_content["revelations"] = [
        {
            "title": "Leitura da residência B",
            "text": "Texto da residência B.",
            "question": "Pergunta da residência B?",
        }
        for _ in range(5)
    ]
    _add_interpretation(
        session,
        user_id,
        TODAY,
        content=matching_content,
        facts_hash=matching_hash,
        created_at=datetime(2026, 11, 16, 9, tzinfo=UTC),
    )
    _add_interpretation(
        session,
        user_id,
        TODAY,
        content=newer_content,
        facts_hash="a" * 64,
        created_at=datetime(2026, 11, 16, 12, tzinfo=UTC),
    )
    _set_now(client, NOW)

    saved = client.put(
        f"/api/v1/me/reflections/{TODAY}/revelations/0",
        json={"body": "A resposta corresponde à residência A."},
    )
    assert saved.status_code == 200
    assert saved.json()["question"] == "Pergunta da residência A?"

    archive = client.get(f"/api/v1/me/archive/{TODAY}")
    assert archive.status_code == 200
    assert archive.json()["theme"] == "Residência A"
    assert archive.json()["revelations"][0]["reading"]["title"] == "Leitura da residência A"
    assert archive.json()["revelations"][0]["origin"] is not None
    assert archive.json()["reflections"][0]["question"] == "Pergunta da residência A?"


def test_users_cannot_read_or_change_another_users_reflections(
    client: TestClient, session: Session
) -> None:
    user_a = _register(client, "a@example.org")
    _set_now(client, NOW)
    assert (
        client.put(
            f"/api/v1/me/reflections/{TODAY}/note", json={"body": "Privado de A"}
        ).status_code
        == 200
    )

    client.cookies.clear()
    _register(client, "b@example.org")
    _set_now(client, NOW)
    assert client.get(f"/api/v1/me/reflections/{TODAY}").json() == []
    assert (
        client.put(
            f"/api/v1/me/reflections/{TODAY}/note", json={"body": "Privado de B"}
        ).status_code
        == 200
    )
    assert client.delete(f"/api/v1/me/reflections/{TODAY}/note").status_code == 204
    client.cookies.clear()
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "a@example.org", "password": "palavra-passe-longa"},
        ).status_code
        == 200
    )
    reflections = client.get(f"/api/v1/me/reflections/{TODAY}").json()
    assert [reflection["body"] for reflection in reflections] == ["Privado de A"]
    user_a_reflection = session.scalars(
        select(Reflection).where(Reflection.user_id == user_a)
    ).one()
    assert user_a_reflection.body == "Privado de A"


def test_archive_is_descending_paginated_includes_reflection_only_days_and_needs_no_model(
    client: TestClient, session: Session
) -> None:
    user_id = _register(client)
    _set_now(client, datetime(2026, 11, 19, 12, tzinfo=UTC))
    _add_interpretation(
        session,
        user_id,
        date(2026, 11, 16),
        content=_content(2),
        facts_hash="a" * 64,
        created_at=datetime(2026, 11, 16, 10, tzinfo=UTC),
    )
    _add_interpretation(
        session,
        user_id,
        date(2026, 11, 16),
        content=_content(3) | {"theme": "Tema mais recente"},
        facts_hash="b" * 64,
        created_at=datetime(2026, 11, 16, 12, tzinfo=UTC),
    )
    _add_interpretation(session, user_id, date(2026, 11, 14))
    _add_interpretation(session, user_id, date(2026, 11, 20))
    _add_reflection(session, user_id, date(2026, 11, 18), None, "Só uma nota")
    _add_reflection(session, user_id, date(2026, 11, 16), 0, "Uma resposta")
    _add_reflection(session, user_id, date(2026, 11, 16), None, "Nota do mesmo dia")
    _add_reflection(session, user_id, date(2026, 11, 12), None, "Uma nota antiga")
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: None

    first = client.get("/api/v1/me/archive", params={"limit": 3})
    assert first.status_code == 200
    first_json = first.json()
    assert [item["date"] for item in first_json["days"]] == [
        "2026-11-18",
        "2026-11-16",
        "2026-11-14",
    ]
    assert first_json["days"][0]["theme"] is None
    assert first_json["days"][0]["reflection_count"] == 1
    latest = first_json["days"][1]
    assert latest["theme"] == "Tema mais recente"
    assert latest["revelation_count"] == 3
    assert latest["reflection_count"] == 2
    assert latest["has_note"] is True
    assert first_json["next_before"] == "2026-11-14"

    second = client.get(
        "/api/v1/me/archive", params={"before": first_json["next_before"], "limit": 3}
    )
    assert second.status_code == 200
    assert [item["date"] for item in second.json()["days"]] == ["2026-11-12"]
    assert second.json()["next_before"] is None


def test_archive_day_redacts_locked_slots_and_invalidates_origin_after_residence_change(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = _register(client)
    prompt = _patch_sky(monkeypatch)
    _add_interpretation(
        session,
        user_id,
        TODAY,
        facts_hash=prompt_hash(SYSTEM, prompt),
    )
    _set_now(client, NOW)

    response = client.get(f"/api/v1/me/archive/{TODAY}")
    assert response.status_code == 200
    items = response.json()["revelations"]
    assert [item["reading"] is not None for item in items] == [True, True, False, False, False]
    assert [item["origin"] is not None for item in items] == [True, True, False, False, False]
    for index in range(2, 5):
        assert f"Título reservado {index}" not in response.text
        assert f"Texto reservado {index}" not in response.text
        assert f"Pergunta guardada {index}" not in response.text

    assert (
        client.put(
            "/api/v1/me/residence",
            json={"place_name": "Tóquio", "zone": "Asia/Tokyo"},
        ).status_code
        == 200
    )
    changed = client.get(f"/api/v1/me/archive/{TODAY}")
    assert changed.status_code == 200
    assert all(item["reading"] is not None for item in changed.json()["revelations"])
    assert all(item["origin"] is None for item in changed.json()["revelations"])


def test_archive_day_returns_reflections_without_a_reading(client: TestClient) -> None:
    _register(client)
    _set_now(client, NOW)
    saved = client.put(f"/api/v1/me/reflections/{TODAY}/note", json={"body": "Só uma nota"})
    assert saved.status_code == 200
    cast(FastAPI, client.app).dependency_overrides[get_text_model] = lambda: None

    response = client.get(f"/api/v1/me/archive/{TODAY}")
    assert response.status_code == 200
    assert response.json()["theme"] is None
    assert response.json()["revelations"] == []
    assert response.json()["reflections"][0]["body"] == "Só uma nota"
    assert response.json()["model"] is None
    assert response.json()["note"] is None


def test_archive_day_preserves_saved_content_when_sky_calculation_fails(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = _register(client)
    _add_interpretation(session, user_id, TODAY)
    _add_reflection(session, user_id, TODAY, None, "Nota preservada")
    _set_now(client, NOW)

    def fail_daily_sky(
        _user: User,
        _profile: BirthProfile,
        _day: date | None = None,
        *,
        now: datetime | None = None,
    ) -> tuple[NatalChart, DailySky]:
        del now
        raise HTTPException(422, "não foi possível calcular o céu")

    monkeypatch.setattr("arquivo.api.journal._daily_sky", fail_daily_sky)

    response = client.get(f"/api/v1/me/archive/{TODAY}")

    assert response.status_code == 200
    items = response.json()["revelations"]
    assert items[0]["reading"]["title"] == "Título reservado 0"
    assert items[0]["reading"]["text"] == "Texto reservado 0."
    assert all(item["origin"] is None for item in items)
    assert response.json()["reflections"][0]["body"] == "Nota preservada"


def test_deleting_account_cascades_reflections(client: TestClient, session: Session) -> None:
    user_id = _register(client)
    _set_now(client, NOW)
    saved = client.put(f"/api/v1/me/reflections/{TODAY}/note", json={"body": "Privado"})
    assert saved.status_code == 200
    assert session.scalars(select(Reflection).where(Reflection.user_id == user_id)).all()

    assert client.delete("/api/v1/me").status_code == 204
    assert session.scalars(select(Reflection)).all() == []
