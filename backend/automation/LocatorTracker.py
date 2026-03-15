"""Centralized locator tracking — captures debug artifacts on every locator interaction."""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from playwright.sync_api import Locator, Page

import repositories.MongoRepository as MongoRepository
from utils.screenshot_store import (
    save_locator_screenshot,
    save_page_screenshot,
    save_screenshot_bytes,
)

logger = logging.getLogger(__name__)

# Module-level throttle cache: selector_hash -> last_screenshot_epoch
_screenshot_cache: dict[str, float] = {}
_SCREENSHOT_THROTTLE_SECONDS = 3600  # 1 hour


def _selector_hash(selector: str) -> str:
    return hashlib.md5(selector.encode()).hexdigest()[:12]


def _extract_selector(locator: Locator) -> str:
    """Parse the CSS selector from a Playwright Locator's string representation."""
    try:
        text = str(locator)
        # Playwright Python: Locator@<selector>
        if "@" in text:
            return text.split("@", 1)[1].strip()
    except Exception:
        pass
    return "unknown"


def track_locator(
    page: Page,
    selector: str,
    handler: str,
    action: str,
    success: bool,
    *,
    error_message: Optional[str] = None,
    locator: Optional[Locator] = None,
) -> None:
    """Record a locator interaction with optional screenshot capture.

    Args:
        page: Playwright Page instance (used for full-page screenshots)
        selector: CSS selector string
        handler: Handler or module name
        action: Interaction type (visibility_check, click, wait_for, count, inner_text)
        success: Whether the interaction succeeded
        error_message: Optional error detail on failure
        locator: Optional Locator for element-level screenshot capture
    """
    sel_hash = _selector_hash(selector)
    doc_id = f"locator:{sel_hash}"
    now = datetime.now(tz=timezone.utc)

    # Fetch existing document for incremental counters
    try:
        existing = MongoRepository.get_db().locator_tracker.find_one({"_id": doc_id})
    except Exception:
        existing = None

    hit_count = (existing.get("hit_count", 0) if existing else 0) + 1
    success_count = (existing.get("success_count", 0) if existing else 0) + (
        1 if success else 0
    )
    failure_count = (existing.get("failure_count", 0) if existing else 0) + (
        0 if success else 1
    )
    first_seen = existing.get("first_seen", now) if existing else now

    # Determine whether to capture a screenshot
    screenshot_asset_id = existing.get("screenshot_asset_id") if existing else None
    locator_screenshot_asset_id = (
        existing.get("locator_screenshot_asset_id") if existing else None
    )
    dom_snapshot_asset_id = existing.get("dom_snapshot_asset_id") if existing else None
    should_capture = False

    if not success:
        # Always capture on failure
        should_capture = True
    else:
        # On success, throttle to once per hour per selector
        last_capture = _screenshot_cache.get(sel_hash, 0)
        if time.time() - last_capture >= _SCREENSHOT_THROTTLE_SECONDS:
            should_capture = True

    if should_capture:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            filename = f"locator_{sel_hash}_{ts}.png"
            screenshot_asset_id = save_page_screenshot(page, filename)
            _screenshot_cache[sel_hash] = time.time()
        except Exception as exc:
            logger.debug("Locator tracker page screenshot failed: %s", exc)

        # Capture element-level screenshot when locator is provided and visible
        if locator is not None:
            try:
                if locator.count() > 0 and locator.first.is_visible(timeout=500):
                    el_filename = f"locator_el_{sel_hash}_{ts}.png"
                    locator_screenshot_asset_id = save_locator_screenshot(
                        locator.first, el_filename
                    )
            except Exception as exc:
                logger.debug("Locator tracker element screenshot failed: %s", exc)

        if not success:
            try:
                dom_html = page.content().encode("utf-8")
                dom_filename = f"locator_dom_{sel_hash}_{ts}.html"
                dom_snapshot_asset_id = save_screenshot_bytes(
                    dom_filename, dom_html, metadata={"type": "dom_snapshot"}
                )
            except Exception as exc:
                logger.debug("Locator tracker DOM snapshot failed: %s", exc)

    entry = {
        "_id": doc_id,
        "selector": selector,
        "handler": handler,
        "last_action": action,
        "last_success": success,
        "last_error": error_message,
        "hit_count": hit_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "screenshot_asset_id": screenshot_asset_id,
        "locator_screenshot_asset_id": locator_screenshot_asset_id,
        "dom_snapshot_asset_id": dom_snapshot_asset_id if not success else None,
        "first_seen": first_seen,
        "last_seen": now,
    }

    try:
        MongoRepository.upsert_locator_entry(entry)
    except Exception as exc:
        logger.debug("Locator tracker upsert failed: %s", exc)


def get_all_entries() -> list[dict]:
    """Return all tracked locator entries."""
    return MongoRepository.get_locator_entries()


def clear_entries() -> None:
    """Remove all tracked locator entries and reset screenshot cache."""
    _screenshot_cache.clear()
    MongoRepository.clear_locator_entries()
