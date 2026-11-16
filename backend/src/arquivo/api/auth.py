from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response, status
from pydantic import BaseModel, EmailStr, Field, StringConstraints
from starlette.responses import JSONResponse

from arquivo.api.deps import SESSION_COOKIE, CurrentUser, Db, Now
from arquivo.config import get_settings
from arquivo.persistence import accounts, throttle
from arquivo.persistence.models import User

router = APIRouter(tags=["Contas"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=200)
    display_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=200)


class Me(BaseModel):
    id: str
    email: str
    display_name: str
    residence_name: str | None = None
    residence_zone: str | None = None

    @classmethod
    def of(cls, user: User) -> "Me":
        return cls(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            residence_name=user.residence_name,
            residence_zone=user.residence_zone,
        )


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(accounts.SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=get_settings().environment == "production",
        path="/",
    )


def _delete_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=get_settings().environment == "production",
        httponly=True,
        samesite="lax",
    )


def _failure_response(
    status_code: int, detail: str, retry_after: int | None = None
) -> JSONResponse:
    headers = {"Cache-Control": "no-store"}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse(status_code=status_code, content={"detail": detail}, headers=headers)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "desconhecido"


@router.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=Me)
def register(
    request: RegisterRequest,
    http_request: Request,
    response: Response,
    db: Db,
    now: Now,
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Me | JSONResponse:
    key = throttle.register_key(_client_ip(http_request))
    throttle.lock(db, [key])
    retry = throttle.retry_after(db, [key], now)
    if retry is not None:
        return _failure_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "demasiadas tentativas; tenta novamente mais tarde",
            retry,
        )
    throttle.record(db, [key], now)
    try:
        user = accounts.register(db, request.email, request.password, request.display_name)
    except accounts.EmailInUseError as error:
        return _failure_response(status.HTTP_409_CONFLICT, str(error))
    if token:
        accounts.close_session(db, token)
    _set_cookie(response, accounts.open_session(db, user))
    return Me.of(user)


@router.post("/auth/login", response_model=Me)
def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
    db: Db,
    now: Now,
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Me | JSONResponse:
    keys = throttle.login_keys(request.email, _client_ip(http_request))
    throttle.lock(db, keys)
    retry = throttle.retry_after(db, keys, now)
    if retry is not None:
        return _failure_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "demasiadas tentativas; tenta novamente mais tarde",
            retry,
        )
    user = accounts.authenticate(db, request.email, request.password)
    if user is None:
        throttle.record(db, keys, now)
        # A resposta normal confirma os registos; lançar HTTPException faria rollback.
        return _failure_response(
            status.HTTP_401_UNAUTHORIZED,
            "email ou palavra-passe incorretos",
        )
    throttle.clear(db, throttle.LOGIN_ACCOUNT_IP, keys[1][1], now)
    if token:
        accounts.close_session(db, token)
    accounts.purge_expired_sessions(db, user, now)
    _set_cookie(response, accounts.open_session(db, user))
    return Me.of(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Db,
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    if token:
        accounts.close_session(db, token)
    _delete_cookie(response)


@router.get("/me")
def me(user: CurrentUser) -> Me:
    return Me.of(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: CurrentUser, response: Response, db: Db) -> None:
    accounts.delete_account(db, user)
    _delete_cookie(response)
