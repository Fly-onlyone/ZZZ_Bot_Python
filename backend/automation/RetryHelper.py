"""Retry helper utilities for Playwright operations.

Provides robust retry mechanisms for element interactions and visibility checks.
"""

import logging
from typing import Optional

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_RETRIES = 10
DEFAULT_DELAY_MS = 1000
VISIBILITY_TIMEOUT = 5000


def retry_until_screen_appears(
    screen: Locator,
    button: Locator,
    max_retries: int = DEFAULT_MAX_RETRIES,
    delay_ms: int = DEFAULT_DELAY_MS,
    timeout: int = VISIBILITY_TIMEOUT,
) -> bool:
    """Click button repeatedly until target screen appears.

    Args:
        screen: Target screen locator to wait for
        button: Button locator to click
        max_retries: Maximum number of retry attempts
        delay_ms: Delay between retries in milliseconds
        timeout: Timeout for visibility checks in milliseconds

    Returns:
        True if screen appeared, False if max retries reached
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Wait for button and click
            button.wait_for(state="visible", timeout=timeout)
            button.click(force=True)
            logger.debug(f"Button clicked (attempt {attempt}/{max_retries})")

            # Check if target screen is visible
            if screen.is_visible(timeout=timeout):
                logger.info(f"Target screen appeared on attempt {attempt}")
                return True

            logger.debug(
                f"Attempt {attempt}/{max_retries}: Target screen not visible, retrying..."
            )

        except PlaywrightTimeoutError:
            logger.warning(
                f"Attempt {attempt}/{max_retries}: Timeout waiting for button or screen"
            )
        except Exception as e:
            logger.error(f"Attempt {attempt}/{max_retries}: Unexpected error: {e}")

        # Wait before next retry (skip on last attempt)
        if attempt < max_retries:
            button.page.wait_for_timeout(delay_ms)

    # Diagnostic logging when max retries reached
    logger.error(f"Max retries ({max_retries}) reached. Target screen did not appear.")

    try:
        # Log diagnostic information
        page = button.page

        from datetime import datetime

        from utils.screenshot_store import save_page_screenshot

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"retry_failed_{timestamp}.png"
        asset_id = save_page_screenshot(page, filename)
        logger.error("Screenshot saved to MongoDB asset: %s", asset_id)

        # Log available image buttons
        all_images = page.get_by_role("img")
        image_count = all_images.count()
        logger.error(f"Found {image_count} image elements on page:")
        for i in range(min(image_count, 10)):  # Log first 10 images
            try:
                img = all_images.nth(i)
                alt_text = img.get_attribute("alt") or "N/A"
                src = img.get_attribute("src") or "N/A"
                logger.error(f"  Image {i}: alt='{alt_text}', src='{src[:50]}...'")
            except Exception as e:
                logger.error(f"  Image {i}: Error getting attributes - {e}")

        # Log target screen selector info
        screen_count = screen.count()
        logger.error(f"Target screen selector matched {screen_count} elements")

    except Exception as e:
        logger.error(f"Error during diagnostic logging: {e}")

    return False


def retry_until_non_zero_count(
    locator: Locator,
    max_retries: int = DEFAULT_MAX_RETRIES,
    delay_ms: int = DEFAULT_DELAY_MS,
) -> int:
    """Retry counting elements until a non-zero count is found.

    Args:
        locator: Element locator to count
        max_retries: Maximum number of retry attempts
        delay_ms: Delay between retries in milliseconds

    Returns:
        Element count (may be 0 if max retries reached)
    """
    for attempt in range(1, max_retries + 1):
        try:
            count = locator.count()

            if count > 0:
                logger.info(
                    f"Non-zero count found: {count} (attempt {attempt}/{max_retries})"
                )
                return count

            logger.debug(f"Attempt {attempt}/{max_retries}: Count is 0, retrying...")

        except Exception as e:
            logger.error(
                f"Attempt {attempt}/{max_retries}: Error counting elements: {e}"
            )

        # Wait before next retry (skip on last attempt)
        if attempt < max_retries:
            locator.page.wait_for_timeout(delay_ms)

    logger.warning(f"Max retries ({max_retries}) reached. Count is still 0.")
    return 0


def wait_for_element(
    locator: Locator,
    state: str = "visible",
    timeout: int = VISIBILITY_TIMEOUT,
    element_name: Optional[str] = None,
) -> bool:
    """Wait for element to reach desired state.

    Args:
        locator: Element locator
        state: Desired state ('visible', 'hidden', 'attached', 'detached')
        timeout: Maximum wait time in milliseconds
        element_name: Optional name for logging

    Returns:
        True if element reached desired state, False otherwise
    """
    element_desc = element_name or "element"

    try:
        locator.wait_for(state=state, timeout=timeout)
        logger.info(f"{element_desc} reached state '{state}'")
        return True
    except PlaywrightTimeoutError:
        logger.warning(
            f"{element_desc} did not reach state '{state}' within {timeout}ms"
        )
        return False
    except Exception as e:
        logger.error(f"Error waiting for {element_desc}: {e}")
        return False
