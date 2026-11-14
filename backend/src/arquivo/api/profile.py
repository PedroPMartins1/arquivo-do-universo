from datetime import date, datetime, time
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, StringConstraints

from arquivo.api.auth import Me
from arquivo.api.deps import CurrentUser, Db
from arquivo.natal.birth import InexactBirthDataError, resolve_birth_instant
from arquivo.natal.chart import ChartError, NatalChart, calculate_chart
from arquivo.persistence.accounts import audit
from arquivo.persistence.models import BirthProfile, User
from arquivo.temporal.zones import UnknownTimeZoneError, zone_for_coordinates
from arquivo.transits.engine import DailySky, daily_sky

router = APIRouter(prefix="/me", tags=["Perfil"])


class BirthData(BaseModel):
    birth_date: date
    birth_time: time
    place_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    zone: str | None = None
    occurrence: Literal[0, 1] | None = None


class BirthProfileOut(BirthData):
    zone: str
    birth_utc: datetime
    tzdata_version: str | None


def _out(profile: BirthProfile) -> BirthProfileOut:
    return BirthProfileOut(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        place_name=profile.place_name,
        latitude=profile.latitude,
        longitude=profile.longitude,
        zone=profile.zone,
        occurrence=profile.occurrence if profile.occurrence in (0, 1) else None,
        birth_utc=profile.birth_utc,
        tzdata_version=profile.tzdata_version,
    )


def _profile(db: Db, user: CurrentUser) -> BirthProfile:
    profile = db.get(BirthProfile, user.id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "dados de nascimento ainda não indicados")
    return profile


@router.put("/birth")
def save_birth(data: BirthData, user: CurrentUser, db: Db) -> BirthProfileOut:
    zone = data.zone
    if zone is None:
        lookup = zone_for_coordinates(data.latitude, data.longitude)
        if lookup is None:
            raise HTTPException(422, "não foi possível determinar o fuso destas coordenadas")
        zone = lookup.zone
    try:
        instant = resolve_birth_instant(
            data.birth_date, data.birth_time, zone, occurrence=data.occurrence
        )
    except (InexactBirthDataError, UnknownTimeZoneError) as error:
        raise HTTPException(422, str(error)) from error
    profile = db.get(BirthProfile, user.id) or BirthProfile(user_id=user.id)
    profile.birth_date = data.birth_date
    profile.birth_time = data.birth_time
    profile.place_name = data.place_name.strip()
    profile.latitude = data.latitude
    profile.longitude = data.longitude
    profile.zone = zone
    profile.occurrence = data.occurrence
    profile.birth_utc = instant.utc
    profile.tzdata_version = instant.resolution.tzdata_version
    db.add(profile)
    db.flush()
    audit(db, user.id, "birth_profile.saved")
    return _out(profile)


@router.get("/birth")
def get_birth(user: CurrentUser, db: Db) -> BirthProfileOut:
    return _out(_profile(db, user))


def _chart(profile: BirthProfile) -> NatalChart:
    try:
        return calculate_chart(profile.birth_utc, profile.latitude, profile.longitude)
    except ChartError as error:
        raise HTTPException(422, str(error)) from error


def _daily_sky(
    user: User, profile: BirthProfile, day: date | None = None
) -> tuple[NatalChart, DailySky]:
    zone = user.residence_zone or profile.zone
    day = day or datetime.now(ZoneInfo(zone)).date()
    if not 1801 <= day.year <= 2398:
        raise HTTPException(422, "data fora do intervalo das efemérides (1801–2398)")
    chart = _chart(profile)
    try:
        return chart, daily_sky(chart, day, zone)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.get("/chart")
def my_chart(user: CurrentUser, db: Db) -> NatalChart:
    return _chart(_profile(db, user))


class Residence(BaseModel):
    place_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    zone: Annotated[str, StringConstraints(min_length=1, max_length=64)]


@router.put("/residence")
def save_residence(data: Residence, user: CurrentUser, db: Db) -> Me:
    try:
        ZoneInfo(data.zone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(422, f"fuso desconhecido: {data.zone}") from error
    user.residence_name = data.place_name
    user.residence_zone = data.zone
    db.flush()
    return Me.of(user)


@router.get("/today")
def today(
    user: CurrentUser,
    db: Db,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> DailySky:
    """O céu do dia, no fuso onde a pessoa vive (por omissão, o do nascimento)."""
    profile = _profile(db, user)
    _, sky = _daily_sky(user, profile, day)
    return sky
