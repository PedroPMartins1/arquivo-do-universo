from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, StringConstraints

from arquivo.api.deps import SESSION_COOKIE, CurrentUser, Db
from arquivo.config import get_settings
from arquivo.persistence import accounts
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


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, response: Response, db: Db) -> Me:
    try:
        user = accounts.register(db, request.email, request.password, request.display_name)
    except accounts.EmailInUseError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    _set_cookie(response, accounts.open_session(db, user))
    return Me.of(user)


@router.post("/auth/login")
def login(request: LoginRequest, response: Response, db: Db) -> Me:
    user = accounts.authenticate(db, request.email, request.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "email ou palavra-passe incorretos")
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
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
def me(user: CurrentUser) -> Me:
    return Me.of(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: CurrentUser, response: Response, db: Db) -> None:
    accounts.delete_account(db, user)
    response.delete_cookie(SESSION_COOKIE, path="/")
