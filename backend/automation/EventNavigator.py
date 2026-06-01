"""Shared panel navigation helpers for the HoYoLab event UI."""

from __future__ import annotations

import logging
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable

from core.constants import (
    DEFAULT_EVENT_URL,
    EVENT_PAGE_GOTO_MAX_ATTEMPTS,
    EVENT_PAGE_GOTO_RETRY_WAIT_MS,
    EVENT_PAGE_GOTO_TIMEOUT,
    EVENT_PAGE_WAIT_UNTIL,
    PANEL_BACK_SELECTOR,
)
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page
from utils.screenshot_store import save_page_screenshot

from .Selectors import MISSION_DIALOG_CLOSE, SHOPPING_CLOSE_BUTTON
from .tracking import safe_track_locator

logger = logging.getLogger(__name__)

DEFAULT_LAUNCH_TIMEOUT = 5000
DEFAULT_PANEL_CLOSE_TIMEOUT = 2000
DEFAULT_RESET_ATTEMPTS = 3
DEFAULT_RETRY_WAIT_MS = 1000
EVENT_PAGE_AUTH_TIMEOUT_MS = 10000
EVENT_PAGE_AUTH_POLL_INTERVAL_MS = 500
EVENT_PAGE_LOGIN_TEXT = "Log In"
EVENT_PAGE_MISSION_HINT_TEXT = "Carry out missions to earn"
EVENT_PAGE_LOGIN_FRAME_SELECTOR = "#hyv-account-frame"
EVENT_PAGE_AUTH_SCREENSHOT_PREFIX = "event_page_auth_required_"

# Domains and cookie names that prove an active HoYoLab login. The browser drops
# expired cookies, so presence of a full pair implies an unexpired session.
HOYOLAB_AUTH_COOKIE_DOMAINS = ("hoyolab.com", "hoyoverse.com")
HOYOLAB_AUTH_COOKIE_PAIRS = (
    ("ltoken_v2", "ltuid_v2"),
    ("cookie_token_v2", "account_id_v2"),
)

LauncherCandidate = tuple[str, Callable[[], Locator]]


@dataclass
class PanelOpenResult:
    """Outcome for a shared panel open attempt."""

    opened: bool
    candidate_name: str | None = None
    last_error: Exception | None = None


@dataclass
class EventPageAuthResult:
    """Outcome for validating the event page before panel automation starts."""

    ready: bool
    auth_required: bool
    reason: str
    screenshot_asset_id: str | None = None


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

    def _panel_back_hidden() -> bool:
        """Treat the panel as closed only after the back button disappears."""
        with suppress(Exception):
            page.wait_for_selector(
                PANEL_BACK_SELECTOR,
                state="hidden",
                timeout=timeout,
            )
            return True
        return not is_locator_visible(page.locator(PANEL_BACK_SELECTOR).first, timeout=250)

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
            if _panel_back_hidden():
                return True
            logger.warning(
                "Panel back remained visible while %s after %s click",
                context,
                "forced" if force_click else "normal",
            )
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


def _has_hoyolab_auth_cookies(page: Page) -> bool:
    """Return whether the context carries a full HoYoLab login cookie pair.

    The page itself is a canvas/sprite UI whose home content is unreliable to scrape,
    so the cookies are the authoritative "logged in" signal.
    """
    with suppress(Exception):
        cookies = page.context.cookies()
        present = {
            cookie.get("name")
            for cookie in cookies
            if any(domain in (cookie.get("domain") or "") for domain in HOYOLAB_AUTH_COOKIE_DOMAINS)
        }
        return any(
            first in present and second in present for first, second in HOYOLAB_AUTH_COOKIE_PAIRS
        )
    return False


def _collect_event_page_auth_indicators(page: Page) -> dict[str, object]:
    """Collect lightweight signals that distinguish guest vs ready event page state."""
    login_link_visible = is_locator_visible(
        page.get_by_role("link", name=EVENT_PAGE_LOGIN_TEXT).first,
        timeout=250,
    )
    login_button_visible = is_locator_visible(
        page.get_by_role("button", name=EVENT_PAGE_LOGIN_TEXT).first,
        timeout=250,
    )
    login_frame_visible = is_locator_visible(
        page.locator(EVENT_PAGE_LOGIN_FRAME_SELECTOR).first,
        timeout=250,
    )
    mission_hint_visible = is_locator_visible(
        page.get_by_text(EVENT_PAGE_MISSION_HINT_TEXT, exact=False).first,
        timeout=250,
    )

    launcher_image_count = 0
    with suppress(Exception):
        launcher_image_count = page.get_by_role("img").count()

    return {
        "login_link_visible": login_link_visible,
        "login_button_visible": login_button_visible,
        "login_frame_visible": login_frame_visible,
        "mission_hint_visible": mission_hint_visible,
        "launcher_image_count": launcher_image_count,
        # Home content alone is not enough; the auth-ready decision also requires
        # the login controls to be absent.
        "home_signal_visible": mission_hint_visible or launcher_image_count >= 2,
    }


