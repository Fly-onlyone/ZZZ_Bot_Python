"""Centralized locator tracking with summary rows and rolling failure history."""

from __future__ import annotations

import hashlib
import logging
import time
from contextlib import suppress
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from playwright.sync_api import Locator, Page

import repositories.MongoRepository as MongoRepository
from utils.screenshot_store import (
    save_locator_screenshot,
    save_page_screenshot,
    save_screenshot_bytes,
)

logger = logging.getLogger(__name__)

_screenshot_cache: dict[str, float] = {}
_SCREENSHOT_THROTTLE_SECONDS = 3600


def _selector_hash(selector: str) -> str:
    return hashlib.md5(selector.encode("utf-8")).hexdigest()[:12]


def _summary_id(handler: str, action: str, selector_hash: str) -> str:
    return f"locator:{handler}:{action}:{selector_hash}"


def _asset_metadata(
    *,
    kind: str,
    handler: str,
    action: str,
    selector_hash: str,
    summary_id: str,
) -> dict[str, str]:
    return {
        "owner": MongoRepository.LOCATOR_TRACKER_ASSET_OWNER,
        "kind": kind,
        "handler": handler,
        "action": action,
        "selector_hash": selector_hash,
        "summary_id": summary_id,
    }


def _should_capture(summary_id: str, success: bool) -> bool:
    if not success:
        return True

    last_capture = _screenshot_cache.get(summary_id, 0)
    return time.time() - last_capture >= _SCREENSHOT_THROTTLE_SECONDS


def _capture_artifacts(
    page: Page,
    selector_hash: str,
    summary_id: str,
    handler: str,
    action: str,
    success: bool,
    locator: Optional[Locator],
) -> dict[str, str | None]:
    page_asset_id = None
    locator_asset_id = None
    dom_snapshot_asset_id = None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    page_metadata = _asset_metadata(
        kind="page_screenshot",
        handler=handler,
        action=action,
        selector_hash=selector_hash,
        summary_id=summary_id,
    )
    try:
        page_asset_id = save_page_screenshot(
            page,
            f"locator_{selector_hash}_{timestamp}.png",
            full_page=True,
            metadata=page_metadata,
        )
        _screenshot_cache[summary_id] = time.time()
    except Exception as exc:
        logger.debug("Locator tracker page screenshot failed: %s", exc)

    if locator is not None:
        try:
            if locator.count() > 0 and locator.first.is_visible(timeout=500):
                locator_asset_id = save_locator_screenshot(
                    locator.first,
                    f"locator_el_{selector_hash}_{timestamp}.png",
                    metadata=_asset_metadata(
                        kind="locator_screenshot",
                        handler=handler,
                        action=action,
                        selector_hash=selector_hash,
                        summary_id=summary_id,
                    ),
                )
        except Exception as exc:
            logger.debug("Locator tracker element screenshot failed: %s", exc)

    if not success:
        try:
            dom_snapshot_asset_id = save_screenshot_bytes(
                f"locator_dom_{selector_hash}_{timestamp}.html",
                page.content().encode("utf-8"),
                metadata=_asset_metadata(
                    kind="dom_snapshot",
                    handler=handler,
                    action=action,
                    selector_hash=selector_hash,
                    summary_id=summary_id,
                ),
                content_type="text/html; charset=utf-8",
            )
        except Exception as exc:
            logger.debug("Locator tracker DOM snapshot failed: %s", exc)

    return {
        "page_asset_id": page_asset_id,
        "locator_asset_id": locator_asset_id,
        "dom_snapshot_asset_id": dom_snapshot_asset_id,
    }


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
    """Record a locator interaction without interrupting the automation flow."""
    selector_hash = _selector_hash(selector)
    summary_id = _summary_id(handler, action, selector_hash)
    now = datetime.now(tz=timezone.utc)

    existing = None
    with suppress(Exception):
        existing = MongoRepository.get_db().locator_tracker.find_one(
            {"_id": summary_id}
        )

    hit_count = (existing.get("hit_count", 0) if existing else 0) + 1
    success_count = (existing.get("success_count", 0) if existing else 0) + (
        1 if success else 0
    )
    failure_count = (existing.get("failure_count", 0) if existing else 0) + (
        0 if success else 1
    )
    first_seen = existing.get("first_seen", now) if existing else now

    page_asset_id = existing.get("page_asset_id") if existing else None
    locator_asset_id = existing.get("locator_asset_id") if existing else None
    dom_snapshot_asset_id = existing.get("dom_snapshot_asset_id") if existing else None
    current_page_asset_id = None
    current_locator_asset_id = None
    current_dom_snapshot_asset_id = None

    if _should_capture(summary_id, success):
        artifacts = _capture_artifacts(
            page,
            selector_hash,
            summary_id,
            handler,
            action,
            success,
            locator,
        )
        current_page_asset_id = artifacts["page_asset_id"]
        current_locator_asset_id = artifacts["locator_asset_id"]
        current_dom_snapshot_asset_id = artifacts["dom_snapshot_asset_id"]
        page_asset_id = current_page_asset_id or page_asset_id
        locator_asset_id = current_locator_asset_id or locator_asset_id
        dom_snapshot_asset_id = (
            current_dom_snapshot_asset_id if not success else dom_snapshot_asset_id
        )

    entry = {
        "_id": summary_id,
        "selector": selector,
        "selector_hash": selector_hash,
        "handler": handler,
        "action": action,
        "last_success": success,
        "last_error": error_message,
        "hit_count": hit_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "page_asset_id": page_asset_id,
        "locator_asset_id": locator_asset_id,
        "dom_snapshot_asset_id": dom_snapshot_asset_id if not success else None,
        "first_seen": first_seen,
        "last_seen": now,
    }

    with suppress(Exception):
        MongoRepository.upsert_locator_entry(entry)

    if not success:
        failure_entry = {
            "_id": f"locator-failure:{uuid4()}",
            "summary_id": summary_id,
            "selector": selector,
            "selector_hash": selector_hash,
            "handler": handler,
            "action": action,
            "error_message": error_message,
            "seen_at": now,
            "page_asset_id": current_page_asset_id,
            "locator_asset_id": current_locator_asset_id,
            "dom_snapshot_asset_id": current_dom_snapshot_asset_id,
        }
        with suppress(Exception):
            MongoRepository.save_locator_failure_event(failure_entry)


def get_all_entries() -> list[dict]:
    """Return all tracked locator summary entries."""
    return MongoRepository.get_locator_entries()


def get_failure_events(limit: int = 100, summary_id: str | None = None) -> list[dict]:
    """Return recent locator tracker failure events."""
    return MongoRepository.get_locator_failure_events(
        limit=limit, summary_id=summary_id
    )


def clear_entries() -> None:
    """Remove all tracked locator entries and reset capture throttling."""
    _screenshot_cache.clear()
    MongoRepository.clear_locator_entries()
