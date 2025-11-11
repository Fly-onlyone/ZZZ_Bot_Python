"""Hunt Mode automation module for ZZZ Bot.

Handles automatic purchasing of specific items when the shop renews.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright, Page, Locator

import NotificationHelper
import RetryHelper
import ShoppingHandler
from DataHandler import load_shopping_data
from GlobalVar import CONFIG, settings
from ImageProcessor import find_correct_avatar
from StringUtil import calculate_return_time

logger = logging.getLogger(__name__)

# Wait buffer time before item becomes available (in seconds)
WAIT_BUFFER_SECONDS = 120  # Open shopping screen 2 minutes early
POLL_INTERVAL_SECONDS = 1  # Check button text every 1 second
EXCHANGE_BUTTON_TEXT = "Exchange"


def get_hunt_items() -> List[str]:
    """Get the list of items marked for hunting.

    Returns:
        List of item names to hunt
    """
    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)

    if not shopping_data:
        logger.warning("No shopping data found")
        return []

    hunt_items = shopping_data.get("Hunt", [])
    logger.info(f"Found {len(hunt_items)} items to hunt: {hunt_items}")
    return hunt_items


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


def wait_for_exchange_button(page: Page, item_name: str, max_wait_seconds: int = 180) -> bool:
    """Wait at shopping screen and monitor item button until 'Exchange' appears.

    Args:
        page: Playwright Page instance
        item_name: Name of the item to monitor
        max_wait_seconds: Maximum time to wait (default 3 minutes)

    Returns:
        True if Exchange button appeared, False if timeout
    """
    logger.info(f"Waiting for '{item_name}' to become available...")

    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait_seconds:
        try:
            # Locate the item on page
            item_locator = page.locator(ShoppingHandler.ITEM_SELECTOR).filter(
                has=page.get_by_text(item_name, exact=True)
            )

            if item_locator.count() == 0:
                logger.warning(f"Item '{item_name}' not found on page")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # Get button text
            button = item_locator.locator(ShoppingHandler.ITEM_BUTTON_SELECTOR)
            button_text = button.inner_text()

            # Log status changes
            if button_text != last_status:
                logger.info(f"Item '{item_name}' button status: {button_text}")
                last_status = button_text

            # Check if Exchange is available
            if button_text == EXCHANGE_BUTTON_TEXT:
                logger.info(f"Exchange button available for '{item_name}'!")
                return True

            # Wait before next check
            time.sleep(POLL_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"Error while monitoring '{item_name}': {e}")
            time.sleep(POLL_INTERVAL_SECONDS)

    logger.warning(f"Timeout waiting for '{item_name}' to become available")
    return False


def run_hunt():
    """Execute hunt mode by waiting at shopping screen and purchasing items when available."""
    logger.info("Starting hunt mode...")

    if not settings.enable_hunt_mode:
        logger.info("Hunt mode is disabled in settings")
        return

    hunt_items = get_hunt_items()
    if not hunt_items:
        logger.info("No items to hunt, skipping")
        return

    # Calculate when to start waiting
    next_hunt_time_str = get_next_hunt_time()
    if not next_hunt_time_str:
        logger.info("No hunt items with return times, skipping")
        return

    try:
        hunt_time = datetime.strptime(next_hunt_time_str, "%H:%M %d/%m/%y")
        wait_start_time = hunt_time - timedelta(seconds=WAIT_BUFFER_SECONDS)
        now = datetime.now()

        # Calculate how long to wait before opening shopping screen
        if wait_start_time > now:
            wait_duration = (wait_start_time - now).total_seconds()
            logger.info(
                f"Waiting {wait_duration:.0f} seconds before opening shopping screen "
                f"(opens at {wait_start_time.strftime('%H:%M:%S')})"
            )
            time.sleep(wait_duration)

    except ValueError as e:
        logger.error(f"Failed to parse hunt time '{next_hunt_time_str}': {e}")
        return

    browser = None
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=settings.hide_browser)
            context_options = (
                {"storage_state": CONFIG["STORAGE_PATH"]}
                if os.path.exists(CONFIG["STORAGE_PATH"])
                else {}
            )
            context = browser.new_context(**context_options)
            page = context.new_page()

            try:
                page.goto(
                    "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?..."
                )

                # Handle manual login if storage path doesn't exist
                if not os.path.exists(CONFIG["STORAGE_PATH"]):
                    NotificationHelper.notify(
                        title="ZZZ Bot - Hunt Mode",
                        message="Please log in manually",
                        app_icon=CONFIG["SAD_ICON"],
                    )
                    return

                # Open shopping screen
                shopping_button = page.get_by_role("img").nth(
                    ShoppingHandler.SHOPPING_BUTTON_SELECTOR
                )
                shopping_screen = page.locator(ShoppingHandler.SHOPPING_SCREEN_SELECTOR)

                if not RetryHelper.retry_until_screen_appears(
                    shopping_screen, shopping_button
                ):
                    logger.error("Failed to open shopping screen")
                    return

                logger.info("Shopping screen opened for hunt mode")

                # Navigate to ZZZ avatar
                zzz_avatar = find_correct_avatar(page)
                if not zzz_avatar:
                    logger.error("ZZZ avatar not found, cannot proceed with hunting")
                    return

                zzz_avatar.click()
                logger.info("Selected ZZZ avatar for hunting")

                # Wait for page to load
                page.wait_for_load_state("networkidle", timeout=5000)

                # Load shopping data
                file_path = Path(CONFIG["SHOPPING_FILE"])
                shopping_data = load_shopping_data(file_path)

                if not shopping_data:
                    logger.error("No shopping data available for hunting")
                    return

                successful_hunts = 0
                failed_hunts = 0

                # Wait and hunt each item
                for item_name in hunt_items:
                    logger.info(f"Starting hunt for '{item_name}'")

                    # Wait for Exchange button to appear
                    if wait_for_exchange_button(page, item_name):
                        # Item is available, attempt purchase
                        item_data = shopping_data.get("Item's list", {}).get(item_name)

                        if item_data:
                            if ShoppingHandler._process_single_item(page, item_name, item_data):
                                successful_hunts += 1
                                logger.info(f"Successfully hunted '{item_name}'")
                            else:
                                failed_hunts += 1
                                logger.warning(f"Failed to hunt '{item_name}'")
                        else:
                            logger.error(f"Item data not found for '{item_name}'")
                            failed_hunts += 1
                    else:
                        logger.warning(f"Hunt timeout for '{item_name}'")
                        failed_hunts += 1

                    # Brief pause between items
                    time.sleep(1)

                # Save session state
                context.storage_state(path=CONFIG["STORAGE_PATH"])

                # Send notification
                message = f"Hunt completed: {successful_hunts} success, {failed_hunts} failed"
                NotificationHelper.notify(
                    title="ZZZ Bot - Hunt Mode",
                    message=message,
                    app_icon=CONFIG["ICON_PATH"] if successful_hunts > 0 else CONFIG["SAD_ICON"],
                )

                logger.info(f"Hunt mode completed: {successful_hunts} successful, {failed_hunts} failed")

            finally:
                # Always close browser, even if errors occur
                if browser:
                    logger.info("Closing hunt mode browser")
                    browser.close()

    except Exception as e:
        logger.error(f"Hunt mode failed: {e}", exc_info=True)
        NotificationHelper.notify(
            title="ZZZ Bot - Hunt Mode",
            message=f"Hunt failed: {str(e)}",
            app_icon=CONFIG["SAD_ICON"],
        )
        # Ensure browser is closed in case of exceptions
        if browser:
            try:
                browser.close()
            except:
                pass  # Browser may already be closed
