import json
from collections.abc import Iterator
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from arquivo.api.deps import get_db, get_text_model
from arquivo.api.reading import _store
from arquivo.interpretation.prompts import NATAL_SECTIONS
from arquivo.main import create_app
from arquivo.persistence.models import Interpretation, User

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
