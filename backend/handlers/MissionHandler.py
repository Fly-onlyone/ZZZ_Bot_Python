"""Mission automation module for ZZZ Bot.

Handles daily check-ins, mission completion, and reward collection.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from automation import RetryHelper
from automation.ImageProcessor import ImageProcessor, find_correct_avatar
from core.constants import PANEL_BACK_SELECTOR
from utils.DataHandler import maintain_mission_data
from utils.NotificationHelper import NotificationModule
from utils.screenshot_store import save_locator_screenshot, save_page_screenshot

# Configure logging
logger = logging.getLogger(__name__)


def _safe_track(page: Page, selector: str, action: str, success: bool, *, error_message: str | None = None) -> None:
    try:
        from automation.LocatorTracker import track_locator
        track_locator(page, selector, "MissionHandler", action, success, error_message=error_message)
    except Exception:
        pass

# Constants
CHECK_IN_URL = "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
CHECK_IN_URL_WITH_AUTH = (
    "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
    "?act_id=e202406031448091&hyl_auth_required=true"
)

# Selector constants
DIALOG_CLOSE_SELECTOR = ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
DIALOG_BODY_SELECTOR = "div.components-pc-assets-__dialog_---dialog-body---1SieDs"
MISSION_WRAPPER_SELECTOR = ".wrapper-O3T67n"
MISSION_BUTTON_TEXT = "Carry out missions to earn"
MISSION_BUTTON_PATTERN = re.compile(
    r"Carry out missions to earn(?: points)?",
    re.IGNORECASE,
)
AVATAR_SELECTOR = "div.avatarsItemImg-AiUG1h"
TASK_ITEM_SELECTOR = ".taskItemPcLeft-Aetp6m"
CLAIMED_POPUP_TEXT = "Claimed!"
LOGIN_MODAL_TITLE_TEXT = "Account Log In"
LOGIN_MODAL_EMAIL_PLACEHOLDER = "Username/Email"

# Timing constants
DIALOG_WAIT_TIMEOUT = 5000
MISSION_CLICK_WAIT = 2000
RETRY_WAIT = 1000
CHECK_IN_READY_TIMEOUT = 10000
CHECK_IN_POLL_INTERVAL = 250

# Status messages
STATUS_SUCCESS = "Login Success"
STATUS_FAILED = "Login Failed"
STATUS_LINK_NOT_OPENED = "Link isn't opened"
CHECK_IN_DETAIL_AUTH_REQUIRED = "auth_required"
POPUP_OUTCOME_NONE = "none"
POPUP_OUTCOME_SUCCESS = "success"
POPUP_OUTCOME_FAILED = "failed"
CHECK_IN_READY = "ready"
CHECK_IN_TIMEOUT = "timeout"
CHECK_IN_AUTH_REQUIRED = "auth_required"


def _close_dialog_if_visible(page: Page) -> None:
    """Close any visible dialog popup.

    Args:
        page: Playwright Page instance
    """
    try:
        close_btn = page.locator(DIALOG_CLOSE_SELECTOR)
        if close_btn.is_visible(timeout=1000):
            close_btn.click()
            _safe_track(page, DIALOG_CLOSE_SELECTOR, "click", True)
            logger.info("Closed popup dialog")
        else:
            _safe_track(page, DIALOG_CLOSE_SELECTOR, "visibility_check", False)
    except PlaywrightTimeoutError:
        logger.debug("No dialog found to close")
    except Exception as e:
        logger.warning(f"Error closing dialog: {e}")


def _locator_is_visible(locator: Locator, timeout: int = 500) -> bool:
    """Return whether the first locator match is visible without raising."""
    try:
        return locator.first.is_visible(timeout=timeout)
    except Exception:
        return False


def _set_check_in_status(
    todays_data: Dict,
    status: str,
    *,
    detail: Optional[str] = None,
) -> None:
    """Store check-in status and optional detail for the current day."""
    todays_data["check_in"] = status
    if detail:
        todays_data["check_in_detail"] = detail
    else:
        todays_data.pop("check_in_detail", None)


def _build_check_in_context(
    page: Page,
    day_text: str,
    *,
    result: str,
    auth_required: bool,
    reason: str,
    screenshot_asset_id: Optional[str] = None,
) -> Dict[str, object]:
    """Create a consistent check-in context payload for tracing and alerts."""
    return {
        "day": day_text,
        "result": result,
        "auth_required": auth_required,
        "page_url": page.url,
        "reason": reason,
        "screenshot_asset_id": screenshot_asset_id,
        "manual_login_url": CHECK_IN_URL_WITH_AUTH if auth_required else None,
    }


def _annotate_check_in_span(span, context: Dict[str, object]) -> None:
    """Attach structured check-in metadata to the active Sentry span."""
    span.set_tag("check_in.result", str(context["result"]))
    span.set_tag("check_in.auth_required", str(context["auth_required"]).lower())
    span.set_data("check_in.day", context["day"])
    span.set_data("check_in.page_url", context["page_url"])
    span.set_data("check_in.reason", context["reason"])
    span.set_data("check_in.manual_login_url", context["manual_login_url"])
    if context.get("screenshot_asset_id"):
        span.set_data("check_in.screenshot_asset_id", context["screenshot_asset_id"])


def _record_check_in_failure(
    todays_data: Dict,
    message: str,
    *,
    detail: Optional[str] = None,
) -> None:
    """Persist and report a check-in failure once the popup is known to exist."""
    _set_check_in_status(todays_data, STATUS_FAILED, detail=detail)
    logger.error(message)


def _is_check_in_login_modal_visible(page: Page, timeout: int = 500) -> bool:
    """Return whether the HoYoVerse account login modal is blocking check-in."""
    title = page.get_by_text(LOGIN_MODAL_TITLE_TEXT, exact=True)
    username_field = page.get_by_placeholder(LOGIN_MODAL_EMAIL_PLACEHOLDER)
    return _locator_is_visible(title, timeout=timeout) and _locator_is_visible(
        username_field, timeout=timeout
    )


def _capture_check_in_screenshot(page: Page, prefix: str) -> Optional[str]:
    """Capture the current page state to MongoDB for failed check-in diagnostics."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    try:
        asset_id = save_page_screenshot(page, filename)
        logger.info(
            "Saved check-in diagnostic screenshot to MongoDB asset: %s", asset_id
        )
        return asset_id
    except Exception as exc:
        logger.warning("Failed to capture check-in diagnostic screenshot: %s", exc)
        return None


