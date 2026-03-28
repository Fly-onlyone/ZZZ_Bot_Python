"""Shared panel navigation helpers for the HoYoLab event UI."""

from __future__ import annotations

import logging
from contextlib import suppress
from dataclasses import dataclass
from typing import Callable, Iterable

from playwright.sync_api import Error as PlaywrightError, Locator, Page

from .Selectors import MISSION_DIALOG_CLOSE, SHOPPING_CLOSE_BUTTON
from .tracking import safe_track_locator
from core.constants import (
    DEFAULT_EVENT_URL,
    EVENT_PAGE_GOTO_MAX_ATTEMPTS,
    EVENT_PAGE_GOTO_RETRY_WAIT_MS,
    EVENT_PAGE_GOTO_TIMEOUT,
    EVENT_PAGE_WAIT_UNTIL,
    PANEL_BACK_SELECTOR,
)
from utils.screenshot_store import save_page_screenshot

logger = logging.getLogger(__name__)

DEFAULT_LAUNCH_TIMEOUT = 5000
DEFAULT_PANEL_CLOSE_TIMEOUT = 2000
DEFAULT_RESET_ATTEMPTS = 3
DEFAULT_RETRY_WAIT_MS = 1000

LauncherCandidate = tuple[str, Callable[[], Locator]]


@dataclass
class PanelOpenResult:
    """Outcome for a shared panel open attempt."""

    opened: bool
    candidate_name: str | None = None
    last_error: Exception | None = None


def is_locator_visible(locator: Locator, timeout: int = 1000) -> bool:
    """Return whether the first matching locator is visible without raising."""
    with suppress(Exception):
        result = locator.count() > 0 and locator.first.is_visible(timeout=timeout)
        safe_track_locator(locator, "EventNavigator", "visibility_check", result)
        return result
    safe_track_locator(locator, "EventNavigator", "visibility_check", False)
    return False


def close_reward_dialog(
    page: Page,
    *,
    context: str,
    timeout: int = DEFAULT_PANEL_CLOSE_TIMEOUT,
) -> bool:
    """Close a lingering reward modal if it is blocking panel navigation."""
    close_button = page.locator(SHOPPING_CLOSE_BUTTON).first
    if not is_locator_visible(close_button):
        return False

    logger.info("Closing reward dialog while %s", context)
    try:
        close_button.click(force=True, timeout=timeout)
        page.wait_for_timeout(500)
        return True
    except Exception as exc:
        logger.warning("Reward dialog close failed while %s: %s", context, exc)
        return False


def close_mission_dialog(
    page: Page,
    *,
    context: str,
    timeout: int = DEFAULT_PANEL_CLOSE_TIMEOUT,
) -> bool:
    """Close the mission popup dialog if it is still visible."""
    close_button = page.locator(MISSION_DIALOG_CLOSE).first
    if not is_locator_visible(close_button):
        return False

    logger.info("Closing mission dialog while %s", context)
    try:
        close_button.click(force=True, timeout=timeout)
        page.wait_for_timeout(500)
        return True
    except Exception as exc:
        logger.warning("Mission dialog close failed while %s: %s", context, exc)
        return False


def close_panel_back(
    page: Page,
    *,
    context: str,
    timeout: int = DEFAULT_PANEL_CLOSE_TIMEOUT,
) -> bool:
    """Click the shared panel back button when it is visible."""
    panel_back = page.locator(PANEL_BACK_SELECTOR).first
    if not is_locator_visible(panel_back):
        return False

    logger.info("Closing open panel while %s", context)
    for force_click in (False, True):
        try:
            page.locator(PANEL_BACK_SELECTOR).first.click(
                force=force_click,
                timeout=timeout,
            )
            page.wait_for_timeout(500)
            with suppress(Exception):
                page.wait_for_load_state("domcontentloaded", timeout=2000)
            return True
        except Exception as exc:
            if not force_click:
                logger.warning(
                    "Panel back click failed while %s (%s), retrying with force",
                    context,
                    exc,
                )

    logger.warning("Skipping panel close after click race while %s", context)
    return False


def has_blocking_ui(page: Page) -> bool:
    """Return whether known blocking overlays or panel chrome remain visible."""
    return any(
        (
            is_locator_visible(page.locator(SHOPPING_CLOSE_BUTTON).first),
            is_locator_visible(page.locator(MISSION_DIALOG_CLOSE).first),
            is_locator_visible(page.locator(PANEL_BACK_SELECTOR).first),
        )
    )


