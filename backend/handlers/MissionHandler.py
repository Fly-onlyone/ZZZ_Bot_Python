"""Mission automation module for ZZZ Bot.

Handles daily check-ins, mission completion, and reward collection.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from automation import RetryHelper
from automation.ImageProcessor import ImageProcessor, find_correct_avatar
from utils.DataHandler import maintain_mission_data
from utils.screenshot_store import save_locator_screenshot

# Configure logging
logger = logging.getLogger(__name__)

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
AVATAR_SELECTOR = "div.avatarsItemImg-AiUG1h"
TASK_ITEM_SELECTOR = ".taskItemPcLeft-Aetp6m"
CLAIMED_POPUP_TEXT = "Claimed!"

# Timing constants
DIALOG_WAIT_TIMEOUT = 5000
MISSION_CLICK_WAIT = 2000
RETRY_WAIT = 1000

# Status messages
STATUS_SUCCESS = "Login Success"
STATUS_FAILED = "Login Failed"
STATUS_LINK_NOT_OPENED = "Link isn't opened"


def _close_dialog_if_visible(page: Page) -> None:
    """Close any visible dialog popup.

    Args:
        page: Playwright Page instance
    """
    try:
        close_btn = page.locator(DIALOG_CLOSE_SELECTOR)
        if close_btn.is_visible(timeout=1000):
            close_btn.click()
            logger.info("Closed popup dialog")
    except PlaywrightTimeoutError:
        logger.debug("No dialog found to close")
    except Exception as e:
        logger.warning(f"Error closing dialog: {e}")


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
    # Wait for page to be fully loaded instead of fixed timeout
    new_page.wait_for_load_state("networkidle", timeout=10000)

    _close_dialog_if_visible(new_page)

    # Compute current day and locate button
    today = datetime.now().day
    day_text = f"Day {today}"
    logger.info(f"Attempting check-in for {day_text}")

    day_btn = new_page.get_by_text(day_text, exact=True)
    success_msg = new_page.locator(DIALOG_BODY_SELECTOR)

    # Retry until success message appears
    clicked = RetryHelper.retry_until_screen_appears(success_msg, day_btn)

    if clicked:
        logger.info("Check-in successful!")
        todays_data["check_in"] = STATUS_SUCCESS
        asset_id = save_locator_screenshot(success_msg, "login_reward.png")
        logger.info("Saved login reward screenshot to MongoDB asset: %s", asset_id)
    else:
        logger.error("Check-in failed")
        todays_data["check_in"] = STATUS_FAILED


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

    def attach_page_listener(self) -> None:
        """Attach event listener to handle popup pages (e.g., check-in)."""
        self._popup_handler = lambda new_page: handle_pop_up(new_page, self.todays_data)
        self.page.context.on("page", self._popup_handler)

    def detach_page_listener(self) -> None:
        """Remove the popup event listener to prevent interference with other handlers."""
        if self._popup_handler:
            self.page.context.remove_listener("page", self._popup_handler)
            self._popup_handler = None
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

                # Check for success popup
                claimed_popup = self.page.locator(f"text={CLAIMED_POPUP_TEXT}")
                if claimed_popup.is_visible(timeout=2000):
                    logger.info("Mission reward claimed successfully")
                    return True

            except PlaywrightTimeoutError:
                logger.warning(f"Mission button not enabled on attempt {attempt}")
            except Exception as e:
                logger.error(f"Error performing mission (attempt {attempt}): {e}")

            if attempt < max_retries:
                self.page.wait_for_timeout(RETRY_WAIT)

        logger.error("Unable to complete mission after maximum retries")
        return False


def handle_pop_up(new_page: Page, todays_data: Dict) -> None:
    """Handle popup pages, specifically check-in dialogs.

    Args:
        new_page: Newly opened page
        todays_data: Dictionary to store mission results
    """
    try:
        if CHECK_IN_URL in new_page.url:
            logger.info("Check-in popup detected")
            handle_check_in(new_page, todays_data)
        else:
            logger.info(f"Closing unrelated popup: {new_page.url}")
    finally:
        new_page.close()


def open_mission_screen(page: Page) -> bool:
    """Navigate to the mission screen.

    Args:
        page: Playwright Page instance

    Returns:
        True if mission screen opened successfully, False otherwise
    """
    logger.info("Opening mission screen...")
    target_screen = page.locator(MISSION_WRAPPER_SELECTOR)
    mission_button = page.locator(f"text={MISSION_BUTTON_TEXT}")

    success = RetryHelper.retry_until_screen_appears(target_screen, mission_button)
    if success:
        logger.info("Mission screen opened successfully")
    else:
        logger.error("Failed to open mission screen")
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
    listener_attached = False

    for idx in range(1, mission_count + 1):
        logger.info(f"Processing mission {idx}/{mission_count}")

        # Locate mission elements
        mission_text_loc = page.locator(
            f"div:nth-child({idx}) > {TASK_ITEM_SELECTOR} > .top-ohhwaM"
        )
        mission_btn_loc = page.locator(
            f"div:nth-child({idx}) > .taskItemPcRight-3-Kwr1 > .icon2-Y7R3Mu"
        )

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
            # Attach listener for first mission to handle check-in popup
            if idx == 1 and not listener_attached:
                mission_handler.attach_page_listener()
                listener_attached = True

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


def run(output_file: str, page: Page, previous_data: Dict, todays_data: Dict) -> None:
    """Main entry point for mission automation.

    Args:
        output_file: Path to save mission data
        page: Playwright Page instance
        previous_data: Historical mission data
        todays_data: Today's mission data to populate
    """
    logger.info("Starting mission automation...")

    try:
        # Navigate to mission screen
        if not open_mission_screen(page):
            logger.error("Failed to open mission screen, aborting")
            return

        # Count and execute missions
        mission_count = count_mission(page)
        doing_mission(mission_count, page, todays_data)

        # Save mission data
        maintain_mission_data(previous_data, output_file, todays_data)
        logger.info("Mission automation completed successfully")

    except Exception as e:
        logger.error(f"Mission automation failed: {e}", exc_info=True)
        raise
