import hashlib
import re
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, cast

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from arquivo import main
from arquivo.api import auth
from arquivo.api.deps import SESSION_COOKIE, get_db, get_now
from arquivo.config import Settings, get_settings
from arquivo.persistence import accounts, throttle
from arquivo.persistence.models import AuditEvent, AuthSession, AuthThrottle, User

pytestmark = pytest.mark.db

NOW = datetime(2026, 11, 18, 12, tzinfo=UTC)
PASSWORD = "palavra-passe-longa"


class ClientResponse(Protocol):
    status_code: int

    @property
    def headers(self) -> Any: ...

    @property
    def text(self) -> str: ...

    def json(self) -> Any: ...


def _app_with_session(session: Session) -> FastAPI:
    app = main.create_app()

    def override_db() -> Iterator[Session]:
        yield session
        session.flush()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_now] = lambda: NOW
    return app


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    with TestClient(_app_with_session(session)) as test_client:
        yield test_client


def _register(client: TestClient, email: str = "ana@example.org") -> ClientResponse:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Ana"},
    )
    assert response.status_code == 201, response.text
    return response


def _login(client: TestClient, email: str, password: str = PASSWORD) -> ClientResponse:
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _create_user(session: Session, email: str) -> User:
    return accounts.register(session, email, PASSWORD, "Ana")


def _session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def _database_dependency(
    factory: sessionmaker[Session],
) -> Callable[[], Iterator[Session]]:
    def dependency() -> Iterator[Session]:
        with factory() as session, session.begin():
            yield session

    return dependency


def _create_committed_user(factory: sessionmaker[Session], email: str) -> None:
    with factory() as session, session.begin():
        accounts.register(session, email, PASSWORD, "Ana")


def _cleanup_committed_user(factory: sessionmaker[Session], email: str, ips: list[str]) -> None:
    with factory() as session, session.begin():
        for ip in ips:
            for limit, hashed_key in throttle.login_keys(email, ip):
                session.execute(
                    delete(AuthThrottle).where(
                        AuthThrottle.scope == limit.scope,
                        AuthThrottle.key_hash == hashed_key,
                    )
                )
        user = session.scalar(select(User).where(User.email == email))
        if user is not None:
            session.execute(delete(AuditEvent).where(AuditEvent.owner_id == user.id))
            session.delete(user)


def test_login_cookie_attributes_and_no_store(client: TestClient) -> None:
    registered = _register(client)
    response = _login(client, "ana@example.org")

    assert registered.headers["cache-control"] == "no-store"
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert "max-age=2592000" in cookie
    assert "secure" not in cookie
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/me").headers["cache-control"] == "no-store"


def test_production_cookie_is_secure(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _register(client)
    production = Settings(
        environment="production",
        cors_origins=["https://arquivo.example"],
        auth_rate_limit_key=SecretStr("x" * 32),
    )
    monkeypatch.setattr(auth, "get_settings", lambda: production)

    response = _login(client, "ana@example.org")

    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_failed_login_messages_do_not_enumerate_accounts(client: TestClient) -> None:
    _register(client)

    wrong_password = _login(client, "ana@example.org", "palavra-incorreta")
    missing_account = _login(client, "inexistente@example.org", "palavra-incorreta")

    assert wrong_password.status_code == missing_account.status_code == 401
    assert wrong_password.headers["cache-control"] == "no-store"
    assert (
        wrong_password.json()
        == missing_account.json()
        == {"detail": "email ou palavra-passe incorretos"}
    )


def test_account_ip_limit_blocks_correct_password_but_another_ip_can_login(
    client: TestClient, session: Session
) -> None:
    email = "limite-ip@example.org"
    _create_user(session, email)
    clock = [NOW]
    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_now] = lambda: clock[0]

    for _ in range(5):
        assert _login(client, email, "palavra-incorreta").status_code == 401
    blocked = _login(client, email)
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "demasiadas tentativas; tenta novamente mais tarde"}
    assert int(blocked.headers["retry-after"]) >= 1

    clock[0] = NOW + timedelta(minutes=16)
    assert _login(client, email).status_code == 200

    with TestClient(app, client=("198.51.100.22", 50001)) as other_ip:
        assert _login(other_ip, email).status_code == 200


