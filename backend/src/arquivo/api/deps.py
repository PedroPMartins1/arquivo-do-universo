from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from arquivo.config import get_settings
from arquivo.interpretation.model import AnthropicModel, TextModel
from arquivo.persistence.accounts import user_for_token
from arquivo.persistence.models import User
from arquivo.persistence.session import get_sessionmaker

SESSION_COOKIE = "arquivo_sessao"


def get_db() -> Iterator[Session]:
    with get_sessionmaker()() as session, session.begin():
        yield session


Db = Annotated[Session, Depends(get_db)]


def current_user(db: Db, token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None) -> User:
    user = user_for_token(db, token) if token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sessão inválida ou expirada")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def get_text_model() -> TextModel | None:
    settings = get_settings()
    if settings.anthropic_api_key is None:
        return None
    return AnthropicModel(
        settings.anthropic_api_key.get_secret_value(),
        settings.anthropic_model,
    )


def get_now() -> datetime:
    return datetime.now(UTC)


Now = Annotated[datetime, Depends(get_now)]


def has_immediate_access(user: User) -> bool:
    return False
