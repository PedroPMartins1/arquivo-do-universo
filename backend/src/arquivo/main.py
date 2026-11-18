from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from arquivo import __version__
from arquivo.api import auth, epistemics, health, journal, natal, places, profile, reading, temporal
from arquivo.config import get_settings

NO_STORE_ROUTES = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/me"),
}


class CSRFMiddleware:
    def __init__(self, app: ASGIApp, trusted_origins: list[str]) -> None:
        self.app = app
        self.trusted_origins = set(trusted_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD", "OPTIONS"}:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin")
        if origin is not None:
            allowed = origin in self.trusted_origins
        else:
            fetch_site = headers.get("sec-fetch-site")
            referer = headers.get("referer")
            if fetch_site is not None:
                allowed = fetch_site in {"same-origin", "none"}
            elif referer is not None:
                try:
                    parsed = urlsplit(referer)
                except ValueError:
                    allowed = False
                else:
                    allowed = f"{parsed.scheme}://{parsed.netloc}" in self.trusted_origins
            else:
                allowed = True

        if not allowed:
            response = JSONResponse(
                status_code=403,
                content={"detail": "origem do pedido não autorizada"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class AuthNoStoreMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or (scope["method"], scope["path"]) not in NO_STORE_ROUTES:
            await self.app(scope, receive, send)
            return

        async def send_no_store(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, send_no_store)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Arquivo do Universo", version=__version__)
    app.add_middleware(
        CSRFMiddleware,
        trusted_origins=settings.cors_origins,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_credentials=True,
        allow_headers=["Content-Type"],
    )
    if settings.trusted_proxies:
        app.add_middleware(
            ProxyHeadersMiddleware,
            trusted_hosts=settings.trusted_proxies,
        )
    app.add_middleware(AuthNoStoreMiddleware)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {
                        "type": item["type"],
                        "loc": item["loc"],
                        "msg": item["msg"],
                    }
                    for item in error.errors()
                ]
            },
        )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(epistemics.router, prefix="/api/v1")
    app.include_router(temporal.router, prefix="/api/v1")
    app.include_router(natal.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(profile.router, prefix="/api/v1")
    app.include_router(reading.router, prefix="/api/v1")
    app.include_router(journal.router, prefix="/api/v1")
    app.include_router(places.router, prefix="/api/v1")
    return app


app = create_app()
