"""
conftest.py - Shared test helpers ("fixtures") for every test file.

pytest finds this file automatically.
  db_session -> a database session whose changes are ALWAYS undone after the test
  client     -> a fake browser for calling our API, wired to use db_session
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app


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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    A fake browser for calling the API inside tests.

    Every endpoint that asks for get_db() receives the test's db_session instead,
    so users created through the API (Som, Nahul, Priya) are rolled back afterwards.
    """

    def use_test_session() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = use_test_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()  # put the real get_db back