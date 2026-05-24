"""Hunt Mode automation module for ZZZ Bot.

Handles automatic purchasing of specific items when the shop renews.
"""

import logging
import time
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from automation import EventNavigator, RedeemAutofill
from automation.Selectors import (
    SHOPPING_ITEM,
    SHOPPING_ITEM_BUTTON,
)
from automation.tracking import safe_track
from core.GlobalVar import CONFIG, settings
from playwright.sync_api import (
    Page,
    sync_playwright,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from utils import NotificationHelper
from utils.DataHandler import load_shopping_data, save_shopping_data
from utils.storage_state_store import (
    build_context_options,
    save_context_storage_state,
)

from . import ShoppingHandler

logger = logging.getLogger(__name__)


def _safe_track(
    page,
    selector: str,
    action: str,
    success: bool,
    *,
    error_message: str | None = None,
    locator=None,
) -> None:
    safe_track(
        page,
        selector,
        "HuntModeHandler",
        action,
        success,
        error_message=error_message,
        locator=locator,
    )


# Wait buffer time before item becomes available (in seconds)
WAIT_BUFFER_SECONDS = 120  # Open shopping screen 2 minutes early
POLL_INTERVAL_SECONDS = 1  # Check button text every 1 second
EXCHANGE_BUTTON_TEXT = "Exchange"
UNAVAILABLE_BUTTON_TOKENS = ("limit reached", "sold out", "unavailable")
_hunt_target_date: Optional[datetime] = None


def set_hunt_target_date(target_date: Optional[datetime]) -> None:
    """Store the scheduled hunt target date inside the handler module."""
    global _hunt_target_date
    _hunt_target_date = target_date


def get_hunt_items() -> List[str]:
    """Get the list of items marked for hunting, sorted by shopping priority.

    Returns:
        List of item names to hunt, ordered by their priority in Selected list
    """
    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)

    if not shopping_data:
        logger.warning("No shopping data found")
        return []

    hunt_items = shopping_data.get("Hunt", [])
    selected_items = shopping_data.get("Selected", [])

    if not hunt_items:
        logger.info("No items marked for hunting")
        return []

    # Sort hunt items by their priority in Selected list
    # Items that appear earlier in Selected list have higher priority
    sorted_hunt_items = []
    for item in selected_items:
        if item in hunt_items:
            sorted_hunt_items.append(item)

    # Add any hunt items not in Selected (shouldn't happen, but just in case)
    for item in hunt_items:
        if item not in sorted_hunt_items:
            sorted_hunt_items.append(item)
            logger.warning(f"Hunt item '{item}' not found in Selected list")

    logger.info(
        f"Found {len(sorted_hunt_items)} items to hunt (ordered by priority): {sorted_hunt_items}"
    )
    return sorted_hunt_items


def get_next_hunt_time() -> Optional[str]:
    """Calculate the next hunt time based on item availability.

    Returns:
        Next hunt time in format "HH:MM DD/MM/YY" or None if no items need hunting
    """
    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)

    if not shopping_data:
        logger.warning("No shopping data found")
        return None

    hunt_items = shopping_data.get("Hunt", [])
    if not hunt_items:
        logger.info("No items marked for hunting")
        return None

    items_list = shopping_data.get("Item's list", {})
    earliest_time = None

    for item_name in hunt_items:
        item_data = items_list.get(item_name)
        if not item_data:
            logger.warning(f"Hunt item '{item_name}' not found in shopping data")
            continue

        availability = item_data.get("Available", "")

        # Check if availability is a return time (format: "HH:MM DD/MM/YY")
        if "/" in availability and ":" in availability:
            return_time_str = availability
            logger.info(f"Item '{item_name}' will be available at {return_time_str}")

            # Parse and compare times to find earliest
            try:
                return_time = datetime.strptime(return_time_str, "%H:%M %d/%m/%y")
                if earliest_time is None or return_time < earliest_time:
                    earliest_time = return_time
            except ValueError as e:
                logger.error(f"Failed to parse return time '{return_time_str}': {e}")

    if earliest_time:
        result = earliest_time.strftime("%H:%M %d/%m/%y")
        logger.info(f"Next hunt scheduled for: {result}")
        return result

    logger.info("No hunt items with return times found")
    return None


