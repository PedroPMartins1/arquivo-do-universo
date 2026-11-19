from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from arquivo.api import auth
from arquivo.api.deps import get_db
from arquivo.config import get_settings
from arquivo.main import create_app
from arquivo.persistence import accounts
from arquivo.persistence.models import PasswordResetToken


@pytest.fixture
def recovery_client(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, list[tuple[str, str]]]]:
    monkeypatch.setenv("ARQUIVO_RESEND_API_KEY", "chave-ficticia")
    monkeypatch.setenv("ARQUIVO_PUBLIC_URL", "https://teste.example.org")
    get_settings.cache_clear()
    deliveries: list[tuple[str, str]] = []
    monkeypatch.setattr(
        auth, "send_recovery_email", lambda email, token: deliveries.append((email, token))
    )
    app = create_app()

    def db() -> Iterator[Session]:
        yield session
        session.flush()

    app.dependency_overrides[get_db] = db
    with TestClient(app) as client:
        yield client, deliveries
    get_settings.cache_clear()


def test_recovery_preserves_account_and_revokes_sessions(
    recovery_client: tuple[TestClient, list[tuple[str, str]]], session: Session
) -> None:
    client, deliveries = recovery_client
    user = accounts.register(session, "ana@example.org", "password-anterior", "Ana")
    old_session = accounts.open_session(session, user)
    client.cookies.set("arquivo_sessao", old_session)
    known = client.post("/api/v1/auth/forgot-password", json={"email": "ANA@example.org"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "outra@example.org"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(deliveries) == 1
    email, token = deliveries[0]
    assert email == "ana@example.org"
    assert token not in session.scalars(select(PasswordResetToken.token_hash)).all()
    extra = accounts.issue_password_reset(session, email, datetime.now(UTC))
    reset = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "password": "nova-password-segura"}
    )
    assert reset.status_code == 204
    assert reset.headers["cache-control"] == "no-store"
    assert accounts.user_for_token(session, old_session) is None
    assert not accounts.reset_password(session, token, "outra-password", datetime.now(UTC))
    assert extra and not accounts.reset_password(
        session, extra, "outra-password", datetime.now(UTC)
    )
    assert accounts.authenticate(session, email, "password-anterior") is None
    authenticated = accounts.authenticate(session, email, "nova-password-segura")
    assert authenticated is not None
    assert authenticated.id == user.id
    assert client.get("/api/v1/me").status_code == 401


def test_expired_link_and_request_limits(
    recovery_client: tuple[TestClient, list[tuple[str, str]]], session: Session
) -> None:
    client, deliveries = recovery_client
    accounts.register(session, "ana@example.org", "password-anterior", "Ana")
    expired = accounts.issue_password_reset(
        session, "ana@example.org", datetime.now(UTC) - timedelta(hours=1)
    )
    assert expired and not accounts.reset_password(
        session, expired, "nova-password", datetime.now(UTC)
    )
    for _ in range(5):
        assert (
            client.post(
                "/api/v1/auth/forgot-password", json={"email": "ana@example.org"}
            ).status_code
            == 202
        )
    assert len(deliveries) == 3
    invalid = client.post(
        "/api/v1/auth/reset-password", json={"token": "x" * 43, "password": "nova-password"}
    )
    assert invalid.status_code == 400
    assert accounts.authenticate(session, "ana@example.org", "password-anterior") is not None


def test_only_one_concurrent_reset_succeeds(engine: Engine) -> None:
    now = datetime.now(UTC)
    with Session(engine) as session, session.begin():
        user = accounts.register(
            session, "concorrencia-recovery@example.org", "password-anterior", "Teste"
        )
        user_id = user.id
        token = accounts.issue_password_reset(session, user.email, now)
    assert token is not None

    def reset(_: int) -> bool:
        with Session(engine) as session, session.begin():
            return accounts.reset_password(session, token, "nova-password-segura", now)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(reset, [0, 1])) == [False, True]
    finally:
        with Session(engine) as session, session.begin():
            from arquivo.persistence.models import User

            stored_user = session.get(User, user_id)
            assert stored_user is not None
            accounts.delete_account(session, stored_user)
