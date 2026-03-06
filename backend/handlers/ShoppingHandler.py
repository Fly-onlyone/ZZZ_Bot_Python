"""Shopping automation module for ZZZ Bot.

Handles shopping item gathering, exchange, and redemption code automation.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from automation import RedeemAutofill, RetryHelper
from automation.ImageProcessor import find_correct_avatar
from automation.Selectors import (
    AVATAR_SELECTOR,
    SHOPPING_SCREEN,
    SHOPPING_CURRENT_POINTS,
    SHOPPING_ITEM,
    SHOPPING_ITEM_NAME,
    SHOPPING_ITEM_PRICE,
    SHOPPING_ITEM_BUTTON,
    SHOPPING_ITEM_COUNT,
    SHOPPING_DURATION,
    SHOPPING_CONFIRM_DIALOG,
    SHOPPING_CONFIRM_OK,
    SHOPPING_REDEEM_CODE,
    SHOPPING_COPY_BUTTON,
    SHOPPING_CLOSE_BUTTON,
)
from core.GlobalVar import CONFIG, settings
from utils.DataHandler import load_shopping_data, save_shopping_data
from utils.StringUtil import (
    extract_number_from_string,
    extract_and_convert_duration,
    calculate_return_time,
)
from . import HuntModeHandler as HuntMode

logger = logging.getLogger(__name__)

# Constants
SHOPPING_BUTTON_SELECTOR = 1  # nth image role for shopping button
TIME_PATTERN = re.compile(r"^\d+:\d{2}:\d{2}$")  # Allow any number of digits for hours
EXCHANGE_BUTTON_TEXT = "Exchange"
SHOPPING_OPEN_RETRY_WAIT = 1000
SHOPPING_OPEN_MAX_RETRIES = 5
SHOPPING_MODAL_CLOSE_TIMEOUT = 2000


# ===== UTILITY FUNCTIONS =====


def open_shopping_screen(page: Page) -> bool:
    """Open the shopping screen and return success status.

    Args:
        page: Playwright Page instance

    Returns:
        True if shopping screen opened successfully, False otherwise
    """
    def _shopping_ready() -> bool:
        duration = page.locator(SHOPPING_DURATION)
        points = page.locator(SHOPPING_CURRENT_POINTS)
        avatars = page.locator(AVATAR_SELECTOR)

        try:
            if duration.count() > 0 and duration.first.is_visible(timeout=1000):
                return True
        except Exception:
            pass

        try:
            return (
                points.count() > 0
                and avatars.count() > 0
                and points.first.is_visible(timeout=1000)
                and avatars.first.is_visible(timeout=1000)
            )
        except Exception:
            return False

    def _close_blocking_reward_dialog() -> None:
        close_button = page.locator(SHOPPING_CLOSE_BUTTON).first
        try:
            if close_button.count() > 0 and close_button.is_visible(timeout=1000):
                logger.info("Closing lingering reward dialog before opening shopping")
                close_button.click(force=True, timeout=SHOPPING_MODAL_CLOSE_TIMEOUT)
                page.wait_for_timeout(500)
        except Exception as close_error:
            logger.debug("No blocking reward dialog to close: %s", close_error)

    if _shopping_ready():
        logger.info("Shopping screen already open")
        return True

    shopping_button = page.get_by_role("img").nth(SHOPPING_BUTTON_SELECTOR)

    for attempt in range(1, SHOPPING_OPEN_MAX_RETRIES + 1):
        _close_blocking_reward_dialog()

        try:
            shopping_button.click(force=True, timeout=5000)
            page.wait_for_timeout(SHOPPING_OPEN_RETRY_WAIT)
        except Exception as exc:
            logger.warning(
                "Shopping button click failed on attempt %s/%s: %s",
                attempt,
                SHOPPING_OPEN_MAX_RETRIES,
                exc,
            )

        if _shopping_ready():
            logger.info("Shopping screen opened")
            return True

        try:
            page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass

        if _shopping_ready():
            logger.info("Shopping screen opened")
            return True

    logger.error("Failed to open shopping screen")
    logger.error(
        "Shopping diagnostics: wrapper_count=%s, duration_count=%s, point_count=%s, avatar_count=%s, image_count=%s",
        page.locator(SHOPPING_SCREEN).count(),
        page.locator(SHOPPING_DURATION).count(),
        page.locator(SHOPPING_CURRENT_POINTS).count(),
        page.locator(AVATAR_SELECTOR).count(),
        page.get_by_role("img").count(),
    )
    return False


def select_zzz_avatar(page: Page) -> bool:
    """Select the ZZZ avatar and wait for page load.

    Args:
        page: Playwright Page instance

    Returns:
        True if avatar selected successfully, False otherwise
    """
    zzz_avatar = find_correct_avatar(page)
    if not zzz_avatar:
        logger.error("ZZZ avatar not found")
        return False

    zzz_avatar.click()
    logger.info("Selected ZZZ avatar")
    # Wait for DOM to be loaded instead of networkidle for more reliability
    # networkidle can timeout on pages with continuous network activity
    page.wait_for_load_state("domcontentloaded", timeout=10000)
    # Add a small delay to ensure content is rendered
    page.wait_for_timeout(1000)
    return True


def load_or_gather_shopping_data(page: Page, current_points: int) -> Dict:
    """Load existing shopping data or gather fresh data based on duration.

    Args:
        page: Playwright Page instance
        current_points: Current point balance

    Returns:
        Shopping data dictionary
    """
    file_path = Path(CONFIG["SHOPPING_FILE"])
    existing_data = load_shopping_data(file_path)

    if existing_data:
        duration = existing_data.get("Duration", {})
        if is_current_time_in_duration(duration):
            logger.info("Current time within event duration, updating existing data")
            # Gather new data
            new_data = gather_data(page, current_points)

            # Merge Purchased lists (keep old + add new)
            old_purchased = set(existing_data.get("Purchased", []))
            new_purchased = set(new_data.get("Purchased", []))
            merged_purchased = list(old_purchased | new_purchased)

            # Update existing data with new data
            existing_data.update(new_data)
            existing_data["Purchased"] = merged_purchased
            shopping_data = existing_data

            logger.debug(f"Merged purchased list: {merged_purchased}")
        else:
            logger.info("Event duration expired, gathering fresh data")
            shopping_data = gather_data(page, current_points)
    else:
        logger.info("No existing data found, gathering fresh data")
        shopping_data = gather_data(page, current_points)

    return shopping_data


def handle_exchange_dialog(page: Page, item_name: str) -> Optional[str]:
    """Handle the exchange confirmation dialog and return redemption code.

    Args:
        page: Playwright Page instance
        item_name: Name of the item being exchanged

    Returns:
        Redemption code if successful, None if failed
    """
    try:
        # Wait for and handle confirmation dialog
        confirm_dialog = page.locator(SHOPPING_CONFIRM_DIALOG)

        if not confirm_dialog.is_visible(timeout=5000):
            logger.warning("Confirmation dialog did not appear")
            return None

        logger.info("Confirmation dialog detected")
        confirm_ok_button = page.locator(SHOPPING_CONFIRM_OK)
        confirm_ok_button.click()

        # Extract redemption code
        code_element = page.locator(SHOPPING_REDEEM_CODE)
        code_element.wait_for(state="visible", timeout=5000)
        redeem_code = code_element.inner_text()

        # Copy code to clipboard
        copy_button = page.locator(SHOPPING_COPY_BUTTON)
        copy_button.click()
        logger.info(f"Copied redemption code for '{item_name}'")

        # Close dialog
        close_button = page.locator(SHOPPING_CLOSE_BUTTON)
        close_button.click()
        logger.info(f"Closed exchange dialog for '{item_name}'")

        return redeem_code

    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout while handling dialog for '{item_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error handling dialog for '{item_name}': {e}")
        return None


# ===== END UTILITY FUNCTIONS =====


def is_current_time_in_duration(duration: Dict[str, str]) -> bool:
    """Check if current time is within the shopping event duration.

    Args:
        duration: Dictionary with 'Start' and 'End' dates in '%d/%m' format

    Returns:
        True if current time is within duration, False otherwise
    """
    try:
        start_str = duration.get("Start", "")
        end_str = duration.get("End", "")

        if not start_str or not end_str:
            logger.warning("Missing start or end date in duration")
            return False

        # Parse dates and set current year
        current_year = datetime.now().year
        start_date = datetime.strptime(start_str, "%d/%m").replace(year=current_year)
        end_date = datetime.strptime(end_str, "%d/%m").replace(year=current_year)
        current_time = datetime.now()

        # Check if within range
        is_within = start_date <= current_time <= end_date
        logger.info(
            f"Duration check: {start_date.date()} to {end_date.date()}, "
            f"Current: {current_time.date()}, Within: {is_within}"
        )
        return is_within

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid duration format: {e}")
        return False


def _extract_item_availability(item_locator: Locator) -> tuple[int, str]:
    """Extract item inventory and availability status.

    Args:
        item_locator: Locator for the item element

    Returns:
        Tuple of (inventory_count, availability_status)
    """
    button_text = item_locator.locator(SHOPPING_ITEM_BUTTON).inner_text()

    # Check if button shows countdown timer
    if TIME_PATTERN.match(button_text):
        return_time = calculate_return_time(button_text)
        logger.debug(f"Item on cooldown, returns at: {return_time}")
        return 0, return_time
    else:
        # Item is available, get inventory count
        inventory_text = item_locator.locator(SHOPPING_ITEM_COUNT).inner_text()
        inventory = extract_number_from_string(inventory_text)
        return inventory, button_text


def check_and_process_item(item_locator: Locator) -> Dict[str, any]:
    """Process a single shopping item and extract its data.

    Args:
        item_locator: Locator for the item element

    Returns:
        Dictionary containing item data (Name, Price, Inventory, Available)
    """
    try:
        # Extract item name
        item_name = item_locator.locator(SHOPPING_ITEM_NAME).inner_text()

        # Extract and parse price
        price_text = item_locator.locator(SHOPPING_ITEM_PRICE).inner_text()
        item_price = int(price_text.replace(",", ""))

        # Extract availability
        inventory, availability = _extract_item_availability(item_locator)

        item_data = {
            "Name": item_name,
            "Price": item_price,
            "Inventory": inventory,
            "Available": availability,
        }

        logger.debug(
            f"Processed item: {item_name}, Price: {item_price}, "
            f"Inventory: {inventory}, Status: {availability}"
        )
        return item_data

    except Exception as e:
        logger.error(f"Error processing item: {e}")
        raise


def _extract_current_points(page: Page) -> int:
    """Extract current points from the shopping page.

    NOTE: This should be called AFTER clicking the game avatar,
    as the points element shows 0 before a game is selected.

    Args:
        page: Playwright Page instance

    Returns:
        Current point balance

    Raises:
        ValueError: If points cannot be extracted
    """
    logger.info("Extracting current points...")
    point_text = ""

    try:
        point_element = page.locator(SHOPPING_CURRENT_POINTS)

        # Wait for element to be visible and have content
        point_element.wait_for(state="visible", timeout=5000)
        # Wait for non-empty text content instead of fixed timeout
        page.wait_for_function(
            f"document.querySelector('{SHOPPING_CURRENT_POINTS}')?.innerText?.trim().length > 0",
            timeout=5000,
        )

        # Get the text content
        point_text = point_element.inner_text()
        logger.debug(f"Raw point text extracted: '{point_text}'")

        # Validate we got something
        if not point_text or len(point_text.strip()) == 0:
            logger.error("Point element found but text is empty")
            raise ValueError("Point element has no text content")

        # Remove first character (usually a bullet or currency symbol)
        # Original working logic: point_text[1:]
        point_text_cleaned = point_text[1:].strip()
        logger.debug(f"After removing first char: '{point_text_cleaned}'")

        # Parse to integer (remove commas if any)
        current_point = int(point_text_cleaned.replace(",", ""))
        logger.info(f"Current points: {current_point}")
        return current_point

    except (ValueError, AttributeError, IndexError) as e:
        logger.error(f"Failed to extract points: {e}")
        logger.error(f"Point text was: '{point_text or 'N/A'}'")
        raise ValueError(
            f"Could not parse point balance from element {SHOPPING_CURRENT_POINTS}"
        ) from e


def gather_data(page: Page, point: int) -> Dict:
    """Gather all shopping item data from the page.

    Args:
        page: Playwright Page instance
        point: Current point balance

    Returns:
        Dictionary containing shopping data with items, duration, and points
    """
    logger.info("Gathering shopping item data...")
    items = {}
    purchased_items = []  # Track items with "Limit Reached" status

    # Count and process all items
    item_locators = page.locator(SHOPPING_ITEM)
    item_count = RetryHelper.retry_until_non_zero_count(item_locators)

    if item_count == 0:
        logger.warning("No shopping items found")
        return {"Point": point, "Duration": {}, "Item's list": {}, "Purchased": []}

    logger.info(f"Processing {item_count} items...")

    for i in range(item_count):
        try:
            item_locator = item_locators.nth(i)
            item_data = check_and_process_item(item_locator)
            item_name = item_data["Name"]

            # Check for duplicates
            if item_name in items:
                logger.warning(f"Duplicate item detected: {item_name}, skipping")
                continue

            items[item_name] = item_data

            # Track items that have already been purchased (Limit Reached)
            if item_data.get("Available") == "Limit Reached":
                purchased_items.append(item_name)
                logger.debug(f"Item '{item_name}' marked as purchased (Limit Reached)")

        except Exception as e:
            logger.error(f"Error processing item {i + 1}: {e}")
            continue

    # Extract event duration
    try:
        duration_text = page.locator(SHOPPING_DURATION).inner_text()
        duration = extract_and_convert_duration(duration_text)
        logger.info(f"Event duration: {duration}")
    except Exception as e:
        logger.warning(f"Could not extract duration: {e}")
        duration = {}

    shopping_data = {
        "Point": point,
        "Duration": duration,
        "Item's list": items,
        "Purchased": purchased_items,
    }

    logger.info(f"Gathered data for {len(items)} items")
    if purchased_items:
        logger.info(
            f"Detected {len(purchased_items)} already purchased items: {purchased_items}"
        )
    return shopping_data


def run(page: Page) -> None:
    """Main entry point for shopping automation.

    Args:
        page: Playwright Page instance
    """
    import sentry_sdk

    logger.info("Starting shopping automation...")

    with sentry_sdk.start_span(op="automation.shopping", name="shopping-handler") as span:
        span.set_data("workflow.phase", "shopping")
        try:
            # Open shopping screen
            with sentry_sdk.start_span(op="browser.navigate", name="Open shopping screen"):
                if not open_shopping_screen(page):
                    return

            # Select ZZZ avatar
            with sentry_sdk.start_span(op="browser.navigate", name="Select ZZZ avatar"):
                if not select_zzz_avatar(page):
                    logger.error("Cannot proceed with shopping")
                    return

            # Extract current points after selecting the game
            with sentry_sdk.start_span(op="browser.interact", name="Gather shopping data"):
                current_points = _extract_current_points(page)
                shopping_data = load_or_gather_shopping_data(page, current_points)

            # Save data
            with sentry_sdk.start_span(op="db.write", name="Save shopping data"):
                file_path = Path(CONFIG["SHOPPING_FILE"])
                save_shopping_data(file_path, shopping_data)
                shopping_data = load_shopping_data(file_path)

            # Execute shopping if enabled
            if settings.exchange_good:
                with sentry_sdk.start_span(op="browser.interact", name="Run shopping exchanges"):
                    run_shopping(page, shopping_data)
            else:
                logger.info("Shopping disabled in settings, skipping redemption")

            logger.info("Shopping automation completed successfully")

        except Exception as e:
            span.set_status("internal_error")
            logger.error(f"Shopping automation failed: {e}", exc_info=True)
            raise


def _process_single_item(page: Page, item_name: str, item_data: Dict) -> bool:
    """Process exchange for a single shopping item.

    Args:
        page: Playwright Page instance
        item_name: Name of the item to exchange
        item_data: Item data dictionary

    Returns:
        True if exchange was successful, False otherwise
    """
    logger.info(f"Processing item: {item_name}")

    # Locate item on page
    item_locator = page.locator(SHOPPING_ITEM).filter(
        has=page.get_by_text(item_name, exact=True)
    )

    if item_locator.count() == 0:
        logger.warning(f"Item '{item_name}' not found on page, skipping")
        return False

    # Check exchange button
    try:
        exchange_button = item_locator.locator(SHOPPING_ITEM_BUTTON)
        button_text = exchange_button.inner_text()

        if button_text != EXCHANGE_BUTTON_TEXT:
            logger.info(
                f"Item '{item_name}' not available for exchange (status: {button_text})"
            )
            return False

        # Click exchange
        exchange_button.click()
        logger.info(f"Clicked exchange button for '{item_name}'")

        # Handle exchange dialog and get redemption code
        redeem_code = handle_exchange_dialog(page, item_name)
        if not redeem_code:
            return False

        # Brief pause to ensure dialog is fully closed
        page.wait_for_timeout(500)

        # Autofill and redeem (after dialog is closed)
        RedeemAutofill.run(page.context, redeem_code, item_name)
        logger.info(f"Successfully exchanged and redeemed '{item_name}'")

        return True

    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout while exchanging '{item_name}': {e}")
        return False
    except Exception as e:
        logger.error(f"Error exchanging '{item_name}': {e}")
        return False


def run_shopping(page: Page, shopping_data: Dict) -> None:
    """Execute shopping exchanges for selected items.

    Args:
        page: Playwright Page instance
        shopping_data: Shopping data containing selected items
    """
    logger.info("Starting shopping exchange process...")

    selected_items = shopping_data.get("Selected", [])
    purchased_items = shopping_data.get("Purchased", [])

    if not selected_items:
        logger.info("No items selected for exchange")
        return

    # Determine items to process based on settings
    items_to_process = selected_items if settings.buy_all else [selected_items[0]]
    logger.info(
        f"Processing {len(items_to_process)} item(s) " f"(buy_all: {settings.buy_all})"
    )

    successful_exchanges = 0
    failed_exchanges = 0
    successful_items = []  # Track successfully exchanged items

    for item_name in items_to_process:
        # Find item data
        item_data = next(
            (
                item
                for item in shopping_data["Item's list"].values()
                if item["Name"] == item_name
            ),
            None,
        )

        if not item_data:
            logger.warning(f"Item '{item_name}' not found in shopping data, skipping")
            failed_exchanges += 1
            # Only stop if item is not already purchased
            if settings.stop_on_failed_exchange and item_name not in purchased_items:
                logger.info(
                    "stop_on_failed_exchange enabled and item not previously purchased, stopping shopping"
                )
                break
            elif item_name in purchased_items:
                logger.info(f"Item '{item_name}' already purchased, ignoring failure")
            continue

        # Process exchange
        if _process_single_item(page, item_name, item_data):
            successful_exchanges += 1
            successful_items.append(item_name)
        else:
            failed_exchanges += 1
            # Only stop if item is not already purchased
            if settings.stop_on_failed_exchange and item_name not in purchased_items:
                logger.info(
                    "stop_on_failed_exchange enabled and item not previously purchased, stopping shopping"
                )
                break
            elif item_name in purchased_items:
                logger.info(f"Item '{item_name}' already purchased, ignoring failure")

        # Brief pause between exchanges
        page.wait_for_timeout(1000)

    logger.info(
        f"Shopping exchange completed: {successful_exchanges} successful, "
        f"{failed_exchanges} failed"
    )

    # Update Purchased list and save
    if successful_items:
        # Add successful items to purchased list
        updated_purchased = list(set(purchased_items) | set(successful_items))
        shopping_data["Purchased"] = updated_purchased

        # Save updated shopping data
        file_path = Path(CONFIG["SHOPPING_FILE"])
        save_shopping_data(file_path, shopping_data)
        logger.info(f"Added {len(successful_items)} items to purchased list")

        # Remove successfully purchased items from hunt list
        HuntMode.remove_items_from_hunt_list(successful_items)


def execute_shopping_with_existing_data(page: Page) -> bool:
    """Execute shopping with existing data (before draw).

    Opens shopping screen, loads existing data, executes exchanges if enabled.

    Args:
        page: Playwright Page instance

    Returns:
        True if shopping screen was closed successfully, False otherwise
    """
    import sentry_sdk

    logger.info("Starting shopping execution phase (before draw)...")

    with sentry_sdk.start_span(op="automation.shopping", name="shopping-execute") as span:
        span.set_data("workflow.phase", "shopping_execute")
        try:
            # Open shopping screen
            with sentry_sdk.start_span(op="browser.navigate", name="Open shopping screen"):
                if not open_shopping_screen(page):
                    logger.error("Failed to open shopping screen for execution")
                    return False

            # Select ZZZ avatar
            with sentry_sdk.start_span(op="browser.navigate", name="Select ZZZ avatar"):
                if not select_zzz_avatar(page):
                    return False

            # Load existing shopping data
            file_path = Path(CONFIG["SHOPPING_FILE"])
            shopping_data = load_shopping_data(file_path)

            if not shopping_data:
                logger.warning("No existing shopping data found, skipping execution")
                return True  # Not an error, just no data

            # Execute shopping if enabled
            if settings.exchange_good:
                with sentry_sdk.start_span(op="browser.interact", name="Execute shopping exchanges"):
                    run_shopping(page, shopping_data)
            else:
                logger.info("Shopping execution disabled in settings")

            logger.info("Shopping execution phase completed")
            return True

        except Exception as e:
            span.set_status("internal_error")
            logger.error(f"Shopping execution phase failed: {e}", exc_info=True)
            return False


def gather_shopping_data_only(page: Page) -> bool:
    """Gather shopping data only (after draw).

    Opens shopping screen, gathers new data, saves it.

    Args:
        page: Playwright Page instance

    Returns:
        True if successful, False otherwise
    """
    import sentry_sdk

    logger.info("Starting shopping data gathering phase (after draw)...")

    with sentry_sdk.start_span(op="automation.shopping", name="shopping-gather") as span:
        span.set_data("workflow.phase", "shopping_gather")
        try:
            # Open shopping screen
            with sentry_sdk.start_span(op="browser.navigate", name="Open shopping screen"):
                if not open_shopping_screen(page):
                    logger.error("Failed to open shopping screen for data gathering")
                    return False

            # Select ZZZ avatar
            with sentry_sdk.start_span(op="browser.navigate", name="Select ZZZ avatar"):
                if not select_zzz_avatar(page):
                    return False

            # Extract current points and gather data
            with sentry_sdk.start_span(op="browser.interact", name="Gather shopping data"):
                current_points = _extract_current_points(page)
                shopping_data = load_or_gather_shopping_data(page, current_points)

            # Save data
            with sentry_sdk.start_span(op="db.write", name="Save shopping data"):
                file_path = Path(CONFIG["SHOPPING_FILE"])
                save_shopping_data(file_path, shopping_data)

            logger.info("Shopping data gathering phase completed")

            # Note: Hunt tasks will be rescheduled by Bot.py after this function returns
            return True

        except Exception as e:
            span.set_status("internal_error")
            logger.error(f"Shopping data gathering phase failed: {e}", exc_info=True)
            return False