def test_login_ip_limit_applies_across_different_emails(client: TestClient) -> None:
    for index in range(20):
        response = _login(client, f"pessoa-{index}@example.org", "palavra-incorreta")
        assert response.status_code == 401

    blocked = _login(client, "pessoa-20@example.org", "palavra-incorreta")
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) >= 1


def test_account_limit_recovers_after_61_minutes(client: TestClient, session: Session) -> None:
    email = "limite-global@example.org"
    _create_user(session, email)
    clock = [NOW]
    cast(FastAPI, client.app).dependency_overrides[get_now] = lambda: clock[0]

    for index in range(50):
        with TestClient(client.app, client=(f"198.51.100.{index + 1}", 50000)) as from_ip:
            assert _login(from_ip, email, "palavra-incorreta").status_code == 401

    with TestClient(client.app, client=("198.51.100.51", 50000)) as new_ip:
        assert _login(new_ip, email).status_code == 429
        clock[0] = NOW + timedelta(minutes=61)
        assert _login(new_ip, email).status_code == 200


def test_success_clears_account_ip_failures(client: TestClient, session: Session) -> None:
    email = "limpar-limite@example.org"
    _create_user(session, email)

    for _ in range(4):
        assert _login(client, email, "palavra-incorreta").status_code == 401
    assert _login(client, email).status_code == 200

    hashed_key = next(
        key
        for limit, key in throttle.login_keys(email, "testclient")
        if limit == throttle.LOGIN_ACCOUNT_IP
    )
    count = session.scalar(
        select(func.count())
        .select_from(AuthThrottle)
        .where(
            AuthThrottle.scope == throttle.LOGIN_ACCOUNT_IP.scope,
            AuthThrottle.key_hash == hashed_key,
        )
    )
    assert count == 0


def test_register_ip_limit_counts_success_and_duplicate_attempts(client: TestClient) -> None:
    registered = _register(client, "registo@example.org")
    assert registered.headers["cache-control"] == "no-store"
    for _ in range(9):
        duplicate = client.post(
            "/api/v1/auth/register",
            json={
                "email": "registo@example.org",
                "password": PASSWORD,
                "display_name": "Ana",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json() == {"detail": "já existe uma conta com este email"}
        assert duplicate.headers["cache-control"] == "no-store"

    blocked = client.post(
        "/api/v1/auth/register",
        json={
            "email": "registo-11@example.org",
            "password": PASSWORD,
            "display_name": "Ana",
        },
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) >= 1


def test_throttles_are_shared_between_app_instances(
    engine: Engine,
) -> None:
    email = "partilhado@example.org"
    ip = "198.51.100.90"
    factory = _session_factory(engine)
    _create_committed_user(factory, email)
    first = main.create_app()
    second = main.create_app()
    for app in (first, second):
        app.dependency_overrides[get_db] = _database_dependency(factory)
        app.dependency_overrides[get_now] = lambda: NOW

    try:
        with (
            TestClient(first, client=(ip, 50000)) as app_a,
            TestClient(second, client=(ip, 50001)) as app_b,
        ):
            for _ in range(5):
                assert _login(app_a, email, "palavra-incorreta").status_code == 401
            assert _login(app_b, email).status_code == 429
    finally:
        _cleanup_committed_user(factory, email, [ip])


def test_no_trusted_proxy_ignores_spoofed_forwarded_for(client: TestClient) -> None:
    for index in range(20):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": f"spoof-{index}@example.org", "password": "incorreta"},
            headers={"X-Forwarded-For": f"198.51.100.{index + 1}"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "spoof-20@example.org", "password": "incorreta"},
        headers={"X-Forwarded-For": "203.0.113.99"},
    )
    assert blocked.status_code == 429


def test_trusted_proxy_uses_forwarded_client_ip(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(trusted_proxies=["127.0.0.1"])
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    email = "proxy-fiavel@example.org"
    _create_user(session, email)
    app = _app_with_session(session)

    with TestClient(app, client=("127.0.0.1", 50000)) as proxy:
        for _ in range(5):
            response = proxy.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "incorreta"},
                headers={"X-Forwarded-For": "198.51.100.70"},
            )
            assert response.status_code == 401
        blocked = proxy.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PASSWORD},
            headers={"X-Forwarded-For": "198.51.100.70"},
        )
        allowed = proxy.post(
            "/api/v1/auth/login",
            json={"email": email, "password": PASSWORD},
            headers={"X-Forwarded-For": "198.51.100.71"},
        )

    assert blocked.status_code == 429
    assert allowed.status_code == 200


