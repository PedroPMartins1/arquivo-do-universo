from datetime import date, datetime, time
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from arquivo.natal.birth import InexactBirthDataError, resolve_birth_instant
from arquivo.natal.chart import ChartError, NatalChart, calculate_chart
from arquivo.natal.labels import label
from arquivo.natal.settings import (
    DEFAULT_ORBS,
    AspectKind,
    Ayanamsa,
    Body,
    ChartSettings,
    HouseSystem,
    Sign,
    Zodiac,
)
from arquivo.temporal.zones import UnknownTimeZoneError, zone_for_coordinates

router = APIRouter(prefix="/natal", tags=["AU-AST — Mapa Natal"])


class ChartRequest(BaseModel):
    birth_date: date
    birth_time: time
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    zone: str | None = None
    occurrence: Literal[0, 1] | None = None
    settings: ChartSettings = Field(default_factory=ChartSettings)


class BirthSummary(BaseModel):
    utc: datetime
    zone: str
    utc_offset_seconds: int
    abbreviation: str | None
    warnings: list[str]


class ChartResponse(BaseModel):
    birth: BirthSummary
    chart: NatalChart


class Option(BaseModel):
    id: str
    label: str


class Options(BaseModel):
    zodiacs: list[Option]
    ayanamsas: list[Option]
    house_systems: list[Option]
    bodies: list[Option]
    aspects: list[Option]
    signs: list[Option]
    default_orbs: dict[AspectKind, float]
    defaults: ChartSettings


def _options(
    values: type[Zodiac | Ayanamsa | HouseSystem | Body | AspectKind | Sign],
) -> list[Option]:
    return [Option(id=v.value, label=label(v)) for v in values]


@router.get("/options")
def options() -> Options:
    return Options(
        zodiacs=_options(Zodiac),
        ayanamsas=_options(Ayanamsa),
        house_systems=_options(HouseSystem),
        bodies=_options(Body),
        aspects=_options(AspectKind),
        signs=_options(Sign),
        default_orbs=DEFAULT_ORBS,
        defaults=ChartSettings(),
    )


@router.post("/chart")
def chart(request: ChartRequest) -> ChartResponse:
    warnings: list[str] = []
    zone = request.zone
    if zone is None:
        lookup = zone_for_coordinates(request.latitude, request.longitude)
        if lookup is None:
            raise HTTPException(422, "não foi possível determinar o fuso: indicar 'zone'")
        zone = lookup.zone
        warnings.extend(lookup.warnings)
    try:
        instant = resolve_birth_instant(
            request.birth_date, request.birth_time, zone, occurrence=request.occurrence
        )
        natal = calculate_chart(instant.utc, request.latitude, request.longitude, request.settings)
    except (InexactBirthDataError, UnknownTimeZoneError, ChartError) as error:
        raise HTTPException(422, str(error)) from error
    warnings.extend(instant.resolution.warnings)
    return ChartResponse(
        birth=BirthSummary(
            utc=instant.utc,
            zone=zone,
            utc_offset_seconds=instant.utc_offset_seconds,
            abbreviation=instant.abbreviation,
            warnings=warnings,
        ),
        chart=natal,
    )
