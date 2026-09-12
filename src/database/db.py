"""Engine/session factory shared by seed, repository, persist CLI and tests.

`get_engine()` is created lazily from `database_url()`; if the URL is not
configured, functions raise `DatabaseNotConfigured` — callers may opt to skip.
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.config import database_url, engine_kwargs, test_database_url


class DatabaseNotConfigured(RuntimeError):
    pass


def _engine_for(url: str) -> Engine:
    return create_engine(url, **engine_kwargs())


@lru_cache(maxsize=2)
def _cached_engine(url: str) -> Engine:
    return _engine_for(url)


def get_engine(require: bool = True) -> Engine:
    url = database_url()
    if not url:
        raise DatabaseNotConfigured("DATABASE_URL not set (see .env.example)")
    return _cached_engine(url)


def get_test_engine(require: bool = True) -> Engine:
    url = test_database_url()
    if not url:
        raise DatabaseNotConfigured(
            "DATABASE_URL / DATABASE_URL_TEST not set (see .env.example)")
    return _cached_engine(url)


def session_factory(engine: Engine | None = None) -> sessionmaker:
    return sessionmaker(bind=engine or get_engine(), autoflush=False, expire_on_commit=False)


def connect(engine: Engine | None = None) -> Session:
    """Convenience: open a session from the app engine."""
    return session_factory(engine)()


def ping(url: str | None = None) -> bool:
    """Lightweight reachability check (used by tests to skip when DB is down)."""
    import sqlalchemy

    url = url or database_url()
    if not url:
        return False
    try:
        e = _engine_for(url)
        with e.connect() as c:
            c.execute(sqlalchemy.text("SELECT 1"))
        e.dispose()
        return True
    except Exception:
        return False


def ping_test() -> bool:
    url = test_database_url()
    return bool(url and ping(url))