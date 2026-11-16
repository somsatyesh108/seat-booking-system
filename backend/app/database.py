"""
database.py - Connection to PostgreSQL using SQLAlchemy.

Every other file that needs the database imports from here.
"""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# The engine manages a "pool" of open connections to PostgreSQL.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # test a connection before using it (avoids stale ones)
    pool_size=10,         # keep up to 10 connections ready
    max_overflow=20,      # allow 20 extra during busy moments
)

# A factory that creates a new Session (one "conversation" with the database).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for all our database tables (users, shows, seats, bookings)."""


def get_db() -> Generator[Session, None, None]:
    """
    Give one database session to an API request, and always close it after.

    Example: when Priya books a seat, her request gets its own session,
    and it is closed even if something goes wrong.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database() -> bool:
    """Return True if PostgreSQL answers a simple query, otherwise False."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as error:
        logger.warning("Database health check failed: %s", error)
        return False