def _is_unavailable_status(button_text: str) -> bool:
    normalized_text = button_text.strip().lower()
    return any(token in normalized_text for token in UNAVAILABLE_BUTTON_TOKENS)


def wait_for_exchange_button(
    page: Page,
    item_name: str,
    max_wait_seconds: int = 180,
    poll_interval_seconds: int = POLL_INTERVAL_SECONDS,
    backoff_enabled: bool = True,
    early_exit_on_unavailable: bool = True,
) -> bool:
    """Wait at shopping screen and monitor item button until 'Exchange' appears.

    Args:
        page: Playwright Page instance
        item_name: Name of the item to monitor
        max_wait_seconds: Maximum time to wait
        poll_interval_seconds: Base poll interval in seconds
        backoff_enabled: Increase poll interval gradually when waiting
        early_exit_on_unavailable: Stop early for terminal unavailable states

    Returns:
        True if Exchange button appeared, False otherwise
    """
    import sentry_sdk

    max_wait = max(1, int(max_wait_seconds))
    base_interval = max(1, int(poll_interval_seconds))
    max_interval = base_interval * 5

    with sentry_sdk.start_span(op="automation.poll", name="wait_for_exchange") as span:
        span.set_data("workflow.phase", "hunt_poll")
        span.set_data("hunt.item_name", item_name)
        span.set_data("hunt.max_wait_seconds", max_wait)
        span.set_data("hunt.poll_interval_seconds", base_interval)
        span.set_data("hunt.backoff_enabled", backoff_enabled)
        span.set_data("hunt.early_exit_on_unavailable", early_exit_on_unavailable)

        logger.info("Waiting for '%s' to become available...", item_name)

        start_time = time.time()
        last_status = None
        attempts = 0
        current_interval = base_interval
        exit_reason = "timeout"
        available = False

        try:
            while time.time() - start_time < max_wait:
                attempts += 1
                try:
                    item_locator = page.locator(SHOPPING_ITEM).filter(
                        has=page.get_by_text(item_name, exact=True)
                    )

                    if item_locator.count() == 0:
                        if last_status != "__missing__":
                            logger.warning("Item '%s' not found on page", item_name)
                            last_status = "__missing__"
                    else:
                        button = item_locator.locator(SHOPPING_ITEM_BUTTON)
                        button_text = button.inner_text().strip()

                        if button_text != last_status:
                            logger.info("Item '%s' button status: %s", item_name, button_text)
                            last_status = button_text

                        if button_text == EXCHANGE_BUTTON_TEXT:
                            logger.info("Exchange button available for '%s'", item_name)
                            available = True
                            exit_reason = "exchange_available"
                            break

                        if (
                            early_exit_on_unavailable
                            and button_text
                            and _is_unavailable_status(button_text)
                        ):
                            logger.info(
                                "Early exit for '%s' due to unavailable status: %s",
                                item_name,
                                button_text,
                            )
                            exit_reason = "unavailable_status"
                            break

                    remaining = max_wait - (time.time() - start_time)
                    if remaining <= 0:
                        break

                    sleep_for = min(float(current_interval), remaining)
                    time.sleep(sleep_for)

                    if backoff_enabled:
                        current_interval = min(max_interval, current_interval + base_interval)

                except Exception as e:
                    logger.error("Error while monitoring '%s': %s", item_name, e)
                    remaining = max_wait - (time.time() - start_time)
                    if remaining <= 0:
                        break
                    time.sleep(min(float(current_interval), remaining))
                    if backoff_enabled:
                        current_interval = min(max_interval, current_interval + base_interval)
        finally:
            elapsed = time.time() - start_time
            span.set_data("hunt.poll_attempts", attempts)
            span.set_data("hunt.exit_reason", exit_reason)
            span.set_data("hunt.elapsed_seconds", round(elapsed, 3))
            span.set_data("hunt.final_status", last_status)

        if not available:
            if exit_reason == "timeout":
                logger.warning("Timeout waiting for '%s' to become available", item_name)
            else:
                logger.warning("Stopped waiting for '%s' with reason: %s", item_name, exit_reason)
            _safe_track(
                page,
                SHOPPING_ITEM_BUTTON,
                "wait_for",
                False,
                error_message=f"{item_name}: {exit_reason}",
            )
        else:
            _safe_track(
                page,
                SHOPPING_ITEM_BUTTON,
                "wait_for",
                True,
                locator=page.locator(SHOPPING_ITEM_BUTTON),
            )

        return available


