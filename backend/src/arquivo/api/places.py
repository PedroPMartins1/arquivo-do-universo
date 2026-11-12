from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from arquivo.api.deps import Db
from arquivo.persistence.places import search_places
from arquivo.places.geonames import ATTRIBUTION

router = APIRouter(tags=["Localidades"])


class PlaceOut(BaseModel):
    id: int
    name: str
    region: str | None
    country_code: str
    latitude: float
    longitude: float
    zone: str


class PlaceSearch(BaseModel):
    results: list[PlaceOut]
    attribution: str = ATTRIBUTION


@router.get("/places")
def places(db: Db, q: Annotated[str, Query(min_length=2, max_length=100)]) -> PlaceSearch:
    return PlaceSearch(
        results=[
            PlaceOut(
                id=p.geoname_id,
                name=p.name,
                region=p.region,
                country_code=p.country_code,
                latitude=p.latitude,
                longitude=p.longitude,
                zone=p.zone,
            )
            for p in search_places(db, q)
        ]
    )
