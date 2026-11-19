"""Contas, autenticação por palavra-passe e sessões."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from arquivo.persistence.models import AuditEvent, AuthSession, PasswordResetToken, User

SESSION_TTL = timedelta(days=30)
PASSWORD_RESET_TTL = timedelta(minutes=30)
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
    try:
        with session.begin_nested():
            session.add(user)
    except IntegrityError as error:
        raise EmailInUseError("já existe uma conta com este email") from error
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


def issue_password_reset(session: Session, email: str, now: datetime) -> str | None:
    user = session.scalar(
        select(User).where(User.email == normalize_email(email)).with_for_update()
    )
    session.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at <= now))
    if user is None:
        return None
    token = secrets.token_urlsafe(32)
    session.add(
        PasswordResetToken(
            user_id=user.id, token_hash=_token_hash(token), expires_at=now + PASSWORD_RESET_TTL
        )
    )
    audit(session, user.id, "account.password_reset_requested")
    session.flush()
    return token


def reset_password(session: Session, token: str, password: str, now: datetime) -> bool:
    user_id = session.scalar(
        select(PasswordResetToken.user_id).where(
            PasswordResetToken.token_hash == _token_hash(token), PasswordResetToken.expires_at > now
        )
    )
    if user_id is None:
        return False
    user = session.scalar(select(User).where(User.id == user_id).with_for_update())
    found = session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == _token_hash(token), PasswordResetToken.expires_at > now
        )
    )
    if user is None or found is None:
        return False
    user.password_hash = _hasher.hash(password)
    session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    session.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    audit(session, user.id, "account.password_reset_completed")
    session.flush()
    return True


def purge_expired_sessions(session: Session, user: User, now: datetime) -> None:
    session.execute(
        delete(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.expires_at <= now,
        )
    )


def delete_account(session: Session, user: User) -> None:
    """Apaga a conta e todos os dados (RGPD). A auditoria fica anonimizada (owner_id = NULL)."""
    audit(session, user.id, "account.deleted")
    session.flush()
    session.delete(user)
    session.flush()
