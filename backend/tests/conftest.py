"""
conftest.py - Shared test helpers ("fixtures") for every test file.

pytest finds this file automatically.
  db_session -> a database session whose changes are ALWAYS undone after the test
  test_redis -> a separate Redis database (number 15), wiped before and after each test
  client     -> a fake browser for calling our API, wired to use db_session and test_redis
"""

from collections.abc import Generator

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, get_db
from app.main import app
from app.redis_client import get_redis

# The app uses Redis database 0. Tests use database 15, so real holds are never touched.
TEST_REDIS_DB = 15


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Give one test a database session, then roll back everything it did.

    Example: a test creates "Som" and "Nahul" and tries to double-book seat A1.
    After the test, Som, Nahul and the booking attempt all disappear,
    and the sample shows from seed.py are untouched.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()

    # "create_savepoint": if the code under test commits or rolls back, it only affects
    # a savepoint INSIDE our outer transaction, so we can still undo everything.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()  # undo everything the test did
        connection.close()


@pytest.fixture
def test_redis() -> Generator[redis.Redis, None, None]:
    """A clean, separate Redis database for one test. Wiped before and after."""
    settings = get_settings()
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=TEST_REDIS_DB,
        decode_responses=True,
    )
    client.flushdb()  # start empty
    try:
        yield client
    finally:
        client.flushdb()  # leave nothing behind
        client.close()


@pytest.fixture
def client(db_session: Session, test_redis: redis.Redis) -> Generator[TestClient, None, None]:
    """
    A fake browser for calling the API inside tests.

    Every endpoint that asks for get_db() gets the test's db_session, and every endpoint
    that asks for get_redis() gets test_redis. Nothing real is changed.
    """

    def use_test_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = use_test_session
    app.dependency_overrides[get_redis] = lambda: test_redis
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()  # put the real get_db and get_redis back