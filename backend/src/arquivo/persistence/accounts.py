"""Contas, autenticação por palavra-passe e sessões."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from arquivo.persistence.models import AuditEvent, AuthSession, User

SESSION_TTL = timedelta(days=30)
_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash("palavra-passe-inexistente")


class EmailInUseError(ValueError):
    """Já existe uma conta com este email."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def audit(session: Session, user_id: uuid.UUID | None, action: str, **details: Any) -> None:
    session.add(
        AuditEvent(
            owner_id=user_id,
            actor="titular" if user_id else "anónimo",
            action=action,
            entity_type="user",
            entity_id="-",
            correlation_id=uuid.uuid4(),
            details=details,
        )
    )


def register(session: Session, email: str, password: str, display_name: str) -> User:
    email = normalize_email(email)
    if session.scalar(select(User.id).where(User.email == email)) is not None:
        raise EmailInUseError("já existe uma conta com este email")
    user = User(
        email=email, display_name=display_name.strip(), password_hash=_hasher.hash(password)
    )
    session.add(user)
    session.flush()
    audit(session, user.id, "account.registered")
    return user


def authenticate(session: Session, email: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.email == normalize_email(email)))
    stored = user.password_hash if user and user.password_hash else _DUMMY_HASH
    try:
        _hasher.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return None
    if user is None or user.password_hash is None:
        return None
    if _hasher.check_needs_rehash(user.password_hash):
        user.password_hash = _hasher.hash(password)
    audit(session, user.id, "account.login")
    return user


def open_session(session: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    session.add(
        AuthSession(user_id=user.id, token_hash=_token_hash(token), expires_at=_now() + SESSION_TTL)
    )
    session.flush()
    return token


def user_for_token(session: Session, token: str) -> User | None:
    found = session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _token_hash(token), AuthSession.expires_at > _now()
        )
    )
    return session.get(User, found.user_id) if found else None


def close_session(session: Session, token: str) -> None:
    session.execute(delete(AuthSession).where(AuthSession.token_hash == _token_hash(token)))


def delete_account(session: Session, user: User) -> None:
    """Apaga a conta e todos os dados (RGPD). A auditoria fica anonimizada (owner_id = NULL)."""
    audit(session, user.id, "account.deleted")
    session.flush()
    session.delete(user)
    session.flush()
