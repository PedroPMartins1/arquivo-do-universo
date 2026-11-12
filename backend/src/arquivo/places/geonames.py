"""Leitura dos ficheiros do GeoNames (https://www.geonames.org, CC BY 4.0)."""

import csv
import sys
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ATTRIBUTION = "Localidades: GeoNames (geonames.org), licença CC BY 4.0"


def normalize(text: str) -> str:
    """Minúsculas, sem acentos e com espaços simples, para pesquisa."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.replace("-", " ").replace("'", " ").split())


@dataclass(frozen=True)
class PlaceRecord:
    geoname_id: int
    name: str
    region: str | None
    country_code: str
    latitude: float
    longitude: float
    zone: str
    population: int
    search_text: str
    """Nome principal normalizado primeiro, depois os alternativos, entre `|`."""


def _rows(path: Path) -> Iterator[list[str]]:
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding="utf-8", newline="") as handle:
        yield from csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)


def read_admin1(path: Path) -> dict[str, str]:
    return {row[0]: row[1] for row in _rows(path) if len(row) >= 2}


def read_cities(path: Path, admin1: dict[str, str]) -> Iterator[PlaceRecord]:
    for row in _rows(path):
        if len(row) < 19 or not row[17]:
            continue
        primary = normalize(row[1])
        names = {row[2], *row[3].split(",")}
        others = sorted({n for n in (normalize(name) for name in names) if n} - {primary})
        yield PlaceRecord(
            geoname_id=int(row[0]),
            name=row[1],
            region=admin1.get(f"{row[8]}.{row[10]}"),
            country_code=row[8],
            latitude=float(row[4]),
            longitude=float(row[5]),
            zone=row[17],
            population=int(row[14] or 0),
            search_text="|" + "|".join([primary, *others]) + "|",
        )
