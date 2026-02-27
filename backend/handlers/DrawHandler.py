"""Prize draw automation module for ZZZ Bot.

Handles automated prize draws, reward detection, and redemption code processing.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator

from automation import RedeemAutofill, RetryHelper
from automation.ImageProcessor import find_correct_lottery_logo, detect_reward
from core.GlobalVar import CONFIG, resource_path, is_exe
from utils import NotificationHelper
from utils.screenshot_store import save_page_screenshot
from utils.StringUtil import extract_price, extract_number

logger = logging.getLogger(__name__)

# Selector constants
DRAW_BUTTON_INDEX = 2  # nth image role
SCREEN_SELECTOR = ".panelTitle-6aEu3I"
SCREEN_TEXT = "Prize Draw"
POINT_VALUE_SELECTOR = ".lotteryPointValue-qM8enE"
DRAW_COST_SELECTOR = ".lotteryCost-D-QGTv"
DRAW_LIMIT_SELECTOR = ".lotteryLimitCount-fqLQOi"
DRAW_BUTTON_SELECTOR = ".lotteryBtnCover-xI-MlR"
SUCCESS_DIALOG_TEXT = "Congratulations, you've"
REWARD_IMAGE_SELECTOR = ".gainPrizeImage-FqEqMM"
REWARD_IMAGE_SELECTOR_ALT = (
    ".gainPrizeImage-FqEqMM img"  # Alternative: img inside container
)
SUCCESS_DIALOG_SELECTOR = ".customModal-JTvCMP"  # Container for success dialog
REDEEM_CODE_SELECTOR = "div.gainCodeCopyInput-QcgdvD"  # More specific with tag
REDEEM_CODE_SELECTOR_ALT = ".gainCodeCopyInput-QcgdvD"  # Fallback selector
CLOSE_DIALOG_SELECTOR = ".gainClose-7Q0hz8"

# Timing constants
DRAW_RESULT_WAIT = 5000
CLOSE_DIALOG_TIMEOUT = 2000
REDEEM_CODE_WAIT = 3000  # Wait for redemption code element

# Reward constants
UNKNOWN_REWARD = "Unknown reward"


def _find_reward_image(page: Page, draw_number: int) -> Optional[Locator]:
    """Find the reward image element using multiple selectors with escalating timeouts.

    Args:
        page: Playwright Page instance
        draw_number: Current draw number for logging

    Returns:
        Locator for the reward image if found, None otherwise
    """
    # Try multiple selectors in order of preference
    selectors_to_try = [
        REWARD_IMAGE_SELECTOR,
        REWARD_IMAGE_SELECTOR_ALT,
        f"{SUCCESS_DIALOG_SELECTOR} img",  # Any img in success dialog
    ]

    # Escalating timeouts: 3s → 5s → 8s to handle animation + CDN load delays
    timeouts = [3000, 5000, 8000]

    for selector_idx, selector in enumerate(selectors_to_try):
        timeout = timeouts[min(selector_idx, len(timeouts) - 1)]
        try:
            reward_image = page.locator(selector)

            # Wait for element with escalating timeout
            if reward_image.count() > 0:
                # Element exists, wait for it to be visible
                try:
                    reward_image.first.wait_for(state="visible", timeout=timeout)
                    logger.debug(
                        f"Draw {draw_number}: Found reward image with selector '{selector}' (timeout={timeout}ms)"
                    )
                    return reward_image.first
                except PlaywrightTimeoutError:
                    logger.debug(
                        f"Draw {draw_number}: Reward image exists but not visible with selector '{selector}' after {timeout}ms"
                    )
                    # Continue to next selector
                    continue
            else:
                logger.debug(
                    f"Draw {draw_number}: No reward image found with selector '{selector}'"
                )
                # Try next selector
                continue

        except Exception as e:
            logger.debug(f"Draw {draw_number}: Error with selector '{selector}': {e}")
            continue

    logger.warning(
        f"Draw {draw_number}: Could not find reward image after trying all selectors with escalating timeouts"
    )
    return None


def _save_debug_artifacts(page: Page, draw_number: int) -> None:
    """Save screenshot and DOM snapshot for debugging reward detection failures."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if is_exe:
        error_dir = resource_path("logs/errors", outside_path=True)
    else:
        error_dir = "backend/logs/errors"
    os.makedirs(error_dir, exist_ok=True)

    # Screenshot
    screenshot_name = f"draw_{draw_number}_{timestamp}.png"
    try:
        asset_id = save_page_screenshot(page, screenshot_name)
        logger.info("Debug screenshot saved to MongoDB asset: %s", asset_id)
    except Exception as e:
        logger.error(f"Failed to save debug screenshot: {e}")

    # DOM snapshot
    dom_path = os.path.join(error_dir, f"draw_{draw_number}_{timestamp}_dom.html")
    try:
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        logger.info(f"Debug DOM snapshot saved: {dom_path}")
    except Exception as e:
        logger.error(f"Failed to save DOM snapshot: {e}")


