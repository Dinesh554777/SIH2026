"""Database configuration: resolve the app/test DSN from environment only.

Rules (Phase I-A STEP 4)
- Never hardcode usernames, passwords, hosts or database URLs in source.
- Prefer the single `DATABASE_URL`; fall back to PG* parts if provided.
- Test DSN: `DATABASE_URL_TEST`, else the app DSN with the database name
  replaced by <name>_test (used only by the test suite).

`.env` files at the repository root are loaded when present (so alembic,
seed, pytest and the app all see the same DATABASE_URL without shell
plumbing); real environment variables always take precedence.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlalchemy.engine.url import make_url

try:  # python-dotenv is optional; without it `.env` is simply not loaded
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

DEFAULT_PORT = 5432
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_envfile() -> None:
    if load_dotenv is None:
        return
    for candidate in (_REPO_ROOT / ".env", Path.cwd() / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return


def _from_parts() -> Optional[str]:
    user = os.environ.get("PGUSER")
    if not user:
        return None
    password = os.environ.get("PGPASSWORD", "")
    host = os.environ.get("PGHOST", "127.0.0.1")
    port = os.environ.get("PGPORT", str(DEFAULT_PORT))
    dbname = os.environ.get("PGDATABASE", "sih2026_app")
    cred = user if not password else f"{user}:{password}"
    return f"postgresql+psycopg2://{cred}@{host}:{port}/{dbname}"


def database_url() -> Optional[str]:
    """Resolve the application DSN. Returns None when not configured (caller decides)."""
    _load_envfile()
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    return _from_parts()


def _swap_dbname(url: str, new_db: str) -> str:
    parsed = make_url(url)
    return parsed.set(database=new_db).render_as_string(hide_password=False)


def test_database_url() -> Optional[str]:
    """Test DSN: DATABASE_URL_TEST, else app DSN with `_test` database name."""
    _load_envfile()
    url = os.environ.get("DATABASE_URL_TEST")
    if url:
        return url
    app = database_url()
    if not app:
        return None
    return _swap_dbname(app, _test_name_for(app))


def _test_name_for(url: str) -> str:
    db = make_url(url).database or "sih2026_app"
    return db if db.endswith("_test") else f"{db}_test"


def engine_kwargs() -> dict:
    """Connection tuning shared by dev/test engines."""
    return {
        "pool_pre_ping": True,
        "pool_size": 5,
        "connect_args": {
            "connect_timeout": 5,
            "application_name": "sih2026_app",
        },
    }