def _notify_check_in_auth_required() -> None:
    """Send a desktop notification when check-in needs a fresh login."""
    from core.GlobalVar import CONFIG

    NotificationModule.notify(
        title="ZZZ Bot",
        message="Check-in needs manual login. Open Manual Login and choose CHECK_IN_URL.",
        app_icon=CONFIG["SAD_ICON"],
    )


def _capture_check_in_auth_required_event(context: Dict[str, object]) -> None:
    """Emit a dedicated Sentry warning for auth-required check-in failures."""
    import sentry_sdk

    with sentry_sdk.isolation_scope():
        sentry_sdk.set_tag("check_in.result", str(context["result"]))
        sentry_sdk.set_tag("check_in.auth_required", "true")
        sentry_sdk.set_context("check_in", context)
        sentry_sdk.capture_message(
            "Check-in requires manual login",
            level="warning",
        )


def _record_check_in_auth_required(
    page: Page,
    todays_data: Dict,
    day_text: str,
    span,
    reason: str,
) -> None:
    """Persist, notify, and trace when the check-in popup requires re-auth."""
    screenshot_asset_id = _capture_check_in_screenshot(page, "checkin_auth_required")
    _record_check_in_failure(
        todays_data,
        reason,
        detail=CHECK_IN_DETAIL_AUTH_REQUIRED,
    )
    context = _build_check_in_context(
        page,
        day_text,
        result=STATUS_FAILED,
        auth_required=True,
        reason=reason,
        screenshot_asset_id=screenshot_asset_id,
    )
    _annotate_check_in_span(span, context)
    _capture_check_in_auth_required_event(context)
    _notify_check_in_auth_required()


