"""Mongo-first Playwright storage state utilities."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from bson.binary import Binary
from pymongo import DESCENDING

from repositories.connection import get_db

logger = logging.getLogger(__name__)

_STORAGE_STATE_CATEGORY = "storage_state"


def _storage_asset_id(storage_path: str) -> str:
    filename = Path(storage_path).name or "hoyo.json"
    return f"{_STORAGE_STATE_CATEGORY}:{filename}"


def load_storage_state(storage_path: str) -> dict | None:
    """Load Playwright storage state from MongoDB, with file fallback handled by caller."""
    import sentry_sdk
    with sentry_sdk.start_span(op="auth.storage_state", name="load_storage_state"):
        collection = get_db().binary_assets
        asset_id = _storage_asset_id(storage_path)
        doc = collection.find_one({"_id": asset_id}, {"payload": 1})

        if not doc:
            # Fallback to latest storage_state asset when filename/key changed.
            doc = collection.find_one(
                {"category": _STORAGE_STATE_CATEGORY},
                {"payload": 1},
                sort=[("updated_at", DESCENDING)],
            )

        if not doc or "payload" not in doc:
            return None

        try:
            payload = bytes(doc["payload"]).decode("utf-8")
            data = json.loads(payload)
        except Exception as exc:
            logger.warning("Failed to parse Mongo storage state payload: %s", exc)
            return None

        if isinstance(data, dict):
            return data

        logger.warning("Invalid Mongo storage state payload type: %s", type(data).__name__)
        return None


def build_context_options(storage_path: str) -> dict:
    """Build Playwright new_context options using Mongo storage state first."""
    state_from_db = load_storage_state(storage_path)
    if state_from_db is not None:
        logger.info("Loading authentication state from MongoDB")
        return {"storage_state": state_from_db}

    if storage_path and os.path.exists(storage_path):
        logger.info("Loading authentication state from file fallback: %s", storage_path)
        return {"storage_state": storage_path}

    logger.info("No authentication state found in MongoDB or local file")
    return {}


def save_storage_state(
    storage_path: str,
    storage_state: dict,
    write_local_backup: bool = True,
) -> None:
    """Persist Playwright storage state to MongoDB and optional local backup file."""
    payload_bytes = json.dumps(storage_state, ensure_ascii=False).encode("utf-8")
    filename = Path(storage_path).name or "hoyo.json"

    get_db().binary_assets.find_one_and_replace(
        {"_id": _storage_asset_id(storage_path)},
        {
            "_id": _storage_asset_id(storage_path),
            "category": _STORAGE_STATE_CATEGORY,
            "source_path": storage_path,
            "content_type": "application/json",
            "size_bytes": len(payload_bytes),
            "payload": Binary(payload_bytes),
            "metadata": {"filename": filename},
            "updated_at": datetime.now(tz=timezone.utc),
        },
        upsert=True,
    )

    if write_local_backup:
        storage_parent = os.path.dirname(storage_path)
        if storage_parent:
            os.makedirs(storage_parent, exist_ok=True)
        with open(storage_path, "w", encoding="utf-8") as file:
            json.dump(storage_state, file, ensure_ascii=False)


def save_context_storage_state(context, storage_path: str, write_local_backup: bool = True) -> None:
    """Capture current Playwright context storage state and persist it to MongoDB."""
    import sentry_sdk
    with sentry_sdk.start_span(op="auth.storage_state", name="save_storage_state"):
        storage_state = context.storage_state()
        if not isinstance(storage_state, dict):
            raise ValueError("Playwright storage_state() returned non-dict payload")
        save_storage_state(storage_path, storage_state, write_local_backup=write_local_backup)