def exchange_item_only(page: Page, item_name: str) -> Optional[str]:
    """Exchange an item and return the redemption code WITHOUT redeeming it.

    Args:
        page: Playwright Page instance
        item_name: Name of the item to exchange

    Returns:
        Redemption code if successful, None if failed
    """
    logger.info(f"Exchanging item: {item_name}")

    # Locate item on page
    item_locator = page.locator(SHOPPING_ITEM).filter(has=page.get_by_text(item_name, exact=True))

    if item_locator.count() == 0:
        logger.warning(f"Item '{item_name}' not found on page")
        _safe_track(
            page,
            SHOPPING_ITEM,
            "count",
            False,
            error_message=f"Hunt item '{item_name}' not found",
            locator=item_locator,
        )
        return None

    try:
        # Check exchange button
        exchange_button = item_locator.locator(SHOPPING_ITEM_BUTTON)
        button_text = exchange_button.inner_text()

        if button_text != EXCHANGE_BUTTON_TEXT:
            logger.info(f"Item '{item_name}' not available for exchange (status: {button_text})")
            return None

        # Click exchange
        exchange_button.click()
        logger.info(f"Clicked exchange button for '{item_name}'")

        # Handle exchange dialog and get redemption code
        redeem_code = ShoppingHandler.handle_exchange_dialog(page, item_name)
        if redeem_code:
            logger.info(f"Obtained redemption code for '{item_name}': {redeem_code}")
            logger.info(f"Successfully exchanged '{item_name}'")

        return redeem_code

    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout while exchanging '{item_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error exchanging '{item_name}': {e}")
        return None


def redeem_all_codes(context, codes_to_redeem: List[Tuple[str, str]]):
    """Redeem all collected codes after exchanging.

    Args:
        context: Playwright browser context
        codes_to_redeem: List of tuples (item_name, redeem_code)
    """
    if not codes_to_redeem:
        logger.info("No codes to redeem")
        return

    logger.info(f"Redeeming {len(codes_to_redeem)} codes...")

    for item_name, redeem_code in codes_to_redeem:
        try:
            logger.info(f"Redeeming code for '{item_name}': {redeem_code}")
            redeem_result = RedeemAutofill.run(context, redeem_code, item_name)
            if redeem_result["ok"]:
                logger.info("Redeem confirmed for '%s'", item_name)
            else:
                logger.warning(
                    "Redeem was not confirmed for '%s' (status=%s, detail=%s)",
                    item_name,
                    redeem_result["status"],
                    redeem_result["detail"],
                )
        except Exception as e:
            logger.error(f"Failed to redeem '{item_name}': {e}")

    logger.info("All codes redeemed")


def remove_items_from_hunt_list(item_names: List[str]):
    """Remove successfully hunted items from the hunt list.

    Args:
        item_names: List of item names to remove from hunt list
    """
    if not item_names:
        logger.info("No items to remove from hunt list")
        return

    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)

    if not shopping_data:
        logger.error("No shopping data found")
        return

    hunt_items = shopping_data.get("Hunt", [])
    original_count = len(hunt_items)

    # Remove items
    for item_name in item_names:
        if item_name in hunt_items:
            hunt_items.remove(item_name)
            logger.info(f"Removed '{item_name}' from hunt list")

    shopping_data["Hunt"] = hunt_items

    # Save updated data
    save_shopping_data(file_path, shopping_data)

    removed_count = original_count - len(hunt_items)
    logger.info(f"Removed {removed_count} item(s) from hunt list. Remaining: {len(hunt_items)}")


