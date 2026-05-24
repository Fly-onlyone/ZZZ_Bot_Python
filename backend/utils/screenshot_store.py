"""SQLite-backed screenshot storage for runtime captures."""

import logging
from pathlib import Path
from typing import Any, Optional

from repositories import DataStore

logger = logging.getLogger(__name__)

SCREENSHOT_CATEGORY = "screenshot"


def _asset_id(filename: str) -> str:
    return f"{SCREENSHOT_CATEGORY}:{filename}"


def save_screenshot_bytes(
    filename: str,
    payload: bytes,
    metadata: dict[str, Any] | None = None,
    *,
    content_type: str = "image/png",
) -> str:
    """Save binary bytes to the database and return the stored asset id."""
    safe_name = Path(filename).name
    if not safe_name:
        raise ValueError("filename must not be empty")

    asset_id = _asset_id(safe_name)
    DataStore.upsert_binary_asset(
        asset_id,
        category=SCREENSHOT_CATEGORY,
        source_path=safe_name,
        content_type=content_type,
        size_bytes=len(payload),
        payload=payload,
        metadata=metadata or {},
    )
    logger.debug("Stored screenshot: %s (%d bytes)", safe_name, len(payload))
    return asset_id


def save_page_screenshot(
    page,
    filename: str,
    full_page: bool = False,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Capture a Playwright page screenshot to the database."""
    payload = page.screenshot(full_page=full_page)
    return save_screenshot_bytes(
        filename,
        payload,
        metadata={**(metadata or {}), "full_page": full_page},
    )


def save_locator_screenshot(
    locator,
    filename: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Capture a Playwright locator screenshot to the database."""
    payload = locator.screenshot()
    return save_screenshot_bytes(filename, payload, metadata=metadata)


def get_screenshot_bytes(filename: str) -> bytes | None:
    """Load screenshot bytes from the database by filename."""
    asset = get_screenshot_asset(filename)
    if asset is None:
        return None
    return asset["payload"]


def get_screenshot_asset(filename: str) -> Optional[dict[str, Any]]:
    """Load binary asset payload and metadata from the database by filename."""
    safe_name = Path(filename).name
    if not safe_name:
        return None

    asset = DataStore.get_binary_asset(_asset_id(safe_name))
    if asset is None:
        return None
    return {
        "payload": asset["payload"],
        "content_type": asset.get("content_type") or "application/octet-stream",
        "metadata": asset.get("metadata") or {},
        "source_path": asset.get("source_path") or safe_name,
    }
