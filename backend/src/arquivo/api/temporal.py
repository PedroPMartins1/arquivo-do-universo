from datetime import datetime
from typing import Self

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, NaiveDatetime, model_validator

from arquivo.temporal.local_time import LocalTimeResolution, resolve_local_time
from arquivo.temporal.zones import UnknownTimeZoneError, ZoneLookup, zone_for_coordinates

router = APIRouter(prefix="/temporal", tags=["F60 — Inteligência Temporal"])


class ResolveRequest(BaseModel):
    local_datetime: NaiveDatetime
    zone: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    uncertainty_minutes: int = Field(default=0, ge=0, le=24 * 60)

    @model_validator(mode="after")
    def _zone_or_coordinates(self) -> Self:
        has_coordinates = self.latitude is not None and self.longitude is not None
        if self.zone is None and not has_coordinates:
            raise ValueError("indicar o fuso IANA ou as coordenadas (latitude e longitude)")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude e longitude têm de ser indicadas em conjunto")
        return self


class ResolveResponse(BaseModel):
    resolution: LocalTimeResolution
    zone_lookup: ZoneLookup | None


@router.post("/resolve")
def resolve(request: ResolveRequest) -> ResolveResponse:
    lookup: ZoneLookup | None = None
    zone = request.zone
    if zone is None:
        assert request.latitude is not None and request.longitude is not None
        lookup = zone_for_coordinates(request.latitude, request.longitude)
        if lookup is None:
            raise HTTPException(422, "não foi possível determinar o fuso para estas coordenadas")
        zone = lookup.zone
    local: datetime = request.local_datetime
    try:
        resolution = resolve_local_time(
            local, zone, uncertainty_minutes=request.uncertainty_minutes
        )
    except UnknownTimeZoneError as error:
        raise HTTPException(422, str(error)) from error
    return ResolveResponse(resolution=resolution, zone_lookup=lookup)
