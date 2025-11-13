"""Hunt Mode automation module for ZZZ Bot.

Handles automatic purchasing of specific items when the shop renews.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError

import NotificationHelper
import RedeemAutofill
import RetryHelper
import ShoppingHandler
from DataHandler import load_shopping_data, save_shopping_data
from GlobalVar import CONFIG, settings
from ImageProcessor import find_correct_avatar
from StringUtil import calculate_return_time

logger = logging.getLogger(__name__)

# Wait buffer time before item becomes available (in seconds)
WAIT_BUFFER_SECONDS = 120  # Open shopping screen 2 minutes early
POLL_INTERVAL_SECONDS = 1  # Check button text every 1 second
EXCHANGE_BUTTON_TEXT = "Exchange"


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
    item_locator = page.locator(ShoppingHandler.ITEM_SELECTOR).filter(
        has=page.get_by_text(item_name, exact=True)
    )

    if item_locator.count() == 0:
        logger.warning(f"Item '{item_name}' not found on page")
        return None

    try:
        # Check exchange button
        exchange_button = item_locator.locator(ShoppingHandler.ITEM_BUTTON_SELECTOR)
        button_text = exchange_button.inner_text()

        if button_text != EXCHANGE_BUTTON_TEXT:
            logger.info(
                f"Item '{item_name}' not available for exchange (status: {button_text})"
            )
            return None

        # Click exchange
        exchange_button.click()
        logger.info(f"Clicked exchange button for '{item_name}'")

        # Wait for and handle confirmation dialog
        confirm_dialog = page.locator(ShoppingHandler.CONFIRM_DIALOG_SELECTOR)

        if not confirm_dialog.is_visible(timeout=5000):
            logger.warning("Confirmation dialog did not appear")
            return None

        logger.info("Confirmation dialog detected")
        confirm_ok_button = page.locator(ShoppingHandler.CONFIRM_OK_SELECTOR)
        confirm_ok_button.click()

        # Extract redemption code
        code_element = page.locator(ShoppingHandler.REDEEM_CODE_SELECTOR)
        code_element.wait_for(state="visible", timeout=5000)
        redeem_code = code_element.inner_text()

        # Copy code to clipboard
        copy_button = page.locator(ShoppingHandler.COPY_BUTTON_SELECTOR)
        copy_button.click()
        logger.info(f"Obtained redemption code for '{item_name}': {redeem_code}")

        # Close dialog
        close_button = page.locator(ShoppingHandler.CLOSE_BUTTON_SELECTOR)
        close_button.click()
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
            RedeemAutofill.run(context, redeem_code, item_name)
            logger.info(f"Successfully redeemed '{item_name}'")
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
    logger.info("Starting hunt mode...")

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

                # Phase 1: Exchange all items and collect codes
                logger.info("=" * 50)
                logger.info("PHASE 1: Exchanging all hunt items...")
                logger.info("=" * 50)

                codes_to_redeem = []  # List of (item_name, redeem_code) tuples
                successful_exchanges = []
                failed_items = []

                for item_name in hunt_items:
                    logger.info(f"Starting hunt for '{item_name}'")

                    # Wait for Exchange button to appear
                    if wait_for_exchange_button(page, item_name):
                        # Item is available, attempt exchange
                        redeem_code = exchange_item_only(page, item_name)

                        if redeem_code:
                            codes_to_redeem.append((item_name, redeem_code))
                            successful_exchanges.append(item_name)
                            logger.info(f"✓ Successfully exchanged '{item_name}'")
                        else:
                            failed_items.append(item_name)
                            logger.warning(f"✗ Failed to exchange '{item_name}'")
                    else:
                        failed_items.append(item_name)
                        logger.warning(f"✗ Hunt timeout for '{item_name}'")

                    # Brief pause between exchanges
                    time.sleep(1)

                logger.info(f"Exchange phase completed: {len(successful_exchanges)} success, {len(failed_items)} failed")

                # Phase 2: Redeem all collected codes
                logger.info("=" * 50)
                logger.info("PHASE 2: Redeeming all codes...")
                logger.info("=" * 50)

                if codes_to_redeem:
                    redeem_all_codes(context, codes_to_redeem)
                else:
                    logger.warning("No codes to redeem")

                # Phase 3: Remove successful items from hunt list
                logger.info("=" * 50)
                logger.info("PHASE 3: Updating hunt list...")
                logger.info("=" * 50)

                if successful_exchanges:
                    remove_items_from_hunt_list(successful_exchanges)
                    logger.info(f"Removed {len(successful_exchanges)} item(s) from hunt list")
                else:
                    logger.info("No items to remove from hunt list")

                # Save session state
                context.storage_state(path=CONFIG["STORAGE_PATH"])

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
                    app_icon=CONFIG["ICON_PATH"] if successful_exchanges else CONFIG["SAD_ICON"],
                )

                logger.info("=" * 50)
                logger.info(f"Hunt mode completed: {len(successful_exchanges)} successful, {len(failed_items)} failed")
                logger.info(f"Items removed from hunt list: {successful_exchanges}")
                logger.info("=" * 50)

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