def _extract_redemption_code(page: Page, draw_number: int) -> Optional[str]:
    """Extract redemption code from the reward dialog.

    Args:
        page: Playwright Page instance
        draw_number: Current draw number for logging

    Returns:
        Redemption code string if found, None otherwise
    """
    # Try multiple selectors
    selectors_to_try = [REDEEM_CODE_SELECTOR, REDEEM_CODE_SELECTOR_ALT]

    for selector_idx, selector in enumerate(selectors_to_try):
        try:
            code_element = page.locator(selector)

            # Check if element exists in DOM
            if code_element.count() == 0:
                if selector_idx == 0:
                    logger.debug(
                        f"Draw {draw_number}: Selector '{selector}' not found, trying alternative..."
                    )
                    continue
                else:
                    logger.debug(
                        f"Draw {draw_number}: No redemption code element found (reward may not have code)"
                    )
                    return None

            # Wait for element to be attached and visible
            try:
                # First wait for it to be attached to DOM
                code_element.wait_for(state="attached", timeout=2000)
                logger.debug(f"Draw {draw_number}: Code element attached to DOM")

                # Then wait for it to be visible
                code_element.wait_for(state="visible", timeout=REDEEM_CODE_WAIT)
                logger.debug(f"Draw {draw_number}: Code element visible")

                # Get the text using inner_text (waits for element to have text)
                redeem_code = code_element.inner_text(timeout=2000)

                # Validate the code
                if redeem_code and len(redeem_code.strip()) > 0:
                    logger.info(
                        f"Draw {draw_number}: Successfully extracted code: {redeem_code}"
                    )
                    return redeem_code.strip()
                else:
                    logger.warning(
                        f"Draw {draw_number}: Code element found but text is empty"
                    )

            except PlaywrightTimeoutError:
                logger.warning(
                    f"Draw {draw_number}: Timeout waiting for code element with selector '{selector}'"
                )

                # Try alternative method: text_content (doesn't wait for visibility)
                try:
                    redeem_code = code_element.text_content(timeout=1000)
                    if redeem_code and len(redeem_code.strip()) > 0:
                        logger.info(
                            f"Draw {draw_number}: Extracted code via text_content: {redeem_code}"
                        )
                        return redeem_code.strip()
                except Exception:
                    pass

                # Try next selector if available
                if selector_idx < len(selectors_to_try) - 1:
                    logger.debug(f"Draw {draw_number}: Trying alternative selector...")
                    continue

        except Exception as e:
            logger.error(f"Draw {draw_number}: Error with selector '{selector}': {e}")
            if selector_idx < len(selectors_to_try) - 1:
                continue

    logger.warning(
        f"Draw {draw_number}: Could not extract redemption code after trying all methods"
    )
    return None


def _calculate_available_draws(page: Page) -> Optional[int]:
    """Calculate how many draws are available based on points and limits.

    Args:
        page: Playwright Page instance

    Returns:
        Number of available draws, or None if cannot be calculated
    """
    try:
        # Get current points
        current_point_text = page.locator(POINT_VALUE_SELECTOR).inner_text()
        current_points = int(current_point_text.replace(",", ""))
        logger.debug(
            f"Current points: {current_points} (raw text: '{current_point_text}')"
        )

        # Get draw cost
        draw_cost_text = page.locator(DRAW_COST_SELECTOR).inner_text()
        draw_price = extract_price(draw_cost_text)
        logger.debug(f"Draw price: ${draw_price} (raw text: '{draw_cost_text}')")

        # Calculate maximum affordable draws
        max_affordable = current_points // draw_price

        # Get draw limit (format: "remaining/total")
        draw_limit_text = page.locator(DRAW_LIMIT_SELECTOR).inner_text()
        logger.debug(f"Draw limit text (raw): '{draw_limit_text}'")

        draws_remaining = extract_number(draw_limit_text, side="left")
        draws_total = extract_number(draw_limit_text, side="right")
        logger.debug(f"Parsed draws: remaining={draws_remaining}, total={draws_total}")

        # Validate parsing
        if draws_remaining is None or draws_total is None:
            logger.error(f"Could not parse draw limit text: '{draw_limit_text}'")
            return None

        # Calculate available draws (minimum of affordable and remaining)
        available = min(max_affordable, draws_remaining)

        logger.info(
            f"Draw calculation: {current_points} points, "
            f"${draw_price} per draw, "
            f"{max_affordable} affordable, "
            f"{draws_remaining}/{draws_total} draws (remaining/total), "
            f"{available} available"
        )

        return available

    except Exception as e:
        logger.error(f"Error calculating available draws: {e}")
        return None