def _wait_for_check_in_ready(page: Page, day_btn: Locator, success_msg: Locator) -> str:
    """Wait until the check-in popup is actionable or already completed."""
    deadline = time.monotonic() + (CHECK_IN_READY_TIMEOUT / 1000)

    while time.monotonic() < deadline:
        if _locator_is_visible(success_msg):
            return STATUS_SUCCESS
        if _is_check_in_login_modal_visible(page):
            return CHECK_IN_AUTH_REQUIRED
        if _locator_is_visible(day_btn):
            return CHECK_IN_READY
        day_btn.page.wait_for_timeout(CHECK_IN_POLL_INTERVAL)

    if _locator_is_visible(success_msg):
        return STATUS_SUCCESS
    if _is_check_in_login_modal_visible(page):
        return CHECK_IN_AUTH_REQUIRED
    return CHECK_IN_TIMEOUT


def handle_check_in(new_page: Page, todays_data: Dict) -> None:
    """Perform daily check-in and update status.

    Args:
        new_page: Playwright Page instance for check-in
        todays_data: Dictionary to store today's mission data
    """
    # Skip if already checked in today
    if todays_data.get("check_in") == STATUS_SUCCESS:
        logger.info("Check-in already completed today, skipping")
        return

    logger.info("Starting check-in process...")
    import sentry_sdk

    # Compute current day and locate button
    today = datetime.now().day
    day_text = f"Day {today}"

    with sentry_sdk.start_span(op="browser.interact", name="check-in") as check_in_span:
        check_in_span.set_data("workflow.phase", "mission")
        check_in_span.set_data("check_in.day", day_text)

        try:
            new_page.wait_for_load_state("domcontentloaded", timeout=3000)
        except PlaywrightTimeoutError:
            logger.debug(
                "Check-in popup did not report domcontentloaded before locator wait"
            )
        new_page.wait_for_timeout(500)

        _close_dialog_if_visible(new_page)

        day_btn = new_page.get_by_text(day_text, exact=True)
        success_msg = new_page.locator(DIALOG_BODY_SELECTOR)

        readiness = _wait_for_check_in_ready(new_page, day_btn, success_msg)
        if readiness == STATUS_SUCCESS:
            logger.info("Check-in success dialog already visible")
            _set_check_in_status(todays_data, STATUS_SUCCESS)
            _annotate_check_in_span(
                check_in_span,
                _build_check_in_context(
                    new_page,
                    day_text,
                    result=STATUS_SUCCESS,
                    auth_required=False,
                    reason="Success dialog already visible",
                ),
            )
            return

        if readiness == CHECK_IN_AUTH_REQUIRED:
            _record_check_in_auth_required(
                new_page,
                todays_data,
                day_text,
                check_in_span,
                "Check-in requires login before the reward day became actionable",
            )
            return

        if readiness != CHECK_IN_READY:
            reason = f"Check-in popup opened but '{day_text}' never became actionable"
            _safe_track(new_page, DIALOG_BODY_SELECTOR, "visibility_check", False, error_message=reason)
            _record_check_in_failure(
                todays_data,
                reason,
            )
            _annotate_check_in_span(
                check_in_span,
                _build_check_in_context(
                    new_page,
                    day_text,
                    result=STATUS_FAILED,
                    auth_required=False,
                    reason=reason,
                ),
            )
            return

        logger.info(f"Attempting check-in for {day_text}")

        # Retry until success message appears
        try:
            clicked = RetryHelper.retry_until_screen_appears(success_msg, day_btn)
        except Exception as exc:
            reason = f"Check-in popup opened but retry flow failed: {exc}"
            _record_check_in_failure(
                todays_data,
                reason,
            )
            _annotate_check_in_span(
                check_in_span,
                _build_check_in_context(
                    new_page,
                    day_text,
                    result=STATUS_FAILED,
                    auth_required=False,
                    reason=reason,
                ),
            )
            return

        if clicked or _locator_is_visible(success_msg, timeout=1000):
            logger.info("Check-in successful!")
            _set_check_in_status(todays_data, STATUS_SUCCESS)
            asset_id = save_locator_screenshot(success_msg, "login_reward.png")
            logger.info("Saved login reward screenshot to MongoDB asset: %s", asset_id)
            _annotate_check_in_span(
                check_in_span,
                _build_check_in_context(
                    new_page,
                    day_text,
                    result=STATUS_SUCCESS,
                    auth_required=False,
                    reason="Day button click produced success dialog",
                    screenshot_asset_id=asset_id,
                ),
            )
        elif _is_check_in_login_modal_visible(new_page):
            _record_check_in_auth_required(
                new_page,
                todays_data,
                day_text,
                check_in_span,
                f"Check-in opened the HoYoVerse login modal after clicking '{day_text}'",
            )
        else:
            reason = f"Check-in popup opened but clicking '{day_text}' did not produce success"
            _record_check_in_failure(
                todays_data,
                reason,
            )
            _annotate_check_in_span(
                check_in_span,
                _build_check_in_context(
                    new_page,
                    day_text,
                    result=STATUS_FAILED,
                    auth_required=False,
                    reason=reason,
                ),
            )


