from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from arquivo.api.deps import get_db
from arquivo.main import create_app
from arquivo.persistence.places import replace_places, search_places
from arquivo.places.geonames import normalize, read_admin1, read_cities


def _city(gid: int, name: str, alt: str, cc: str, adm: str, pop: int, zone: str) -> str:
    cols = [str(gid), name, normalize(name), alt, "38.7", "-9.1", "P", "PPLC", cc, "", adm]
    return "\t".join([*cols, "", "", "", str(pop), "", "", zone, "2024-01-01"])


def _fixture(tmp_path: Path) -> Path:
    (tmp_path / "admin1CodesASCII.txt").write_text("PT.14\tLisbon\tLisbon\t2267056\n")
    rows = [
        _city(2267057, "Lisbon", "Lisboa,Lisabona,Олисипо", "PT", "14", 517802, "Europe/Lisbon"),
        _city(2268339, "Óbidos", "Obidos", "PT", "13", 3100, "Europe/Lisbon"),
        _city(1, "Lisburn", "", "GB", "NIR", 45000, "Europe/London"),
        _city(2, "Sem fuso", "", "PT", "14", 10, ""),
        _city(3, "Porto Alegre", "", "BR", "23", 1400000, "America/Sao_Paulo"),
        _city(4, "Porto", "Oporto", "PT", "17", 250000, "Europe/Lisbon"),
    ]
    (tmp_path / "cities500.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return tmp_path


def test_normalize() -> None:
    assert normalize("  São-João d'Arga ") == "sao joao d arga"


def test_read_cities(tmp_path: Path) -> None:
    directory = _fixture(tmp_path)
    records = list(
        read_cities(directory / "cities500.txt", read_admin1(directory / "admin1CodesASCII.txt"))
    )
    assert [r.name for r in records][:3] == ["Lisbon", "Óbidos", "Lisburn"]
    assert records[0].region == "Lisbon"
    assert "|lisboa|" in records[0].search_text


def test_search_by_alternate_name_and_without_accents(session: Session, tmp_path: Path) -> None:
    directory = _fixture(tmp_path)
    admin1 = read_admin1(directory / "admin1CodesASCII.txt")
    assert replace_places(session, read_cities(directory / "cities500.txt", admin1)) == 5
    assert [p.name for p in search_places(session, "lisboa")] == ["Lisbon"]
    assert [p.name for p in search_places(session, "LISB")] == ["Lisbon", "Lisburn"]
    assert [p.name for p in search_places(session, "obido")] == ["Óbidos"]
    assert search_places(session, "%") == []
    assert [p.name for p in search_places(session, "porto")] == ["Porto", "Porto Alegre"]

    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    response = TestClient(app).get("/api/v1/places", params={"q": "Óbi"})
    body = response.json()
    assert body["results"][0]["zone"] == "Europe/Lisbon"
    assert "GeoNames" in body["attribution"]
