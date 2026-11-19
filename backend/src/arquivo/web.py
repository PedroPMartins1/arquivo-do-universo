"""Entrada de alojamento que serve a interface e a API na mesma origem."""

import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from arquivo.main import create_app

app = create_app()
app.mount(
    "/",
    StaticFiles(directory=Path(os.environ["ARQUIVO_FRONTEND_PATH"]), html=True),
    name="frontend",
)
