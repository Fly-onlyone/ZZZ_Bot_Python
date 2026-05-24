"""SQLite-backed Playwright storage state utilities."""

import json
import logging
import os
from pathlib import Path

from repositories import DataStore

logger = logging.getLogger(__name__)

_STORAGE_STATE_CATEGORY = "storage_state"


def _storage_asset_id(storage_path: str) -> str:
    filename = Path(storage_path).name or "hoyo.json"
    return f"{_STORAGE_STATE_CATEGORY}:{filename}"


def load_storage_state(storage_path: str) -> dict | None:
    """Load Playwright storage state from the database, file fallback handled by caller."""
    import sentry_sdk

    with sentry_sdk.start_span(op="auth.storage_state", name="load_storage_state"):
        asset = DataStore.get_binary_asset(_storage_asset_id(storage_path))

        if asset is None:
            # Fallback to the latest storage_state asset when the filename changed.
            asset = DataStore.get_latest_binary_asset(_STORAGE_STATE_CATEGORY)

        if asset is None:
            return None

        try:
            data = json.loads(bytes(asset["payload"]).decode("utf-8"))
        except Exception as exc:
            logger.warning("Failed to parse stored storage state payload: %s", exc)
            return None

        if isinstance(data, dict):
            return data

        logger.warning("Invalid storage state payload type: %s", type(data).__name__)
        return None


def build_context_options(storage_path: str) -> dict:
    """Build Playwright new_context options using the stored storage state first."""
    state_from_db = load_storage_state(storage_path)
    if state_from_db is not None:
        logger.info("Loading authentication state from the database")
        return {"storage_state": state_from_db}

    if storage_path and os.path.exists(storage_path):
        logger.info("Loading authentication state from file fallback: %s", storage_path)
        return {"storage_state": storage_path}

    logger.info("No authentication state found in the database or local file")
    return {}


def save_storage_state(
    storage_path: str,
    storage_state: dict,
    write_local_backup: bool = True,
) -> None:
    """Persist Playwright storage state to the database and an optional local file."""
    payload_bytes = json.dumps(storage_state, ensure_ascii=False).encode("utf-8")
    filename = Path(storage_path).name or "hoyo.json"

    DataStore.upsert_binary_asset(
        _storage_asset_id(storage_path),
        category=_STORAGE_STATE_CATEGORY,
        source_path=storage_path,
        content_type="application/json",
        size_bytes=len(payload_bytes),
        payload=payload_bytes,
        metadata={"filename": filename},
    )

    if write_local_backup:
        storage_parent = os.path.dirname(storage_path)
        if storage_parent:
            os.makedirs(storage_parent, exist_ok=True)
        with open(storage_path, "w", encoding="utf-8") as file:
            json.dump(storage_state, file, ensure_ascii=False)


def save_context_storage_state(context, storage_path: str, write_local_backup: bool = True) -> None:
    """Capture the current Playwright context storage state and persist it."""
    import sentry_sdk

    with sentry_sdk.start_span(op="auth.storage_state", name="save_storage_state"):
        storage_state = context.storage_state()
        if not isinstance(storage_state, dict):
            raise ValueError("Playwright storage_state() returned non-dict payload")
        save_storage_state(storage_path, storage_state, write_local_backup=write_local_backup)
