"""Unit tests for src.database.config (no PostgreSQL needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import config


def test_unset_returns_none(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_TEST", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    assert config.database_url() is None
    assert config.test_database_url() is None


def test_database_url_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@h:5433/db")
    monkeypatch.delenv("PGUSER", raising=False)
    assert config.database_url() == "postgresql+psycopg2://u:p@h:5433/db"


def test_test_url_derives_tail(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@h:5432/sih2026_app")
    monkeypatch.delenv("DATABASE_URL_TEST", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    url = config.test_database_url()
    assert url.endswith("/sih2026_app_test")


def test_test_url_explicit(monkeypatch):
    monkeypatch.setenv("DATABASE_URL_TEST",
                       "postgresql+psycopg2://u:p@h:5432/sih2026_app_test")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    assert config.test_database_url().endswith("/sih2026_app_test")


def test_pg_parts_fallback(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("PGUSER", "john")
    monkeypatch.setenv("PGPASSWORD", "secret")
    monkeypatch.setenv("PGHOST", "10.0.0.1")
    monkeypatch.setenv("PGPORT", "5433")
    monkeypatch.setenv("PGDATABASE", "mydb")
    assert config.database_url() == (
        "postgresql+psycopg2://john:secret@10.0.0.1:5433/mydb")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))