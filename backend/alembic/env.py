"""
alembic/env.py - Tells Alembic how to connect to PostgreSQL
and which models (tables) to compare against the real database.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (loads User, Show, Seat, Booking so Alembic can see them)
from app.config import get_settings
from app.database import Base

# Alembic's settings, read from alembic.ini
config = context.config

# Use the database address from our .env file (never hard-code passwords).
# "%" is doubled because alembic.ini treats a single "%" as a special character.
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))

# Set up logging using the settings in alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The "blueprint": all tables defined in models.py
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Write the SQL to the screen instead of running it (rarely used)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to PostgreSQL and apply the changes (the normal mode)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # also notice when a column's type changes
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()