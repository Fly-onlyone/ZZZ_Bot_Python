"""Image processing module for ZZZ Bot.

Provides image comparison, element detection, and visual state recognition
using OpenCV for browser automation.
"""

import base64
import logging
import os
from typing import Optional, Union
from urllib.parse import urljoin

import cv2
import numpy as np
import requests
from core.constants import (
    HTTP_MAX_RETRIES,
    HTTP_POOL_CONNECTIONS,
    HTTP_POOL_MAX_SIZE,
    HTTP_REQUEST_TIMEOUT,
    IMAGE_BINARY_THRESHOLD,
    IMAGE_MATCH_THRESHOLD,
)
from core.GlobalVar import CONFIG, resource_path
from playwright.sync_api import Locator, Page

from . import RetryHelper

logger = logging.getLogger(__name__)

# Type aliases
ImageType = Union[str, np.ndarray]
AVATAR_FETCH_RETRY_ATTEMPTS = 2

# Connection pooling for image fetches
_http_session = None


def get_http_session():
    """Get or create a shared requests session with connection pooling.

    Returns:
        requests.Session: Reusable session instance
    """
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=HTTP_POOL_CONNECTIONS,
            pool_maxsize=HTTP_POOL_MAX_SIZE,
            max_retries=HTTP_MAX_RETRIES,
        )
        _http_session.mount("http://", adapter)
        _http_session.mount("https://", adapter)
    return _http_session


def compare_images(arg1: ImageType, arg2: ImageType) -> float:
    """Compare two images and return the difference percentage.

    Args:
        arg1: First image (file path or numpy array)
        arg2: Second image (file path or numpy array)

    Returns:
        Percentage of different pixels (0-100)

    Raises:
        ValueError: If arguments are not valid image types
    """
    # Load first image
    if isinstance(arg1, str):
        img1 = cv2.imread(arg1)
        if img1 is None:
            raise ValueError(f"Could not load image from path: {arg1}")
    elif isinstance(arg1, np.ndarray):
        img1 = arg1
    else:
        raise ValueError(
            f"arg1 must be file path (str) or OpenCV image (numpy.ndarray), got {type(arg1)}"
        )

    # Load second image
    if isinstance(arg2, str):
        img2 = cv2.imread(arg2)
        if img2 is None:
            raise ValueError(f"Could not load image from path: {arg2}")
    elif isinstance(arg2, np.ndarray):
        img2 = arg2
    else:
        raise ValueError(
            f"arg2 must be file path (str) or OpenCV image (numpy.ndarray), got {type(arg2)}"
        )

    # Resize second image to match first image dimensions
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Compute absolute difference
    difference = cv2.absdiff(img1, img2)

    # Convert to grayscale
    gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # Apply binary threshold
    _, threshold_diff = cv2.threshold(gray_diff, IMAGE_BINARY_THRESHOLD, 255, cv2.THRESH_BINARY)

    # Calculate difference percentage
    non_zero_count = np.count_nonzero(threshold_diff)
    total_pixels = threshold_diff.size
    difference_percentage = (non_zero_count / total_pixels) * 100

    return difference_percentage


