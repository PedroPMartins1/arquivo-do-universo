from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from arquivo import __version__
from arquivo.api import auth, epistemics, health, natal, places, profile, reading, temporal
from arquivo.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Arquivo do Universo", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_credentials=True,
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(epistemics.router, prefix="/api/v1")
    app.include_router(temporal.router, prefix="/api/v1")
    app.include_router(natal.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(profile.router, prefix="/api/v1")
    app.include_router(reading.router, prefix="/api/v1")
    app.include_router(places.router, prefix="/api/v1")
    return app


app = create_app()
