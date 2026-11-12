import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from arquivo.config import get_settings


def _test_database_url() -> str:
    explicit = os.environ.get("ARQUIVO_TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = make_url(get_settings().database_url)
    return base.set(database=f"{base.database}_test").render_as_string(hide_password=False)


def _alembic_config(url: str) -> Config:
    config = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    config.attributes["database_url"] = url
    return config


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    url = make_url(_test_database_url())
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
            connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    except Exception as error:  # pragma: no cover - depende do ambiente
        pytest.skip(f"PostgreSQL indisponível: {error}")
    rendered = url.render_as_string(hide_password=False)
    command.upgrade(_alembic_config(rendered), "head")
    yield rendered
    admin.dispose()


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def alembic_config(database_url: str) -> Config:
    return _alembic_config(database_url)