# --- Mission Logic ---
class Mission:
    """Handles mission execution and reward claiming."""

    def __init__(self, page: Page, todays_data: Dict):
        """Initialize Mission handler.

        Args:
            page: Playwright Page instance
            todays_data: Dictionary to store mission results
        """
        self.page = page
        self.todays_data = todays_data
        self._popup_handler = None
        self._pending_popups: List[Page] = []

    def _queue_popup(self, new_page: Page) -> None:
        """Queue popup pages so mission flow can handle them outside the event callback."""
        self._pending_popups.append(new_page)
        logger.info("Queued mission popup for deferred handling")

    def process_pending_popups(self) -> str:
        """Process and close any queued popup pages."""
        popup_outcome = POPUP_OUTCOME_NONE

        while self._pending_popups:
            popup_page = self._pending_popups.pop(0)
            try:
                current_outcome = handle_pop_up(popup_page, self.todays_data)
                if current_outcome == POPUP_OUTCOME_FAILED:
                    popup_outcome = POPUP_OUTCOME_FAILED
                elif (
                    current_outcome == POPUP_OUTCOME_SUCCESS
                    and popup_outcome != POPUP_OUTCOME_FAILED
                ):
                    popup_outcome = POPUP_OUTCOME_SUCCESS
            except Exception as exc:
                logger.warning("Error processing mission popup: %s", exc)

        return popup_outcome

    def attach_page_listener(self) -> None:
        """Attach event listener to handle popup pages (e.g., check-in)."""
        self._popup_handler = self._queue_popup
        self.page.context.on("page", self._popup_handler)

    def detach_page_listener(self) -> None:
        """Remove the popup event listener to prevent interference with other handlers."""
        if self._popup_handler:
            self.page.context.remove_listener("page", self._popup_handler)
            self._popup_handler = None
            self.process_pending_popups()
            logger.info("Popup listener detached")

    def perform_mission(self, mission_button: Locator, max_retries: int = 5) -> bool:
        """Attempt to complete a mission by clicking the button.

        Args:
            mission_button: Locator for the mission button
            max_retries: Maximum number of click attempts

        Returns:
            True if mission completed successfully, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            try:
                if mission_button.is_enabled(timeout=1000):
                    mission_button.click()
                    logger.info(
                        f"Mission button clicked (attempt {attempt}/{max_retries})"
                    )
                    self.page.wait_for_timeout(MISSION_CLICK_WAIT)

                popup_outcome = self.process_pending_popups()

                # Check for success popup
                claimed_popup = self.page.locator(f"text={CLAIMED_POPUP_TEXT}")
                if claimed_popup.is_visible(timeout=2000):
                    logger.info("Mission reward claimed successfully")
                    return True

                if popup_outcome == POPUP_OUTCOME_SUCCESS:
                    logger.info("Mission completed successfully via check-in popup")
                    return True

                if popup_outcome == POPUP_OUTCOME_FAILED:
                    logger.warning(
                        "Mission popup completed without a successful check-in"
                    )
                    return False

            except PlaywrightTimeoutError:
                logger.warning(f"Mission button not enabled on attempt {attempt}")
                if attempt == max_retries:
                    _safe_track(self.page, TASK_ITEM_SELECTOR, "click", False, error_message="Button not enabled after max retries")
            except Exception as e:
                logger.error(f"Error performing mission (attempt {attempt}): {e}")

            if attempt < max_retries:
                self.page.wait_for_timeout(RETRY_WAIT)

        logger.warning("Unable to complete mission after maximum retries")
        return False


def handle_pop_up(new_page: Page, todays_data: Dict) -> str:
    """Handle popup pages, specifically check-in dialogs.

    Args:
        new_page: Newly opened page
        todays_data: Dictionary to store mission results
    """
    popup_outcome = POPUP_OUTCOME_NONE

    try:
        if CHECK_IN_URL in new_page.url:
            logger.info("Check-in popup detected")
            handle_check_in(new_page, todays_data)
            if todays_data.get("check_in") == STATUS_SUCCESS:
                popup_outcome = POPUP_OUTCOME_SUCCESS
            elif todays_data.get("check_in") == STATUS_FAILED:
                popup_outcome = POPUP_OUTCOME_FAILED
            else:
                _record_check_in_failure(
                    todays_data,
                    "Check-in popup was detected but no final status was recorded",
                )
                popup_outcome = POPUP_OUTCOME_FAILED
        else:
            logger.info(f"Closing unrelated popup: {new_page.url}")
    finally:
        try:
            new_page.close()
        except Exception as exc:
            logger.debug("Popup page was already closed: %s", exc)

    return popup_outcome


def open_mission_screen(page: Page) -> bool:
    """Navigate to the mission screen.

    Args:
        page: Playwright Page instance

    Returns:
        True if mission screen opened successfully, False otherwise
    """
    logger.info("Opening mission screen...")
    target_screen = page.locator(PANEL_BACK_SELECTOR).first
    mission_button = page.get_by_text(MISSION_BUTTON_PATTERN).first

    success = RetryHelper.retry_until_screen_appears(target_screen, mission_button)
    if success:
        logger.info("Mission screen opened successfully")
    else:
        logger.warning(
            "Mission screen did not open after clicking launcher text '%s'",
            MISSION_BUTTON_TEXT,
        )
    return success


def count_mission(page: Page) -> int:
    """Count the number of available missions.

    Args:
        page: Playwright Page instance

    Returns:
        Number of missions found
    """
    logger.info("Counting available missions...")
    avatar = find_correct_avatar(page)

    if not avatar:
        logger.warning("ZZZ avatar not found, no missions available")
        return 0

    avatar.click()
    logger.info("Clicked on ZZZ avatar")

    mission_items = page.locator(TASK_ITEM_SELECTOR)
    count = RetryHelper.retry_until_non_zero_count(mission_items)

    logger.info(f"Found {count} available missions")
    return count


def _get_or_create_mission_record(
    todays_data: Dict, mission_name: str
) -> Optional[Dict]:
    """Get existing mission record or create a new one.

    Args:
        todays_data: Today's mission data dictionary
        mission_name: Name of the mission

    Returns:
        Existing mission record or None if creating new
    """
    missions = todays_data.get("missions", [])
    return next((m for m in missions if m["name"] == mission_name), None)


def _perform_direct_check_in(page: Page, todays_data: Dict) -> None:
    """Perform check-in directly when no missions are available.

    Args:
        page: Playwright Page instance
        todays_data: Dictionary to store mission results
    """
    logger.info("No missions available, performing direct check-in")
    check_in_page = page.context.new_page()
    try:
        check_in_page.goto(CHECK_IN_URL_WITH_AUTH)
        handle_check_in(check_in_page, todays_data)
    finally:
        check_in_page.close()


def doing_mission(mission_count: int, page: Page, todays_data: Dict) -> None:
    """Execute all available missions.

    Args:
        mission_count: Number of missions to process
        page: Playwright Page instance
        todays_data: Dictionary to store mission results
    """
    if mission_count == 0:
        _perform_direct_check_in(page, todays_data)
        return

    # Initialize mission handler (reusable instance)
    mission_handler = Mission(page, todays_data)
    image_processor = None
    mission_handler.attach_page_listener()
    listener_attached = True

    for idx in range(1, mission_count + 1):
        logger.info(f"Processing mission {idx}/{mission_count}")

        # Locate mission elements
        mission_text_selector = "div:nth-child({}) > {} > .top-ohhwaM".format(
            idx, TASK_ITEM_SELECTOR
        )
        mission_button_selector = (
            "div:nth-child({}) > .taskItemPcRight-3-Kwr1 > .icon2-Y7R3Mu".format(idx)
        )
        mission_text_loc = page.locator(mission_text_selector)
        mission_btn_loc = page.locator(mission_button_selector)

        try:
            mission_name = mission_text_loc.inner_text()
            logger.info(f"Mission name: {mission_name}")
        except Exception as e:
            logger.error(f"Failed to get mission name: {e}")
            continue

        # Check if already completed
        existing_record = _get_or_create_mission_record(todays_data, mission_name)
        if existing_record and existing_record.get("state") == "Finished":
            logger.info(f"Mission '{mission_name}' already completed, skipping")
            continue

        # Detect mission state via image comparison
        if not image_processor:
            image_processor = ImageProcessor(page, mission_btn_loc)
        else:
            image_processor.button = mission_btn_loc

        button_state = image_processor.detect_button_state()

        if button_state == "Finished":
            mission_done = True
            logger.info(
                f"Mission '{mission_name}' already finished (detected via image)"
            )
        else:
            if button_state == "Reward":
                logger.info(
                    "Mission '%s' is directly claimable; attempting action",
                    mission_name,
                )
            elif button_state == "Unfinished":
                logger.info(
                    "Mission '%s' is unfinished; attempting action in case it opens a popup",
                    mission_name,
                )
            else:
                logger.warning(
                    "Mission '%s' button state is unknown; attempting action anyway",
                    mission_name,
                )
            mission_done = mission_handler.perform_mission(mission_btn_loc)

        # Update mission record
        status = "Finished" if mission_done else "Unfinished"
        if existing_record:
            existing_record["state"] = status
        else:
            todays_data.setdefault("missions", []).append(
                {"name": mission_name, "state": status}
            )

    # Remove popup listener to prevent interference with other handlers (e.g., ShoppingHandler)
    if listener_attached:
        mission_handler.detach_page_listener()

    # Log final check-in status
    check_in_status = todays_data.get("check_in", STATUS_LINK_NOT_OPENED)
    if check_in_status == STATUS_LINK_NOT_OPENED:
        logger.warning("Check-in link was not opened - skipping unnecessary wait")

    logger.info(f"Check-in status: {check_in_status}")


def run(
    output_file: str, page: Page, previous_data: List[Dict], todays_data: Dict
) -> bool:
    """Main entry point for mission automation.

    Args:
        output_file: Path to save mission data
        page: Playwright Page instance
        previous_data: Historical mission data records
        todays_data: Today's mission data to populate

    Returns:
        True when mission flow opened and completed, otherwise False.
    """
    import sentry_sdk

    logger.info("Starting mission automation...")

    with sentry_sdk.start_span(op="automation.mission", name="mission-handler") as span:
        span.set_data("workflow.phase", "mission")
        try:
            # Navigate to mission screen
            with sentry_sdk.start_span(
                op="browser.navigate", name="Open mission screen"
            ):
                if not open_mission_screen(page):
                    logger.error("Failed to open mission screen, aborting")
                    return False

            # Count and execute missions
            with sentry_sdk.start_span(
                op="browser.interact", name="Count and execute missions"
            ):
                mission_count = count_mission(page)
                doing_mission(mission_count, page, todays_data)

            # Save mission data
            with sentry_sdk.start_span(op="db.write", name="Save mission data"):
                maintain_mission_data(previous_data, output_file, todays_data)

            logger.info("Mission automation completed successfully")
            return True

        except Exception as e:
            span.set_status("internal_error")
            logger.error(f"Mission automation failed: {e}", exc_info=True)
            raise
