from fastapi.testclient import TestClient

from arquivo.main import create_app

client = TestClient(create_app())


def test_resolve_with_zone() -> None:
    response = client.post(
        "/api/v1/temporal/resolve",
        json={"local_datetime": "2024-10-27T01:30:00", "zone": "Europe/Lisbon"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resolution"]["status"] == "ambiguous"
    assert body["zone_lookup"] is None


def test_resolve_with_coordinates_and_uncertainty() -> None:
    response = client.post(
        "/api/v1/temporal/resolve",
        json={
            "local_datetime": "1990-01-15T08:00:00",
            "latitude": 41.1579,
            "longitude": -8.6291,
            "uncertainty_minutes": 15,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["zone_lookup"]["zone"] == "Europe/Lisbon"
    assert body["resolution"]["earliest_utc"] == "1990-01-15T07:45:00Z"


def test_resolve_requires_zone_or_coordinates() -> None:
    response = client.post("/api/v1/temporal/resolve", json={"local_datetime": "2024-01-01T00:00"})
    assert response.status_code == 422


def test_resolve_rejects_unknown_zone() -> None:
    response = client.post(
        "/api/v1/temporal/resolve",
        json={"local_datetime": "2024-01-01T00:00", "zone": "Mars/Olympus"},
    )
    assert response.status_code == 422


def test_epistemic_classes_are_listed() -> None:
    body = client.get("/api/v1/epistemics/classes").json()
    by_id = {item["id"]: item for item in body}
    assert by_id["interpretation"]["allowed_in_astrology"] is True
    assert by_id["prediction"]["allowed_in_astrology"] is False
