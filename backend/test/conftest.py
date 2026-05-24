"""Shared pytest fixtures for the backend test suite."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from repositories import DataStore, connection


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    """Point DataStore at an isolated temp-file SQLite database for one test."""
    db_path = tmp_path / "test_zzz_bot.db"
    monkeypatch.setattr(connection, "get_db_path", lambda: str(db_path))
    connection.reset_connection()
    monkeypatch.setattr(DataStore, "_schema_ready", False)
    monkeypatch.setattr(DataStore, "_last_purge_monotonic", 0.0)
    DataStore.ensure_schema()

    yield DataStore

    connection.reset_connection()
