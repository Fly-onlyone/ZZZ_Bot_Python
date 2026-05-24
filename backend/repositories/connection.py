"""SQLite connection manager for ZZZ Bot.

A single shared sqlite3.Connection backs all repository access. The backend is
multi-threaded (uvicorn request workers + the schedule loop + the
deferred-startup thread), so the connection is opened with
``check_same_thread=False`` and every DataStore function serializes its work
through ``get_lock()``.
"""

import logging
import os
import sqlite3
import sys
import threading

logger = logging.getLogger(__name__)

# Dev and exe modes use different filenames so dev data never overwrites the
# packaged database.
DEFAULT_DB_NAME_DEV = "zzz_bot_dev.db"
DEFAULT_DB_NAME_EXE = "zzz_bot.db"

_connection: sqlite3.Connection | None = None
_lock = threading.RLock()


def get_runtime_mode() -> str:
    """Return current runtime mode: 'dev' or 'exe'."""
    if os.getenv("SIMULATE_EXE", "0") == "1":
        return "exe"
    if getattr(sys, "frozen", False):
        return "exe"
    return "dev"


def _db_filename() -> str:
    """Choose the SQLite filename based on runtime mode."""
    return DEFAULT_DB_NAME_EXE if get_runtime_mode() == "exe" else DEFAULT_DB_NAME_DEV


def get_db_path() -> str:
    """Resolve the SQLite file path.

    Stored under ``data/`` with ``outside_path=True`` so the database persists
    across app updates (next to the exe in packaged mode).
    """
    # Lazy import avoids a circular import (GlobalVar -> DataStore -> connection).
    from core.GlobalVar import resource_path

    return resource_path(os.path.join("data", _db_filename()), outside_path=True)


def get_lock() -> threading.RLock:
    """Return the lock that serializes all DataStore reads and writes."""
    return _lock


def get_connection() -> sqlite3.Connection:
    """Get or lazily open the shared SQLite connection."""
    global _connection
    if _connection is not None:
        return _connection

    with _lock:
        if _connection is not None:
            return _connection

        db_path = get_db_path()
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # WAL keeps reads and writes from blocking each other; NORMAL is the
        # recommended durability level under WAL; busy_timeout is a safety net.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        _connection = conn
        logger.info("Opened SQLite database at %s", db_path)

    return _connection


def reset_connection() -> None:
    """Close and reset the cached SQLite connection."""
    global _connection

    with _lock:
        if _connection is not None:
            try:
                _connection.close()
            except Exception as exc:
                logger.debug("Ignoring SQLite close error: %s", exc)
        _connection = None


def get_connection_debug_info() -> dict[str, object]:
    """Return non-sensitive storage metadata for diagnostics."""
    db_path = get_db_path()
    return {
        "runtime_mode": get_runtime_mode(),
        "storage": "sqlite",
        "db_path": db_path,
        "db_exists": os.path.exists(db_path),
    }
