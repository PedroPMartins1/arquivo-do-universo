from fastapi.testclient import TestClient

from arquivo.main import create_app


def test_health_reports_ok() -> None:
    response = TestClient(create_app()).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
