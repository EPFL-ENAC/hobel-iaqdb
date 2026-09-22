"""Tests run against a throwaway TimescaleDB (`make test-db`, port 5433).
They truncate tables, so any other port is refused."""

import os
import subprocess
import sys

import pytest
import pytest_asyncio
from api.config import config
from api.db import get_engine, get_session
from api.main import app
from api.services.parameter import ParameterService
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

TEST_DB_PORT = 5433
CATALOG_TABLES = (
    "measurement",
    "dataset_parameter",
    "variable",
    "dataset",
    "instrumentparameter",
    "instrument",
    "certification",
    "space",
    "building",
    "person",
    "contribution",
    "study",
)


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    if config.DB_PORT != TEST_DB_PORT and not os.environ.get("IAQDB_TEST_ANY_PORT"):
        raise RuntimeError(
            f"tests truncate the database: refusing DB_PORT={config.DB_PORT},"
            f" expected {TEST_DB_PORT} (see `make test-db`)"
        )
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], check=True
    )


@pytest_asyncio.fixture(scope="session")
async def engine(migrated_db):
    engine = create_async_engine(config.DB_URL, pool_size=5, max_overflow=5)
    async with AsyncSession(engine) as session:
        await ParameterService(session).sync()
        await session.commit()
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def clean_db(engine):
    """Empty catalog and measurements before every test."""
    async with engine.begin() as conn:
        await conn.execute(
            text(f"TRUNCATE {', '.join(CATALOG_TABLES)} RESTART IDENTITY CASCADE")
        )
        await conn.execute(text("UPDATE catalog_version SET version = 1"))
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        for view in ("measurement_hour", "measurement_day"):
            await conn.execute(
                text(f"CALL refresh_continuous_aggregate('{view}', NULL, NULL)")
            )
    yield engine


@pytest_asyncio.fixture
async def session(clean_db):
    async with AsyncSession(clean_db, expire_on_commit=False) as session:
        yield session


@pytest_asyncio.fixture
async def client(clean_db):
    async def override_session():
        async with AsyncSession(clean_db, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_engine] = lambda: clean_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