def _capture_event_page_auth_screenshot(page: Page) -> str | None:
    """Capture the current event page when auth validation fails."""
    screenshot_name = (
        f"{EVENT_PAGE_AUTH_SCREENSHOT_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    try:
        return save_page_screenshot(page, screenshot_name)
    except Exception as exc:
        logger.warning("Could not save event-page auth failure screenshot: %s", exc)
        return None


def _build_auth_required_result(
    page: Page,
    *,
    context: str,
    reason: str,
    indicators: dict[str, object],
    timeout_ms: int,
    poll_interval_ms: int,
) -> EventPageAuthResult:
    """Capture diagnostics and return a blocking auth-required outcome."""
    import sentry_sdk

    screenshot_asset_id = _capture_event_page_auth_screenshot(page)
    current_url = getattr(page, "url", None)
    logger.warning(
        "Event page requires manual login while %s: reason=%s, screenshot_asset_id=%s",
        context,
        reason,
        screenshot_asset_id or "unavailable",
    )

    with sentry_sdk.isolation_scope():
        sentry_sdk.set_tag("event_page.issue", "manual_login_required")
        sentry_sdk.set_tag("event_page.auth_required", "true")
        sentry_sdk.set_tag("event_page.reason", reason)
        sentry_sdk.set_context(
            "event_page_auth",
            {
                "context": context,
                "reason": reason,
                "timeout_ms": timeout_ms,
                "poll_interval_ms": poll_interval_ms,
                "current_url": current_url,
                "screenshot_asset_id": screenshot_asset_id,
                **indicators,
            },
        )
        sentry_sdk.capture_message("Event page requires manual login", level="warning")

    return EventPageAuthResult(
        ready=False,
        auth_required=True,
        reason=reason,
        screenshot_asset_id=screenshot_asset_id,
    )


def wait_for_authenticated_event_home(
    page: Page,
    *,
    context: str,
    timeout_ms: int = EVENT_PAGE_AUTH_TIMEOUT_MS,
    poll_interval_ms: int = EVENT_PAGE_AUTH_POLL_INTERVAL_MS,
) -> EventPageAuthResult:
    """Verify the event page is usable before mission/shopping/draw automation starts.

    The Mimo event page is a canvas/sprite UI: its home text is baked into images and
    its icons are not ``<img>`` roles, so the DOM "home" heuristic frequently stays
    false while the entrance animation plays. To avoid blocking every scheduled run on
    a false positive, this gate blocks **only** when a login form is positively shown.
    On the ambiguous case (neither home nor login detected) it trusts a valid session
    cookie pair and proceeds, leaving the downstream image-recognition handlers — which
    have their own retries — to surface any real failure.
    """
    has_auth_cookies = _has_hoyolab_auth_cookies(page)

    # Give late-attaching content a brief moment to settle without forcing a long
    # wait on pages that never reach networkidle (capped, best-effort).
    with suppress(Exception):
        page.wait_for_load_state("load", timeout=3000)

    deadline = time.monotonic() + (timeout_ms / 1000)
    last_indicators = _collect_event_page_auth_indicators(page)
    reason = "event_home_not_ready"

    while True:
        last_indicators = _collect_event_page_auth_indicators(page)
        login_visible = any(
            (
                last_indicators["login_link_visible"],
                last_indicators["login_button_visible"],
                last_indicators["login_frame_visible"],
            )
        )
        home_signal_visible = bool(last_indicators["home_signal_visible"])

        if login_visible:
            reason = "login_prompt_visible"
            break

        if home_signal_visible:
            logger.info("Event page ready while %s", context)
            return EventPageAuthResult(
                ready=True,
                auth_required=False,
                reason="event_home_ready",
            )

        if time.monotonic() >= deadline:
            break

        page.wait_for_timeout(poll_interval_ms)

    # A login form was positively shown -> a real re-login is needed, even if stale
    # cookies linger in the context.
    if reason == "login_prompt_visible":
        return _build_auth_required_result(
            page,
            context=context,
            reason=reason,
            indicators=last_indicators,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )

    # Ambiguous: neither home nor login detected within the window. A valid session
    # cookie pair is authoritative, so proceed instead of spamming a manual-login
    # prompt. No failure screenshot here keeps the binary_assets table from bloating.
    if has_auth_cookies:
        logger.info(
            "Event page home signals not detected while %s, but HoYoLab auth cookies "
            "are present; proceeding (reason=auth_cookies_present)",
            context,
        )
        return EventPageAuthResult(
            ready=True,
            auth_required=False,
            reason="auth_cookies_present",
        )

    # No home content and no session cookies -> genuinely signed out.
    return _build_auth_required_result(
        page,
        context=context,
        reason=reason,
        indicators=last_indicators,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
    )


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
