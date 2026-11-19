import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_web_serves_interface_without_hiding_api_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "index.html").write_text("<h1>Arquivo do Universo</h1>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('teste')")
    monkeypatch.setenv("ARQUIVO_FRONTEND_PATH", str(tmp_path))
    web = importlib.import_module("arquivo.web")
    with TestClient(web.app) as client:
        assert "Arquivo do Universo" in client.get("/").text
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/api/v1/health").json()["status"] == "ok"
        assert client.get("/api/v1/rota-inexistente").status_code == 404
        assert client.get("/../alembic.ini").status_code == 404