def _perform_single_draw(page: Page, draw_number: int, total_draws: int) -> bool:
    """Perform a single prize draw and handle the result.

    Args:
        page: Playwright Page instance
        draw_number: Current draw number (1-indexed)
        total_draws: Total number of draws planned

    Returns:
        True if draw was successful, False if should abort remaining draws
    """
    logger.info(f"Performing draw {draw_number}/{total_draws}")

    try:
        # Get draw button
        draw_button = page.locator(DRAW_BUTTON_SELECTOR)

        # Verify button is visible
        if not draw_button.is_visible(timeout=3000):
            logger.error(f"Draw {draw_number}: Draw button not visible")
            return False

        # Note: is_enabled() check removed - the button appears enabled even when
        # no draws are available. We rely on the pre-calculation check instead.

        # Click draw button
        logger.debug(f"Draw {draw_number}: Clicking draw button")
        draw_button.click()

        # Wait for result
        page.wait_for_timeout(DRAW_RESULT_WAIT)

        # Check for success dialog
        success_dialog = page.get_by_text(SUCCESS_DIALOG_TEXT)
        if not success_dialog.is_visible(timeout=3000):
            logger.warning(
                f"Draw {draw_number}: Draw result dialog not visible after clicking button"
            )

            # This usually means no draws are actually available (page data was stale)
            if draw_number == 1:
                logger.warning(
                    "First draw failed - likely no draws actually available despite what page shows"
                )
                NotificationHelper.notify(
                    title="ZZZ Bot - No Draws Available",
                    message="Draw button clicked but no result - draws may be exhausted",
                    app_icon=CONFIG.get("ICON_PATH", ""),
                )
            else:
                NotificationHelper.notify(
                    title="ZZZ Bot - Draw Failed",
                    message=f"Draw {draw_number} failed - dialog not visible",
                    app_icon=CONFIG.get("SAD_ICON", ""),
                )
            return False

        # Wait for draw animation to complete before detecting reward
        logger.debug(f"Draw {draw_number}: Waiting for animation to complete...")
        page.wait_for_timeout(2000)

        # Find and detect reward from image
        reward_image = _find_reward_image(page, draw_number)

        if reward_image is None:
            logger.error(
                f"Draw {draw_number}: Could not locate reward image - skipping reward detection"
            )
            _save_debug_artifacts(page, draw_number)
            reward_name = UNKNOWN_REWARD
        else:
            reward_name = detect_reward(page, reward_image)

        if reward_name == UNKNOWN_REWARD:
            logger.warning(
                f"Draw {draw_number}: Unknown reward detected, skipping redemption"
            )
        else:
            logger.info(f"Draw {draw_number}: Received '{reward_name}'")

            # Get and process redemption code
            redeem_code = _extract_redemption_code(page, draw_number)
            if redeem_code:
                try:
                    RedeemAutofill.run(page.context, redeem_code, reward_name)
                    logger.info(
                        f"Processed redemption code for '{reward_name}': {redeem_code}"
                    )
                except Exception as e:
                    logger.error(f"Error running autofill for '{reward_name}': {e}")
            else:
                logger.warning(
                    f"No redemption code found for '{reward_name}' (may not require one)"
                )

        # Close dialog
        try:
            close_button = page.locator(CLOSE_DIALOG_SELECTOR)
            # Use force=True to bypass any intercepting elements
            close_button.click(force=True, timeout=CLOSE_DIALOG_TIMEOUT)
            logger.debug("Closed draw dialog")
        except PlaywrightTimeoutError:
            logger.warning(
                "Close button not found, dialog may have closed automatically"
            )
        except Exception as e:
            logger.warning(f"Error closing dialog: {e}, attempting to continue")

        return True

    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout during draw {draw_number}: {e}")

        # Try to close any open dialog before returning
        try:
            logger.debug("Attempting to close any open dialog after timeout")
            close_button = page.locator(CLOSE_DIALOG_SELECTOR)
            if close_button.count() > 0:
                close_button.click(force=True, timeout=2000)
                logger.debug("Closed dialog after timeout")
                page.wait_for_timeout(500)
        except Exception as cleanup_error:
            logger.debug(f"Could not close dialog after timeout: {cleanup_error}")

        return False
    except Exception as e:
        logger.error(f"Error during draw {draw_number}: {e}")

        # Try to close any open dialog before returning
        try:
            logger.debug("Attempting to close any open dialog after error")
            close_button = page.locator(CLOSE_DIALOG_SELECTOR)
            if close_button.count() > 0:
                close_button.click(force=True, timeout=2000)
                logger.debug("Closed dialog after error")
                page.wait_for_timeout(500)
        except Exception as cleanup_error:
            logger.debug(f"Could not close dialog after error: {cleanup_error}")

        return False


