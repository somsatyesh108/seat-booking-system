"""
conftest.py - Shared test helpers ("fixtures") for every test file.

pytest finds this file automatically. Any test that asks for `db_session`
gets a database session whose changes are ALWAYS undone after the test.
"""

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from app.database import engine


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

    # "create_savepoint": if the test commits or rolls back, it only affects
    # a savepoint INSIDE our outer transaction, so we can still undo everything.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()  # undo everything the test did
        connection.close()