"""MongoDB-backed screenshot storage for runtime captures."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson.binary import Binary

from repositories.connection import get_db

logger = logging.getLogger(__name__)

SCREENSHOT_CATEGORY = "screenshot"


def _asset_id(filename: str) -> str:
    return f"{SCREENSHOT_CATEGORY}:{filename}"


def save_screenshot_bytes(
    filename: str,
    payload: bytes,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Save screenshot bytes to MongoDB and return the stored asset id."""
    safe_name = Path(filename).name
    if not safe_name:
        raise ValueError("filename must not be empty")

    get_db().binary_assets.find_one_and_replace(
        {"_id": _asset_id(safe_name)},
        {
            "_id": _asset_id(safe_name),
            "category": SCREENSHOT_CATEGORY,
            "source_path": safe_name,
            "content_type": "image/png",
            "size_bytes": len(payload),
            "payload": Binary(payload),
            "metadata": metadata or {},
            "updated_at": datetime.now(tz=timezone.utc),
        },
        upsert=True,
    )
    logger.debug("Stored screenshot in MongoDB: %s (%d bytes)", safe_name, len(payload))
    return _asset_id(safe_name)


def save_page_screenshot(page, filename: str, full_page: bool = False) -> str:
    """Capture a Playwright page screenshot to MongoDB."""
    payload = page.screenshot(full_page=full_page)
    return save_screenshot_bytes(
        filename,
        payload,
        metadata={"full_page": full_page},
    )


def save_locator_screenshot(locator, filename: str) -> str:
    """Capture a Playwright locator screenshot to MongoDB."""
    payload = locator.screenshot()
    return save_screenshot_bytes(filename, payload)


def get_screenshot_bytes(filename: str) -> bytes | None:
    """Load screenshot bytes from MongoDB by filename."""
    safe_name = Path(filename).name
    if not safe_name:
        return None

    doc = get_db().binary_assets.find_one(
        {"_id": _asset_id(safe_name)},
        {"payload": 1},
    )
    if not doc or "payload" not in doc:
        return None
    return bytes(doc["payload"])

