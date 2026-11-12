"""Fusos IANA reprodutíveis: carregados sempre do pacote `tzdata` fixado, nunca do sistema."""

import importlib.metadata
import importlib.resources
import re
from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict
from timezonefinder import TimezoneFinder

TZDATA_VERSION = importlib.metadata.version("tzdata")
TIMEZONEFINDER_VERSION = importlib.metadata.version("timezonefinder")

_ZONE_NAME = re.compile(r"^[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+)*$")


class UnknownTimeZoneError(ValueError):
    pass


@lru_cache(maxsize=512)
def load_zone(name: str) -> ZoneInfo:
    if not _ZONE_NAME.fullmatch(name):
        raise UnknownTimeZoneError(f"nome de fuso inválido: {name!r}")
    resource = importlib.resources.files("tzdata.zoneinfo").joinpath(*name.split("/"))
    if not resource.is_file():
        raise UnknownTimeZoneError(f"fuso desconhecido: {name!r}")
    with resource.open("rb") as handle:
        return ZoneInfo.from_file(handle, key=name)


class ZoneLookup(BaseModel):
    model_config = ConfigDict(frozen=True)

    zone: str
    method: str
    warnings: tuple[str, ...]


@lru_cache(maxsize=1)
def _finder() -> TimezoneFinder:
    return TimezoneFinder()


def zone_for_coordinates(latitude: float, longitude: float) -> ZoneLookup | None:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("coordenadas fora do intervalo válido")
    zone = _finder().timezone_at(lat=latitude, lng=longitude)
    if zone is None:
        return None
    return ZoneLookup(
        zone=zone,
        method=f"timezonefinder {TIMEZONEFINDER_VERSION}",
        warnings=(
            "As fronteiras de fuso usadas são as atuais. Para datas históricas, confirmar que o "
            "local pertencia a este fuso.",
        ),
    )
