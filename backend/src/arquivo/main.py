from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from arquivo import __version__
from arquivo.api import health
from arquivo.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Arquivo do Universo", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api/v1")
    return app


app = create_app()
