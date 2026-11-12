"""Base de localidades para escolher o local de nascimento."""

import sys
from collections.abc import Iterable
from itertools import batched
from pathlib import Path

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from arquivo.persistence.models import Place
from arquivo.places.geonames import PlaceRecord, normalize, read_admin1, read_cities


def replace_places(session: Session, records: Iterable[PlaceRecord]) -> int:
    session.execute(delete(Place))
    total = 0
    for batch in batched(records, 5000):
        session.execute(insert(Place), [record.__dict__ for record in batch])
        total += len(batch)
    return total


def search_places(session: Session, query: str, limit: int = 10) -> list[Place]:
    term = normalize(query).replace("\\", "").replace("%", "").replace("_", "")
    if len(term) < 2:
        return []
    statement = (
        select(Place)
        .where(Place.search_text.like(f"%|{term}%"))
        .order_by(
            Place.search_text.like(f"|{term}|%").desc(),
            Place.search_text.like(f"%|{term}|%").desc(),
            Place.population.desc(),
            Place.name,
        )
        .limit(limit)
    )
    return list(session.scalars(statement))


def main(directory: Path) -> None:
    from arquivo.persistence.session import get_sessionmaker

    admin1 = read_admin1(directory / "admin1CodesASCII.txt")
    with get_sessionmaker()() as session, session.begin():
        total = replace_places(session, read_cities(directory / "cities500.txt", admin1))
    print(f"{total} localidades carregadas")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
