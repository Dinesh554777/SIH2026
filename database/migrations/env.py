"""Alembic environment (Phase I-A).

The DSN is resolved from environment through src.database.config so migrations
can run against dev (DATABASE_URL) or test (DATABASE_URL_TEST via
--name test) without hardcoding credentials.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_url() -> str:
    from src.database.config import database_url, test_database_url

    cfg = config.get_main_option("sqlalchemy.url")
    if cfg:
        return cfg
    section = config.get_section(config.config_ini_section) or {}
    if section.get("is_test_runner") == "True":
        url = test_database_url()
    else:
        url = database_url()
    if not url:
        raise RuntimeError(
            "DATABASE_URL (or DATABASE_URL_TEST for --name test) is not set; "
            "see .env.example.")
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=_resolve_url(),
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()