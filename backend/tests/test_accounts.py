from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from arquivo.api.deps import get_db
from arquivo.main import create_app
from arquivo.persistence import accounts
from arquivo.persistence.models import AuditEvent, AuthSession, BirthProfile, User

BIRTH = {
    "birth_date": "1993-05-20",
    "birth_time": "14:35",
    "place_name": "Lisboa",
    "latitude": 38.7223,
    "longitude": -9.1393,
}


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app = create_app()

    def _db() -> Iterator[Session]:
        yield session
        session.flush()

    app.dependency_overrides[get_db] = _db
    yield TestClient(app)


def _register(client: TestClient, email: str = "ana@example.org") -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "palavra-passe-longa", "display_name": "Ana"},
    )
    assert response.status_code == 201, response.text


def test_register_login_logout(client: TestClient, session: Session) -> None:
    _register(client, "Ana@Example.org")
    assert client.get("/api/v1/me").json()["email"] == "ana@example.org"
    stored = session.scalars(select(AuthSession.token_hash)).all()
    assert client.cookies["arquivo_sessao"] not in stored

    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/v1/me").status_code == 401

    wrong = {"email": "ana@example.org", "password": "errada-errada"}
    assert client.post("/api/v1/auth/login", json=wrong).status_code == 401
    ok = {"email": "ana@example.org", "password": "palavra-passe-longa"}
    assert client.post("/api/v1/auth/login", json=ok).status_code == 200
    assert client.get("/api/v1/me").status_code == 200


def test_duplicate_email_and_short_password(client: TestClient) -> None:
    _register(client)
    again = {"email": "ana@example.org", "password": "palavra-passe-longa", "display_name": "A"}
    assert client.post("/api/v1/auth/register", json=again).status_code == 409
    blank = {"email": "c@example.org", "password": "palavra-passe-longa", "display_name": "  "}
    assert client.post("/api/v1/auth/register", json=blank).status_code == 422
    short = {"email": "b@example.org", "password": "curta", "display_name": "B"}
    assert client.post("/api/v1/auth/register", json=short).status_code == 422


def test_concurrent_registration_maps_unique_violation(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    accounts.register(session, "ana@example.org", "palavra-passe-longa", "Ana")
    monkeypatch.setattr(Session, "scalar", lambda *args, **kwargs: None)
    with pytest.raises(accounts.EmailInUseError):
        accounts.register(session, "ana@example.org", "palavra-passe-longa", "Ana")


def test_birth_profile_and_chart(client: TestClient) -> None:
    assert client.get("/api/v1/me/birth").status_code == 401
    _register(client)
    assert client.get("/api/v1/me/chart").status_code == 404
    saved = client.put("/api/v1/me/birth", json=BIRTH)
    assert saved.status_code == 200, saved.text
    assert saved.json()["zone"] == "Europe/Lisbon"
    assert saved.json()["birth_utc"] == "1993-05-20T12:35:00Z"
    chart = client.get("/api/v1/me/chart").json()
    assert chart["bodies"][0]["sign"] == "taurus"
    assert len(chart["houses"]) == 12


def test_birth_profile_requires_exact_time(client: TestClient) -> None:
    _register(client)
    assert client.put("/api/v1/me/birth", json=BIRTH | {"place_name": "   "}).status_code == 422
    ambiguous = BIRTH | {"birth_date": "2024-10-27", "birth_time": "01:30"}
    response = client.put("/api/v1/me/birth", json=ambiguous)
    assert response.status_code == 422
    assert "duas vezes" in response.json()["detail"]
    chosen = client.put("/api/v1/me/birth", json=ambiguous | {"occurrence": 1})
    assert chosen.json()["birth_utc"] == "2024-10-27T01:30:00Z"


def test_profiles_are_isolated_and_account_deletion(client: TestClient, session: Session) -> None:
    _register(client)
    client.put("/api/v1/me/birth", json=BIRTH)
    client.cookies.clear()
    _register(client, "rui@example.org")
    assert client.get("/api/v1/me/birth").status_code == 404

    client.cookies.clear()
    ok = {"email": "ana@example.org", "password": "palavra-passe-longa"}
    client.post("/api/v1/auth/login", json=ok)
    assert client.delete("/api/v1/me").status_code == 204
    assert session.scalar(select(User).where(User.email == "ana@example.org")) is None
    assert session.scalars(select(BirthProfile)).all() == []
    events = session.scalars(select(AuditEvent).where(AuditEvent.entity_type == "user")).all()
    assert any(event.action == "account.deleted" for event in events)
    ana = "ana@example.org"
    for event in events:
        assert ana not in str(event.details)
        if event.owner_id is None:
            assert event.actor in ("titular", "anónimo")
            assert event.entity_id == "-"


def test_today_uses_residence_zone(client: TestClient) -> None:
    _register(client)
    assert client.put("/api/v1/me/birth", json=BIRTH).status_code == 200
    sky = client.get("/api/v1/me/today", params={"date": "2026-11-12"}).json()
    assert sky["zone"] == "Europe/Lisbon"
    assert len(sky["revelations"]) <= 5
    bad = {"place_name": "Lugar", "zone": "Marte/Olympus"}
    assert client.put("/api/v1/me/residence", json=bad).status_code == 422
    home = {"place_name": "Tokyo, Japão", "zone": "Asia/Tokyo"}
    assert client.put("/api/v1/me/residence", json=home).json()["residence_zone"] == "Asia/Tokyo"
    sky = client.get("/api/v1/me/today", params={"date": "2026-11-12"}).json()
    assert sky["zone"] == "Asia/Tokyo"
    assert sky["day_starts"].startswith("2026-11-12T00:00:00+09:00")
    assert client.get("/api/v1/me/today", params={"date": "1700-01-01"}).status_code == 422
