"""Limites deslizantes de tentativas de autenticação, partilhados pela base de dados."""

import hashlib
import hmac
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from arquivo.config import DEVELOPMENT_AUTH_RATE_LIMIT_KEY, get_settings
from arquivo.persistence.accounts import normalize_email
from arquivo.persistence.models import AuthThrottle


@dataclass(frozen=True)
class Limit:
    scope: str
    max_events: int
    window: timedelta


type RateLimitKey = tuple[Limit, str]

LOGIN_IP = Limit("login_ip", 20, timedelta(minutes=15))
LOGIN_ACCOUNT_IP = Limit("login_account_ip", 5, timedelta(minutes=15))
LOGIN_ACCOUNT = Limit("login_account", 50, timedelta(minutes=60))
REGISTER_IP = Limit("register_ip", 10, timedelta(minutes=60))
RECOVERY_IP = Limit("recovery_ip", 20, timedelta(minutes=15))
RECOVERY_ACCOUNT = Limit("recovery_account", 3, timedelta(minutes=15))
RESET_IP = Limit("reset_ip", 20, timedelta(minutes=15))


def key_hash(scope: str, value: str) -> str:
    configured_key = get_settings().auth_rate_limit_key
    secret = (
        configured_key.get_secret_value()
        if configured_key is not None
        else DEVELOPMENT_AUTH_RATE_LIMIT_KEY
    )
    message = f"{scope}:{value}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def login_keys(email: str, ip: str) -> list[RateLimitKey]:
    normalized_email = normalize_email(email)
    return [
        (LOGIN_IP, key_hash(LOGIN_IP.scope, ip)),
        (LOGIN_ACCOUNT_IP, key_hash(LOGIN_ACCOUNT_IP.scope, f"{normalized_email}|{ip}")),
        (LOGIN_ACCOUNT, key_hash(LOGIN_ACCOUNT.scope, normalized_email)),
    ]


def register_key(ip: str) -> RateLimitKey:
    return REGISTER_IP, key_hash(REGISTER_IP.scope, ip)


def lock(session: Session, limits_and_keys: list[RateLimitKey]) -> None:
    key_hashes = sorted({key for _, key in limits_and_keys})
    for key in key_hashes:
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"),
            {"k": key},
        )


def retry_after(
    session: Session,
    limits_and_keys: list[RateLimitKey],
    now: datetime,
) -> int | None:
    retry_seconds: list[int] = []
    for limit, hashed_key in limits_and_keys:
        timestamps = session.scalars(
            select(AuthThrottle.created_at)
            .where(
                AuthThrottle.scope == limit.scope,
                AuthThrottle.key_hash == hashed_key,
                AuthThrottle.created_at > now - limit.window,
            )
            .order_by(AuthThrottle.created_at.desc())
            .limit(limit.max_events)
        ).all()
        if len(timestamps) == limit.max_events:
            expires_at = timestamps[-1] + limit.window
            retry_seconds.append(max(1, math.ceil((expires_at - now).total_seconds())))
    return max(retry_seconds) if retry_seconds else None


def record(
    session: Session,
    limits_and_keys: list[RateLimitKey],
    now: datetime,
) -> None:
    session.add_all(
        [
            AuthThrottle(scope=limit.scope, key_hash=hashed_key, created_at=now)
            for limit, hashed_key in limits_and_keys
        ]
    )
    session.execute(delete(AuthThrottle).where(AuthThrottle.created_at < now - timedelta(hours=2)))


def clear(session: Session, limit: Limit, hashed_key: str, now: datetime) -> None:
    del now
    session.execute(
        delete(AuthThrottle).where(
            AuthThrottle.scope == limit.scope,
            AuthThrottle.key_hash == hashed_key,
        )
    )