def run_hunt():
    """Execute hunt mode by waiting at shopping screen and purchasing items when available."""
    # Validate we're running on the correct date
    # (schedule library fires daily, but we only want to run on the target date)
    if _hunt_target_date:
        today = datetime.now().date()
        target_date = _hunt_target_date.date()
        if today != target_date:
            logger.info(
                f"Hunt scheduled for {target_date.strftime('%d/%m/%y')}, "
                f"but today is {today.strftime('%d/%m/%y')}. Skipping until correct date."
            )
            return

    logger.info("Starting hunt mode...")

    # WHY: Settings changes clear future schedules, but an already queued hunt
    # job can still fire once. Guard here so disabling automatic runs prevents
    # any late browser launch.
    if not settings.run_task:
        logger.info("Automatic runs are disabled in settings")
        return

    if not settings.enable_hunt_mode:
        logger.info("Hunt mode is disabled in settings")
        return

    hunt_items = get_hunt_items()
    if not hunt_items:
        logger.info("No items to hunt, skipping")
        return

    # Get next hunt time for logging purposes
    next_hunt_time_str = get_next_hunt_time()
    if next_hunt_time_str:
        logger.info(f"Target item availability time: {next_hunt_time_str}")
    else:
        logger.info("No hunt items with return times, skipping")
        return

    import sentry_sdk

    browser = None
    with sentry_sdk.start_transaction(op="automation.hunt", name="hunt-handler") as tx:
        tx.set_data("workflow.phase", "hunt")
        tx.set_data("hunt.item_count", len(hunt_items))
        try:
            with sync_playwright() as p:
                with sentry_sdk.start_span(op="browser.launch", name="Launch browser"):
                    browser = p.firefox.launch(headless=settings.hide_browser)
                    context_options = build_context_options(CONFIG["STORAGE_PATH"])
                    context = browser.new_context(**context_options)
                    page = context.new_page()

                try:
                    EventNavigator.open_event_page(page)
                    auth_status = EventNavigator.wait_for_authenticated_event_home(
                        page,
                        context="starting hunt mode",
                    )
                    if not auth_status.ready:
                        NotificationHelper.notify(
                            title="ZZZ Bot - Hunt Mode",
                            message="Please log in manually",
                            app_icon=CONFIG["SAD_ICON"],
                        )
                        return

                    # Open shopping screen
                    if not ShoppingHandler.open_shopping_screen(page):
                        logger.error("Failed to open shopping screen for hunt mode")
                        return

                    # Select ZZZ avatar
                    if not ShoppingHandler.select_zzz_avatar(page):
                        logger.error("Cannot proceed with hunting")
                        return

                    # Load shopping data
                    file_path = Path(CONFIG["SHOPPING_FILE"])
                    shopping_data = load_shopping_data(file_path)

                    if not shopping_data:
                        logger.error("No shopping data available for hunting")
                        return

                    # Phase 1: Exchange all items and collect codes
                    logger.info("=" * 50)
                    logger.info("PHASE 1: Exchanging all hunt items...")
                    logger.info("=" * 50)

                    codes_to_redeem = []  # List of (item_name, redeem_code) tuples
                    successful_exchanges = []
                    failed_items = []

                    with sentry_sdk.start_span(
                        op="browser.interact", name="Exchange hunt items"
                    ) as exchange_span:
                        exchange_span.set_data("workflow.phase", "hunt_exchange")
                        exchange_span.set_data("hunt.item_count", len(hunt_items))

                        for item_name in hunt_items:
                            with sentry_sdk.start_span(
                                op="automation.hunt.item", name=f"hunt-item:{item_name}"
                            ) as item_span:
                                item_span.set_data("workflow.phase", "hunt_exchange")
                                item_span.set_data("hunt.item_name", item_name)
                                logger.info("Starting hunt for '%s'", item_name)

                                is_available = wait_for_exchange_button(
                                    page,
                                    item_name,
                                    max_wait_seconds=settings.hunt_poll_max_wait_seconds,
                                    poll_interval_seconds=settings.hunt_poll_interval_seconds,
                                    backoff_enabled=settings.hunt_poll_backoff_enabled,
                                    early_exit_on_unavailable=settings.hunt_early_exit_on_unavailable,
                                )
                                item_span.set_data("hunt.exchange_available", is_available)

                                if is_available:
                                    redeem_code = exchange_item_only(page, item_name)

                                    if redeem_code:
                                        codes_to_redeem.append((item_name, redeem_code))
                                        successful_exchanges.append(item_name)
                                        item_span.set_data("hunt.exchange_result", "success")
                                        logger.info("✓ Successfully exchanged '%s'", item_name)
                                    else:
                                        failed_items.append(item_name)
                                        item_span.set_data(
                                            "hunt.exchange_result", "exchange_failed"
                                        )
                                        logger.warning("✗ Failed to exchange '%s'", item_name)
                                else:
                                    failed_items.append(item_name)
                                    item_span.set_data("hunt.exchange_result", "not_available")
                                    logger.warning("✗ Hunt did not complete for '%s'", item_name)

                                time.sleep(1)

                    logger.info(
                        f"Exchange phase completed: {len(successful_exchanges)} success, {len(failed_items)} failed"
                    )

                    # Phase 2: Redeem all collected codes
                    logger.info("=" * 50)
                    logger.info("PHASE 2: Redeeming all codes...")
                    logger.info("=" * 50)

                    with sentry_sdk.start_span(
                        op="browser.navigate", name="Redeem all codes"
                    ) as redeem_span:
                        redeem_span.set_data("workflow.phase", "hunt_redeem")
                        redeem_span.set_data("hunt.codes_to_redeem", len(codes_to_redeem))
                        if codes_to_redeem:
                            redeem_all_codes(context, codes_to_redeem)
                        else:
                            logger.warning("No codes to redeem")

                    # Phase 3: Remove successful items from hunt list
                    logger.info("=" * 50)
                    logger.info("PHASE 3: Updating hunt list...")
                    logger.info("=" * 50)

                    with sentry_sdk.start_span(
                        op="db.write", name="Update hunt list"
                    ) as update_span:
                        update_span.set_data("workflow.phase", "hunt_cleanup")
                        update_span.set_data("hunt.successful_exchanges", len(successful_exchanges))
                        if successful_exchanges:
                            remove_items_from_hunt_list(successful_exchanges)
                            logger.info(
                                f"Removed {len(successful_exchanges)} item(s) from hunt list"
                            )
                        else:
                            logger.info("No items to remove from hunt list")

                    # Save session state
                    with sentry_sdk.start_span(
                        op="auth.storage_state", name="save_storage_state"
                    ) as save_state_span:
                        save_state_span.set_data("workflow.phase", "hunt_persist_state")
                        save_context_storage_state(context, CONFIG["STORAGE_PATH"])

                    # Send notification
                    message = (
                        f"Hunt completed!\n"
                        f"Exchanged: {len(successful_exchanges)}\n"
                        f"Failed: {len(failed_items)}\n"
                        f"Removed from hunt list: {len(successful_exchanges)}"
                    )
                    NotificationHelper.notify(
                        title="ZZZ Bot - Hunt Mode",
                        message=message,
                        app_icon=(
                            CONFIG["ICON_PATH"] if successful_exchanges else CONFIG["SAD_ICON"]
                        ),
                    )

                    logger.info("=" * 50)
                    logger.info(
                        f"Hunt mode completed: {len(successful_exchanges)} successful, {len(failed_items)} failed"
                    )
                    logger.info(f"Items removed from hunt list: {successful_exchanges}")
                    logger.info("=" * 50)

                    emitted = False
                    with suppress(ImportError, RuntimeError):
                        from core.event_bus import emit

                        emit("task-completed", {"source": "hunt_mode"})
                        emitted = True
                    if not emitted:
                        logger.debug("SSE emit after hunt_mode skipped")

                finally:
                    # Always close browser, even if errors occur
                    if browser:
                        logger.info("Closing hunt mode browser")
                        browser.close()

        except Exception as e:
            tx.set_status("internal_error")
            logger.error(f"Hunt mode failed: {e}", exc_info=True)
            NotificationHelper.notify(
                title="ZZZ Bot - Hunt Mode",
                message=f"Hunt failed: {str(e)}",
                app_icon=CONFIG["SAD_ICON"],
            )
            # Ensure browser is closed in case of exceptions
            if browser:
                with suppress(Exception):
                    browser.close()