def ensure_event_home(
    page: Page,
    *,
    context: str,
    attempts: int = DEFAULT_RESET_ATTEMPTS,
) -> bool:
    """Clear known blocking UI so panel launchers are reachable again."""
    for _ in range(attempts):
        changed = False
        changed = close_reward_dialog(page, context=context) or changed
        changed = close_mission_dialog(page, context=context) or changed
        changed = close_panel_back(page, context=context) or changed
        if not changed:
            return not has_blocking_ui(page)
    return not has_blocking_ui(page)


def open_panel(
    page: Page,
    *,
    panel_name: str,
    ready_predicate: Callable[[], bool],
    candidates: Iterable[LauncherCandidate],
    max_attempts: int,
    retry_wait_ms: int = DEFAULT_RETRY_WAIT_MS,
    launch_timeout: int = DEFAULT_LAUNCH_TIMEOUT,
) -> PanelOpenResult:
    """Open a panel from event home using ordered launcher candidates."""
    last_error = None

    if ready_predicate():
        return PanelOpenResult(opened=True, candidate_name="already-open")

    for attempt in range(1, max_attempts + 1):
        ensure_event_home(page, context=f"opening {panel_name}")

        for candidate_name, locator_builder in candidates:
            try:
                launcher = locator_builder().first
                if not is_locator_visible(launcher):
                    continue

                launcher.click(force=True, timeout=launch_timeout)
                page.wait_for_timeout(retry_wait_ms)

                if ready_predicate():
                    return PanelOpenResult(True, candidate_name, last_error)

                with suppress(Exception):
                    page.wait_for_load_state("domcontentloaded", timeout=3000)

                if ready_predicate():
                    return PanelOpenResult(True, candidate_name, last_error)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "%s launcher click failed on attempt %s/%s via %s: %s",
                    panel_name,
                    attempt,
                    max_attempts,
                    candidate_name,
                    exc,
                )

    return PanelOpenResult(False, None, last_error)


def open_event_page(
    page: Page,
    *,
    url: str = DEFAULT_EVENT_URL,
    timeout: int = EVENT_PAGE_GOTO_TIMEOUT,
    max_attempts: int = EVENT_PAGE_GOTO_MAX_ATTEMPTS,
    retry_wait_ms: int = EVENT_PAGE_GOTO_RETRY_WAIT_MS,
    wait_until: str = EVENT_PAGE_WAIT_UNTIL,
) -> None:
    """Open the HoYoLab event page with bounded retries and diagnostics."""
    import sentry_sdk

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                "Opening HoYoLab event page (attempt %s/%s, wait_until=%s, timeout=%sms)",
                attempt,
                max_attempts,
                wait_until,
                timeout,
            )
            page.goto(url, wait_until=wait_until, timeout=timeout)
            return
        except PlaywrightError as exc:
            last_error = exc
            logger.warning(
                "HoYoLab event page navigation failed on attempt %s/%s: %s",
                attempt,
                max_attempts,
                exc,
            )
            if attempt < max_attempts:
                page.wait_for_timeout(retry_wait_ms)

    screenshot_name = f"event_page_navigation_failure_{max_attempts}attempts.png"
    screenshot_asset_id = save_page_screenshot(page, screenshot_name)
    logger.error(
        "Failed to open HoYoLab event page after %s attempts; screenshot_asset_id=%s",
        max_attempts,
        screenshot_asset_id,
    )

    with sentry_sdk.isolation_scope():
        sentry_sdk.set_tag("event_page.issue", "navigation_failed")
        sentry_sdk.set_tag("event_page.attempts", str(max_attempts))
        sentry_sdk.set_context(
            "event_page_navigation",
            {
                "url": url,
                "wait_until": wait_until,
                "timeout_ms": timeout,
                "max_attempts": max_attempts,
                "retry_wait_ms": retry_wait_ms,
                "screenshot_asset_id": screenshot_asset_id,
                "last_error": str(last_error) if last_error is not None else None,
            },
        )
        sentry_sdk.capture_exception(last_error)

    if last_error is not None:
        raise last_error

    raise RuntimeError("Failed to open HoYoLab event page")