def run(page: Page) -> None:
    """Main entry point for prize draw automation.

    Args:
        page: Playwright Page instance
    """
    import sentry_sdk

    logger.info("Starting prize draw automation...")

    _tx = sentry_sdk.start_transaction(op="task", name="draw-handler")
    try:
        # Log diagnostic information before attempting to open screen
        logger.info(f"Looking for draw button at image index {DRAW_BUTTON_INDEX}")
        logger.info(
            f"Looking for screen with selector '{SCREEN_SELECTOR}' containing text '{SCREEN_TEXT}'"
        )

        # Count total images available
        all_images = page.get_by_role("img")
        total_images = all_images.count()
        logger.info(f"Total image elements found on page: {total_images}")

        # Navigate to prize draw screen
        draw_button = page.get_by_role("img").nth(DRAW_BUTTON_INDEX)
        prize_screen = page.locator(SCREEN_SELECTOR).filter(has_text=SCREEN_TEXT)

        if not RetryHelper.retry_until_screen_appears(prize_screen, draw_button):
            logger.error("Failed to open prize draw screen")
            logger.error(
                f"Expected button at index {DRAW_BUTTON_INDEX}, but page has {total_images} images"
            )
            logger.error(
                "Check MongoDB screenshot assets for more details"
            )
            return

        logger.info("Prize draw screen opened")

        # Verify correct lottery (ZZZ)
        if not find_correct_lottery_logo(page):
            logger.error("ZZZ lottery not found or selected")
            return

        logger.info("ZZZ lottery verified")

        # Wait for page to fully load and data to refresh
        logger.debug("Waiting for draw data to load...")
        page.wait_for_timeout(2000)  # Give page time to load fresh data from server

        # Calculate available draws
        available_draws = _calculate_available_draws(page)

        if available_draws is None:
            logger.error("Could not calculate available draws")
            NotificationHelper.notify(
                title="ZZZ Bot - Draw Error",
                message="Could not calculate available draws",
                app_icon=CONFIG.get("SAD_ICON", ""),
            )
            return

        if available_draws <= 0:
            logger.info(
                f"No draws available (calculated: {available_draws} - insufficient points or limit reached)"
            )
            NotificationHelper.notify(
                title="ZZZ Bot - No Draws",
                message="No draws available (insufficient points or limit reached)",
                app_icon=CONFIG.get("ICON_PATH", ""),
            )
            return

        logger.info(f"Starting {available_draws} prize draw(s)")

        # Perform all draws
        successful_draws = 0
        failed_draws = 0

        for i in range(1, available_draws + 1):
            if _perform_single_draw(page, i, available_draws):
                successful_draws += 1
            else:
                failed_draws += 1

                # If first draw fails, page data was likely stale - log for user
                if i == 1:
                    logger.warning(
                        f"First draw failed - page may have shown stale data"
                    )
                    logger.info(
                        f"Page showed {available_draws} draws available, but none could be performed"
                    )
                    # Re-check actual draw count
                    page.wait_for_timeout(1000)
                    actual_available = _calculate_available_draws(page)
                    if (
                        actual_available is not None
                        and actual_available != available_draws
                    ):
                        logger.info(
                            f"After refresh: actually {actual_available} draws available (was showing {available_draws})"
                        )
                else:
                    logger.warning(f"Draw {i} failed, stopping remaining draws")

                break

            # Brief pause between draws
            if i < available_draws:
                page.wait_for_timeout(1000)

        # Log summary
        logger.info(
            f"Prize draw completed: {successful_draws} successful, "
            f"{failed_draws} failed out of {available_draws} available"
        )

        if successful_draws > 0:
            NotificationHelper.notify(
                title="ZZZ Bot - Draws Complete",
                message=f"Completed {successful_draws} prize draws",
                app_icon=CONFIG.get("ICON_PATH", ""),
            )

    except Exception as e:
        _tx.set_status("internal_error")
        logger.error(f"Prize draw automation failed: {e}", exc_info=True)
        NotificationHelper.notify(
            title="ZZZ Bot - Error",
            message="Prize draw automation failed",
            app_icon=CONFIG.get("SAD_ICON", ""),
        )
        raise
    finally:
        _tx.finish()
