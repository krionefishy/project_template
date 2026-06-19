import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from backend.shared.settings.config import default_config_path, load_settings
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from backend.storage.pg.database import Base

# --- Register all ORM models here so Alembic can detect schema changes ---
# Add a new import every time you create a new db_models.py file
import backend.app.example_domain.db_models  # noqa: F401 - register tables with Base.metadata
# import backend.app.users.db_models            # noqa: F401
# import backend.app.orders.db_models           # noqa: F401

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url is not set in alembic.ini or environment")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        config_path = os.getenv("CONFIG_PATH", str(default_config_path()))
        database_url = load_settings(config_path).database.url

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    connectable = create_async_engine(database_url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        def run_migrations(conn):
            context.configure(
                connection=conn,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(run_migrations)


def run_migrations_online() -> None:
    """Entry point for online mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