def test_throttle_rows_store_only_pseudonymous_keys(client: TestClient, session: Session) -> None:
    email = "privado@example.org"
    ip = "testclient"

    assert _login(client, email, "incorreta").status_code == 401

    rows = session.scalars(select(AuthThrottle)).all()
    assert len(rows) == 3
    assert all(email not in str(row.__dict__) and ip not in str(row.__dict__) for row in rows)
    assert all(len(row.key_hash) == 64 for row in rows)


def test_parallel_failures_respect_account_ip_limit(engine: Engine) -> None:
    email = "concorrencia@example.org"
    ip = "198.51.100.88"
    factory = _session_factory(engine)
    _create_committed_user(factory, email)
    app = main.create_app()
    app.dependency_overrides[get_db] = _database_dependency(factory)
    app.dependency_overrides[get_now] = lambda: NOW

    def attempt(_: int) -> int:
        with TestClient(app, client=(ip, 50000)) as test_client:
            return _login(test_client, email, "incorreta").status_code

    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            statuses = list(executor.map(attempt, range(10)))
        assert statuses.count(401) == 5
        assert statuses.count(429) == 5
    finally:
        _cleanup_committed_user(factory, email, [ip])


def test_invalid_origins_are_rejected_on_every_unsafe_route(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    templates = [
        (route.path, route.methods.intersection({"POST", "PUT", "DELETE", "PATCH"}))
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.methods
        and route.methods.intersection({"POST", "PUT", "DELETE", "PATCH"})
    ]
    invalid_headers = [
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
        {"Referer": "https://evil.example/x"},
    ]

    for route_path, methods in templates:
        path = re.sub(r"\{[^{}]+\}", "valor", route_path)
        for method in methods:
            for headers in invalid_headers:
                response = client.request(method, path, headers=headers)
                assert response.status_code == 403, f"{method} {path} {headers}"


def test_allowed_origin_and_form_post_behavior(client: TestClient) -> None:
    _register(client)
    allowed = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.org", "password": PASSWORD},
        headers={"Origin": "http://localhost:5173"},
    )
    form = client.post(
        "/api/v1/auth/login",
        content="email=ana%40example.org&password=palavra-passe-longa",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert allowed.status_code == 200
    assert form.status_code == 422


def test_cors_preflight_is_restricted_to_configured_origins(client: TestClient) -> None:
    allowed = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    denied = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-origin" not in denied.headers


def test_settings_reject_unsafe_origins_and_proxies() -> None:
    assert Settings().cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    with pytest.raises(ValidationError):
        Settings(cors_origins=["*"])
    with pytest.raises(ValidationError):
        Settings(cors_origins=["https://arquivo.example/app"])
    with pytest.raises(ValidationError):
        Settings(cors_origins=["https://arquivo.example:"])
    with pytest.raises(ValidationError):
        Settings(trusted_proxies=["*"])
    with pytest.raises(ValidationError):
        Settings(trusted_proxies=["proxy.local"])


def test_production_settings_fail_closed_and_accept_valid_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            cors_origins=["https://arquivo.example"],
            auth_rate_limit_key=None,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            cors_origins=["https://arquivo.example"],
            auth_rate_limit_key="x" * 31,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            cors_origins=["http://arquivo.example"],
            auth_rate_limit_key="x" * 32,
        )
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            cors_origins=[],
            auth_rate_limit_key="x" * 32,
        )
    with pytest.raises(ValidationError):
        Settings.model_validate({"environment": "prodution"})

    accepted = Settings(
        environment="production",
        cors_origins=["https://arquivo.example"],
        auth_rate_limit_key="x" * 32,
        trusted_proxies=["192.0.2.0/24"],
    )
    assert accepted.environment == "production"


