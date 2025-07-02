# tests/e2e/conftest.py
import os

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from sqlalchemy import create_engine, text

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "example")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3307")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "fastapi_db_test")
os.environ["DATABASE_URL"] = (
    f"mysql+mysqldb://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    admin_url = (
        f"mysql+mysqldb://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
    )
    admin_engine = create_engine(admin_url, pool_pre_ping=True)
    db_name = MYSQL_DATABASE
    with admin_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(
            text(
                f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    # Set DATABASE_URL for Alembic to use the test DB
    os.environ["DATABASE_URL"] = (
        f"mysql+mysqldb://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    os.system(f"PYTHONPATH=. alembic upgrade head")
    yield
    with admin_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))


# MongoDB cleanup before/after each test
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB = os.getenv("MONGODB_DB")


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_mongo_db():
    client = AsyncMongoClient(MONGODB_URL)
    await client.drop_database(MONGODB_DB)  # drop before
    yield
    await client.drop_database(MONGODB_DB)  # drop after
    await client.close()