def fetch_image_from_locator(page: Page, locator_selector: Locator):
    image_url = None

    # 1. If the locator *is* an <img>, grab its `src`
    is_img = locator_selector.evaluate("el => el.tagName.toLowerCase() === 'img'")
    if is_img:
        image_url = locator_selector.get_attribute("src")

    # 2. Otherwise, if it *contains* an <img>, grab that child src
    if not image_url:
        try:
            child_img = locator_selector.locator("img")
            # locator.count() > 0 if it found at least one <img>
            if child_img.count() > 0:
                image_url = child_img.first.get_attribute("src")
        except Exception as e:
            logger.debug(f"Could not extract image from child img element: {e}")

    # 3. Fallback to style attribute / computedStyle background-image
    if not image_url:
        style = locator_selector.get_attribute("style")
        if style and "background-image" in style:
            start = style.find('url("') + len('url("')
            end = style.find('")', start)
            image_url = style[start:end]
        else:
            computed = locator_selector.evaluate(
                "(el) => window.getComputedStyle(el).backgroundImage"
            )
            if computed and computed.startswith("url("):
                start = computed.find('url("') + len('url("')
                end = computed.find('")', start)
                image_url = computed[start:end]

    if not image_url:
        try:
            screenshot_bytes = locator_selector.screenshot()
            arr = np.frombuffer(screenshot_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Failed to decode locator screenshot.")
            logger.debug(
                "Fell back to locator screenshot for image extraction: %s",
                locator_selector,
            )
            return img
        except Exception as screenshot_error:
            raise ValueError(
                f"Image URL not found for locator: {locator_selector}"
            ) from screenshot_error

    # 4. Decode data-URIs
    if image_url.startswith("data:image/"):
        header, base64_data = image_url.split(",", 1)
        try:
            img_data = base64.b64decode(base64_data)
            arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Failed to decode Base64 image.")
            return img
        except Exception as e:
            raise ValueError(f"Error decoding Base64 image: {e}")

    # 5. Resolve relative → absolute URLs
    if not image_url.startswith(("http://", "https://")):
        image_url = urljoin(page.url, image_url)
    logger.debug(f"Resolved image URL: {image_url}")

    # 6. Fetch & decode via requests + OpenCV (using connection pooling)
    session = get_http_session()
    resp = session.get(image_url, timeout=HTTP_REQUEST_TIMEOUT)
    resp.raise_for_status()
    arr = np.frombuffer(resp.content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to decode image from URL: {image_url}")

    return img


def find_correct_avatar(page: Page) -> Optional[Locator]:
    """Find and return the ZZZ game avatar from available avatars.

    Args:
        page: Playwright Page instance

    Returns:
        Locator for ZZZ avatar if found, None otherwise
    """
    avatar_locators = page.locator("div.avatarsItemImg-AiUG1h")
    avatar_count = RetryHelper.retry_until_non_zero_count(avatar_locators)

    logger.info(f"Found {avatar_count} avatars")

    if avatar_count == 0:
        logger.warning("No avatars found on page")
        return None

    zzz_icon_path = CONFIG["ZZZ_ICON"]
    zzz_icon_img = cv2.imread(zzz_icon_path)

    if zzz_icon_img is None:
        logger.error(f"Could not load ZZZ icon from {zzz_icon_path}")
        return None

    transient_failures = 0

    for i in range(avatar_count):
        avatar_locator = avatar_locators.nth(i)

        for attempt in range(1, AVATAR_FETCH_RETRY_ATTEMPTS + 1):
            try:
                avatar_image = fetch_image_from_locator(page, avatar_locator)
                diff = compare_images(avatar_image, zzz_icon_img)

                logger.debug(f"Avatar {i + 1}: {diff:.2f}% difference from ZZZ icon")

                if diff < IMAGE_MATCH_THRESHOLD:
                    logger.info(f"ZZZ avatar found at position {i + 1}")
                    return avatar_locator
                break

            except Exception as e:
                transient_failures += 1
                logger.warning(
                    "Error checking avatar %s on attempt %s/%s: %s",
                    i + 1,
                    attempt,
                    AVATAR_FETCH_RETRY_ATTEMPTS,
                    e,
                )
                if attempt < AVATAR_FETCH_RETRY_ATTEMPTS:
                    page.wait_for_timeout(250)
                    continue

                break

    if transient_failures:
        logger.warning(
            "ZZZ avatar lookup exhausted %s transient fetch/read errors",
            transient_failures,
        )
    logger.warning("ZZZ avatar not found among available avatars")
    return None


def _dismiss_guide_overlay(page: Page) -> None:
    """Dismiss HoYoLab tutorial/guide overlays that block UI interaction.

    Strategy: click the draw button first (the guide highlights it, so
    clicking advances/dismisses the guide naturally). Fall back to JS
    removal of the SVG hollow-mask overlay if the guide persists.
    """
    # Click the overlay element directly to advance/dismiss the guide
    overlay_selector = "rect[mask*='hollow-mask']"
    for attempt in range(5):
        if not _has_guide_overlay(page):
            if attempt > 0:
                logger.info("Guide overlay dismissed after %d click(s)", attempt)
            return
        try:
            page.locator(overlay_selector).first.click(force=True, timeout=1000)
            logger.info("Guide overlay click %d on overlay element", attempt + 1)
            page.wait_for_timeout(500)
        except Exception as exc:
            logger.debug("Guide overlay click %d failed: %s", attempt + 1, exc)
            break

    # Fallback: remove overlay via JS if clicks didn't dismiss it
    if _has_guide_overlay(page):
        removed = page.evaluate(
            """() => {
            let count = 0;
            document.querySelectorAll('rect[mask*="hollow-mask"]').forEach(rect => {
                const container = rect.closest('div');
                if (container && container.parentElement) {
                    container.parentElement.removeChild(container);
                    count++;
                }
            });
            return count;
        }"""
        )
        if removed:
            logger.info("Dismissed %d guide overlay(s) via JS removal", removed)
            page.wait_for_timeout(300)


def _has_guide_overlay(page: Page) -> bool:
    """Check if a HoYoLab guide overlay with hollow mask is present."""
    return page.evaluate(
        "() => document.querySelectorAll('rect[mask*=\"hollow-mask\"]').length > 0"
    )


def find_correct_lottery_logo(page: Page):
    from .tracking import safe_track

    _dismiss_guide_overlay(page)
    zzz_icon_img = cv2.imread(CONFIG["ZZZ_ICON"])
    best_diff = 100.0
    best_img = None
    last_error = None
    logo_selector = "div.lotteryLogo-269XTi"
    switch_selector = ".lotterySwitch-LdUVnT"

    for i in range(4):
        lottery_logo_locator = page.locator(logo_selector)
        try:
            lottery_logo_img = fetch_image_from_locator(page, lottery_logo_locator)
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Lottery logo %d could not be read on current view: %s",
                i + 1,
                exc,
            )
            page.locator(switch_selector).click(force=True)
            page.wait_for_timeout(500)
            continue

        diff = compare_images(lottery_logo_img, zzz_icon_img)
        logger.info("Lottery logo %d: %.2f%% difference from ZZZ icon", i + 1, diff)
        if diff < IMAGE_MATCH_THRESHOLD:
            logger.info("ZZZ lottery logo matched at position %d", i + 1)
            safe_track(
                page,
                logo_selector,
                "DrawHandler",
                "image_match",
                True,
                locator=lottery_logo_locator,
            )
            return True
        if diff < best_diff:
            best_diff = diff
            best_img = lottery_logo_img
        page.locator(switch_selector).click(force=True)
        page.wait_for_timeout(500)

    # Track the failure while still on the draw screen
    safe_track(
        page,
        logo_selector,
        "DrawHandler",
        "image_match",
        False,
        error_message=f"Best diff: {best_diff:.2f}%",
        locator=page.locator(logo_selector),
    )

    # Save diagnostics for reference update
    if best_img is not None:
        logo_path = resource_path("screenshot/lottery_logo_mismatch.png", outside_path=True)
        cv2.imwrite(logo_path, best_img)
    if last_error is not None:
        logger.warning(
            "ZZZ lottery logo not found (best diff: %.2f%%, last_error=%s).",
            best_diff,
            last_error,
        )
    else:
        logger.warning(
            "ZZZ lottery logo not found (best diff: %.2f%%).",
            best_diff,
        )
    return False


def detect_reward(page: Page, img_locator: Locator):
    """Detect reward type by comparing locator image against reference images.

    Uses 5% threshold tolerance to handle minor image variations from
    CDN compression, animation states, or rendering differences.

    Args:
        page: Playwright Page instance
        img_locator: Locator for the reward image element

    Returns:
        Reward name (filename without extension) if match found,
        "Unknown reward" otherwise
    """
    import sentry_sdk

    with sentry_sdk.start_span(op="cv.template_match", name="detect_reward"):
        # Fetch the image from the locator
        target_img = fetch_image_from_locator(page, img_locator)

        # Get list of available reward images
        reward_images = [f for f in os.listdir(CONFIG["REWARD_FOLDER"]) if f.endswith(".png")]

        if not reward_images:
            raise ValueError("No reward images found in the configured reward folder.")

        best_match_name = "Unknown reward"
        best_match_diff = float("inf")

        logger.debug(f"Comparing reward image against {len(reward_images)} reference images...")

        for reward_img_name in reward_images:
            reward_img_path = os.path.join(CONFIG["REWARD_FOLDER"], reward_img_name)
            diff = compare_images(target_img, reward_img_path)

            reward_name = os.path.splitext(reward_img_name)[0]
            logger.debug(f"  '{reward_name}': {diff:.2f}% difference")

            # Track best match (lowest difference)
            if diff < best_match_diff:
                best_match_diff = diff
                best_match_name = reward_name

        # Return best match if within 5% threshold (consistent with button detection)
        if best_match_diff < IMAGE_MATCH_THRESHOLD:
            logger.info(f"Reward detected: '{best_match_name}' ({best_match_diff:.2f}% difference)")
            return best_match_name
        else:
            logger.warning(
                f"No reward match found within threshold. Best match: '{best_match_name}' "
                f"({best_match_diff:.2f}% difference, threshold: {IMAGE_MATCH_THRESHOLD}%)"
            )
            return "Unknown reward"


class ImageProcessor:
    def __init__(self, page, button):
        self.button = button
        self.page = page

    def detect_button_state(self):
        import sentry_sdk

        with sentry_sdk.start_span(op="cv.template_match", name="detect_button_state"):
            tick_image = cv2.imread(CONFIG["SAMPLE_FOLDER"] + "/Finished.png")
            arrow_image = cv2.imread(CONFIG["SAMPLE_FOLDER"] + "/Unfinished.png")
            reward_image = cv2.imread(CONFIG["SAMPLE_FOLDER"] + "/Reward.png")

            buttom_img = fetch_image_from_locator(self.page, self.button)

            tick_diff = compare_images(buttom_img, tick_image)
            arrow_diff = compare_images(buttom_img, arrow_image)
            reward_diff = compare_images(buttom_img, reward_image)

            logger.debug("Difference with Finished (tick) image: %s%%", tick_diff)
            logger.debug("Difference with Unfinished (arrow) image: %s%%", arrow_diff)
            logger.debug("Difference with Reward image: %s%%", reward_diff)

            diffs = {
                "Finished": tick_diff,
                "Unfinished": arrow_diff,
                "Reward": reward_diff,
            }

            closest_state = min(diffs, key=diffs.get)

            if diffs[closest_state] < 5:  # Set a threshold for detection
                logger.info("Mission button detected as %s", closest_state)
                return closest_state
            else:
                logger.warning("Mission button state is unknown")
                return "unknown"
