"""MongoDB connection factory for ZZZ Bot."""

import logging
import os
import sys
from urllib.parse import urlsplit, urlunsplit

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConfigurationError

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_NAME_DEV = "zzz_bot_dev"
DEFAULT_DATABASE_NAME_EXE = "zzz_bot"
DEFAULT_MONGODB_URI_DEV = f"mongodb://localhost:27017/{DEFAULT_DATABASE_NAME_DEV}"
DEFAULT_MONGODB_URI_EXE = f"mongodb://localhost:27017/{DEFAULT_DATABASE_NAME_EXE}"

_client: MongoClient | None = None
_db: Database | None = None
_runtime_uri_override: str | None = None


def _normalize_uri(uri: str | None) -> str | None:
    """Normalize URI values so empty strings behave as unset."""
    if uri is None:
        return None
    normalized = uri.strip()
    return normalized or None


def get_runtime_mode() -> str:
    """Return current runtime mode: 'dev' or 'exe'."""
    if os.getenv("SIMULATE_EXE", "0") == "1":
        return "exe"
    if getattr(sys, "frozen", False):
        return "exe"
    return "dev"


def _default_database_name() -> str:
    """Choose default database name based on runtime mode."""
    if get_runtime_mode() == "exe":
        return DEFAULT_DATABASE_NAME_EXE
    return DEFAULT_DATABASE_NAME_DEV


def _default_mongodb_uri() -> str:
    """Choose default MongoDB URI based on runtime mode."""
    if get_runtime_mode() == "exe":
        return DEFAULT_MONGODB_URI_EXE
    return DEFAULT_MONGODB_URI_DEV


def _mode_uri_env_var() -> str:
    """Return mode-specific MongoDB URI env var name."""
    return "MONGODB_URI_EXE" if get_runtime_mode() == "exe" else "MONGODB_URI_DEV"


def _masked_uri(uri: str) -> str:
    """Mask credentials in URI while preserving host and database path."""
    parsed = urlsplit(uri)
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))


def get_uri_source() -> str:
    """Describe which source currently provides the MongoDB URI."""
    if _normalize_uri(_runtime_uri_override):
        return "settings.mongodb_uri"
    mode_env_var = _mode_uri_env_var()
    if _normalize_uri(os.getenv(mode_env_var)):
        return f"env:{mode_env_var}"
    if _normalize_uri(os.getenv("MONGODB_URI")):
        return "env:MONGODB_URI"
    return f"default:{get_runtime_mode()}"


def get_effective_mongodb_uri() -> str:
    """Resolve MongoDB URI from runtime override, env var, then default."""
    uri = _normalize_uri(_runtime_uri_override)
    if uri:
        return uri

    mode_env_var = _mode_uri_env_var()
    mode_uri = _normalize_uri(os.getenv(mode_env_var))
    if mode_uri:
        return mode_uri

    env_uri = _normalize_uri(os.getenv("MONGODB_URI"))
    if env_uri:
        return env_uri

    return _default_mongodb_uri()


def get_connection_debug_info() -> dict[str, str | None]:
    """Return non-sensitive Mongo connection metadata for diagnostics."""
    uri = get_effective_mongodb_uri()
    return {
        "runtime_mode": get_runtime_mode(),
        "uri_source": get_uri_source(),
        "uri_masked": _masked_uri(uri),
        "db_name": _db.name if _db is not None else None,
    }


def _select_database(client: MongoClient) -> Database:
    """Select default DB from URI, or fallback to project default DB name."""
    try:
        return client.get_default_database()
    except ConfigurationError:
        return client[_default_database_name()]


def reset_connection() -> None:
    """Close and reset cached MongoDB client/database."""
    global _client, _db

    if _client is not None:
        try:
            _client.close()
        except Exception as exc:
            logger.debug("Ignoring MongoDB close error: %s", exc)

    _client = None
    _db = None


def set_runtime_uri(uri: str | None) -> None:
    """Set runtime URI override and force reconnection on next access."""
    global _runtime_uri_override

    normalized = _normalize_uri(uri)
    if normalized == _runtime_uri_override:
        return

    _runtime_uri_override = normalized
    reset_connection()


def get_db() -> Database:
    """Get or lazily create the MongoDB database connection."""
    global _client, _db
    if _db is not None:
        return _db

    uri = get_effective_mongodb_uri()
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")  # Verify reachability
        _db = _select_database(_client)
        logger.info("Connected to MongoDB")
    except Exception as exc:
        logger.error("MongoDB connection failed: %s", exc)
        reset_connection()
        raise

    return _db
