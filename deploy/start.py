"""Inicializa uma instância de teste e entrega o processo ao servidor web."""

import json
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from arquivo.persistence.models import Place
from arquivo.persistence.places import replace_places
from arquivo.places.geonames import read_admin1, read_cities
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


def main() -> None:
    database_url = make_url(os.environ["DATABASE_URL"])
    database_url = database_url.set(drivername="postgresql+psycopg")
    os.environ["ARQUIVO_DATABASE_URL"] = database_url.render_as_string(hide_password=False)
    os.environ.setdefault("ARQUIVO_ENVIRONMENT", "production")
    os.environ.setdefault("ARQUIVO_PUBLIC_URL", os.environ["RENDER_EXTERNAL_URL"])
    os.environ.setdefault("ARQUIVO_CORS_ORIGINS", json.dumps([os.environ["RENDER_EXTERNAL_URL"]]))

    # Validar antes de alterar a base de dados. Os valores secretos nunca são impressos.
    from arquivo.config import get_settings

    get_settings()
    engine = create_engine(database_url)
    with engine.connect() as connection:
        # Serializa migrações/importação quando dois arranques se sobrepõem.
        connection.execute(text("SELECT pg_advisory_lock(8402191119)"))
        connection.commit()
        try:
            config = Config("alembic.ini")
            config.attributes["database_url"] = os.environ["ARQUIVO_DATABASE_URL"]
            command.upgrade(config, "head")
            with Session(engine) as session, session.begin():
                if session.scalar(select(Place.geoname_id).limit(1)) is None:
                    directory = Path(os.environ["ARQUIVO_GEONAMES_PATH"])
                    regions = read_admin1(directory / "admin1CodesASCII.txt")
                    count = replace_places(
                        session, read_cities(directory / "cities500.txt", regions)
                    )
                    print(f"{count} localidades carregadas", flush=True)
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(8402191119)"))
            connection.commit()
    engine.dispose()
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "arquivo.web:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("PORT", "10000"),
            "--no-proxy-headers",
            "--no-access-log",
        ],
    )


if __name__ == "__main__":
    main()