def test_invalid_production_environment_fails_during_app_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ARQUIVO_ENVIRONMENT", "production")
    monkeypatch.setenv("ARQUIVO_CORS_ORIGINS", '["https://arquivo.example"]')
    monkeypatch.delenv("ARQUIVO_AUTH_RATE_LIMIT_KEY", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError):
            main.create_app()
    finally:
        get_settings.cache_clear()


def test_registration_rotates_an_existing_session(client: TestClient, session: Session) -> None:
    _register(client, "primeira@example.org")
    old_token = client.cookies.get(SESSION_COOKIE)
    assert old_token is not None

    registered = _register(client, "segunda@example.org")

    assert registered.status_code == 201
    old_hash = hashlib.sha256(old_token.encode()).hexdigest()
    assert session.scalar(select(AuthSession).where(AuthSession.token_hash == old_hash)) is None


def test_logout_deletion_and_login_rotate_sessions(client: TestClient, session: Session) -> None:
    _register(client)
    old_token = client.cookies.get(SESSION_COOKIE)
    assert old_token is not None
    rotated = _login(client, "ana@example.org")
    assert rotated.status_code == 200
    old_hash = hashlib.sha256(old_token.encode()).hexdigest()
    assert session.scalar(select(AuthSession).where(AuthSession.token_hash == old_hash)) is None

    current_token = client.cookies.get(SESSION_COOKIE)
    assert current_token is not None
    logged_out = client.post("/api/v1/auth/logout")
    logout_cookie = logged_out.headers["set-cookie"].lower()
    assert "httponly" in logout_cookie
    assert "samesite=lax" in logout_cookie
    assert "path=/" in logout_cookie
    assert "secure" not in logout_cookie
    assert logged_out.headers["cache-control"] == "no-store"
    reused = client.get(
        "/api/v1/me",
        headers={"Cookie": f"{SESSION_COOKIE}={current_token}"},
    )
    assert reused.status_code == 401
    assert reused.headers["cache-control"] == "no-store"


def test_expired_session_is_rejected_and_purged_on_login(
    client: TestClient, session: Session
) -> None:
    _register(client)
    user = session.scalar(select(User).where(User.email == "ana@example.org"))
    assert user is not None
    expired_token = "token-expirado"
    expired_hash = hashlib.sha256(expired_token.encode()).hexdigest()
    purge_now = datetime.now(UTC)
    cast(FastAPI, client.app).dependency_overrides[get_now] = lambda: purge_now
    expired = AuthSession(
        user_id=user.id,
        token_hash=expired_hash,
        expires_at=purge_now - timedelta(minutes=1),
    )
    session.add(expired)
    session.flush()
    client.cookies.clear()

    assert (
        client.get(
            "/api/v1/me",
            headers={"Cookie": f"{SESSION_COOKIE}={expired_token}"},
        ).status_code
        == 401
    )
    assert _login(client, "ana@example.org").status_code == 200
    assert session.scalar(select(AuthSession).where(AuthSession.token_hash == expired_hash)) is None


def test_account_deletion_revokes_all_sessions(client: TestClient, session: Session) -> None:
    _register(client)
    user = session.scalar(select(User).where(User.email == "ana@example.org"))
    assert user is not None
    with TestClient(client.app) as second_client:
        assert _login(second_client, "ana@example.org").status_code == 200
    assert (
        session.scalar(
            select(func.count()).select_from(AuthSession).where(AuthSession.user_id == user.id)
        )
        == 2
    )

    deleted = client.delete("/api/v1/me")
    assert deleted.status_code == 204
    deleted_cookie = deleted.headers["set-cookie"].lower()
    assert "httponly" in deleted_cookie
    assert "samesite=lax" in deleted_cookie
    assert "path=/" in deleted_cookie
    assert "secure" not in deleted_cookie
    assert (
        session.scalar(
            select(func.count()).select_from(AuthSession).where(AuthSession.user_id == user.id)
        )
        == 0
    )


def test_long_password_is_not_echoed_in_validation_errors(client: TestClient) -> None:
    password = "segredo-" * 25 + "x"
    assert len(password) == 201
    response = _login(client, "ana@example.org", password)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert password not in response.text
    errors = response.json()["detail"]
    assert all(set(error) == {"type", "loc", "msg"} for error in errors)
