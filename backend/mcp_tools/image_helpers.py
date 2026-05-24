"""Async image helpers for MCP Inspector tools.

Provides async versions of image fetching and comparison functions
for use in MCP tools that need to work with live browser elements.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Union
from urllib.parse import urljoin

import aiohttp
import cv2
import numpy as np
from core.constants import IMAGE_BINARY_THRESHOLD, IMAGE_MATCH_THRESHOLD
from playwright.async_api import Locator, Page

logger = logging.getLogger(__name__)

# Type alias
ImageType = Union[str, np.ndarray]

# Shared aiohttp session (created on first use)
_aiohttp_session: aiohttp.ClientSession | None = None


async def get_aiohttp_session() -> aiohttp.ClientSession:
    """Get or create a shared aiohttp session for async HTTP requests."""
    global _aiohttp_session
    if _aiohttp_session is None or _aiohttp_session.closed:
        timeout = aiohttp.ClientTimeout(total=30)
        _aiohttp_session = aiohttp.ClientSession(timeout=timeout)
    return _aiohttp_session


async def close_aiohttp_session():
    """Close the shared aiohttp session."""
    global _aiohttp_session
    if _aiohttp_session is not None and not _aiohttp_session.closed:
        await _aiohttp_session.close()
        _aiohttp_session = None


async def fetch_image_from_locator_async(page: Page, locator: Locator) -> np.ndarray:
    """Async version of fetch_image_from_locator.

    Extracts image from a Playwright locator using various strategies:
    1. Direct img src attribute
    2. Child img element src
    3. Background-image style (inline or computed)
    4. Data URI decoding

    Args:
        page: Playwright Page instance
        locator: Playwright Locator pointing to element with image

    Returns:
        OpenCV image as numpy array

    Raises:
        ValueError: If no image could be extracted from the locator
    """
    image_url = None

    # 1. If the locator is an <img>, grab its src
    is_img = await locator.evaluate("el => el.tagName.toLowerCase() === 'img'")
    if is_img:
        image_url = await locator.get_attribute("src")

    # 2. If it contains an <img>, grab that child src
    if not image_url:
        try:
            child_img = locator.locator("img")
            if await child_img.count() > 0:
                image_url = await child_img.first.get_attribute("src")
        except Exception as e:
            logger.debug(f"Could not extract image from child img element: {e}")

    # 3. Fallback to background-image style
    if not image_url:
        style = await locator.get_attribute("style")
        if style and "background-image" in style:
            start = style.find('url("') + len('url("')
            end = style.find('")', start)
            if start > 4 and end > start:
                image_url = style[start:end]
        else:
            computed = await locator.evaluate("(el) => window.getComputedStyle(el).backgroundImage")
            if computed and computed.startswith("url("):
                start = computed.find('url("') + len('url("')
                end = computed.find('")', start)
                if start > 4 and end > start:
                    image_url = computed[start:end]

    if not image_url:
        raise ValueError("Image URL not found for locator")

    # 4. Handle data URIs
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

    # 5. Resolve relative URLs to absolute
    if not image_url.startswith(("http://", "https://")):
        image_url = urljoin(page.url, image_url)
    logger.debug(f"Resolved image URL: {image_url}")

    # 6. Fetch image via aiohttp
    session = await get_aiohttp_session()
    async with session.get(image_url) as resp:
        resp.raise_for_status()
        content = await resp.read()

    arr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to decode image from URL: {image_url}")

    return img


def compare_images_sync(
    img1: ImageType, img2: ImageType, binary_threshold: int = IMAGE_BINARY_THRESHOLD
) -> float:
    """Compare two images and return the difference percentage.

    Synchronous function using OpenCV for image comparison.
    Handles file paths and numpy arrays.

    Args:
        img1: First image (file path or numpy array)
        img2: Second image (file path or numpy array)
        binary_threshold: Threshold for binary diff detection

    Returns:
        Percentage of different pixels (0-100)

    Raises:
        ValueError: If images cannot be loaded or are invalid types
    """
    # Load first image
    if isinstance(img1, str):
        loaded_img1 = cv2.imread(img1)
        if loaded_img1 is None:
            raise ValueError(f"Could not load image from path: {img1}")
    elif isinstance(img1, np.ndarray):
        loaded_img1 = img1
    else:
        raise ValueError(f"img1 must be file path (str) or numpy array, got {type(img1)}")

    # Load second image
    if isinstance(img2, str):
        loaded_img2 = cv2.imread(img2)
        if loaded_img2 is None:
            raise ValueError(f"Could not load image from path: {img2}")
    elif isinstance(img2, np.ndarray):
        loaded_img2 = img2
    else:
        raise ValueError(f"img2 must be file path (str) or numpy array, got {type(img2)}")

    # Resize to match dimensions
    if loaded_img1.shape != loaded_img2.shape:
        loaded_img2 = cv2.resize(loaded_img2, (loaded_img1.shape[1], loaded_img1.shape[0]))

    # Compute absolute difference
    difference = cv2.absdiff(loaded_img1, loaded_img2)

    # Convert to grayscale
    gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # Apply binary threshold
    _, threshold_diff = cv2.threshold(gray_diff, binary_threshold, 255, cv2.THRESH_BINARY)

    # Calculate difference percentage
    non_zero_count = np.count_nonzero(threshold_diff)
    total_pixels = threshold_diff.size
    difference_percentage = (non_zero_count / total_pixels) * 100

    return difference_percentage


def scan_folder_for_best_match(
    target_img: np.ndarray,
    folder_path: str,
    threshold: float = IMAGE_MATCH_THRESHOLD,
) -> dict:
    """Scan a folder of reference images to find the best match.

    Args:
        target_img: Target image as numpy array
        folder_path: Path to folder containing reference images
        threshold: Match threshold percentage (lower = stricter)

    Returns:
        dict with:
            - match: bool - True if best match is within threshold
            - best_match: str - Name of best matching file (without extension)
            - difference_percent: float - Difference percentage of best match
            - comparisons: list - All comparisons made
    """
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")

    # Get image files from folder
    image_files = [
        f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]

    if not image_files:
        raise ValueError(f"No image files found in folder: {folder_path}")

    best_match_name = None
    best_match_diff = float("inf")
    comparisons = []

    for img_file in image_files:
        img_path = os.path.join(folder_path, img_file)
        try:
            diff = compare_images_sync(target_img, img_path)
            name = Path(img_file).stem  # Filename without extension

            comparisons.append({"name": name, "difference_percent": round(diff, 2)})
            logger.debug(f"  '{name}': {diff:.2f}% difference")

            if diff < best_match_diff:
                best_match_diff = diff
                best_match_name = name

        except Exception as e:
            logger.warning(f"Error comparing with {img_file}: {e}")
            comparisons.append({"name": Path(img_file).stem, "error": str(e)})

    is_match = best_match_diff < threshold

    return {
        "match": is_match,
        "best_match": best_match_name,
        "difference_percent": round(best_match_diff, 2),
        "threshold": threshold,
        "comparisons": comparisons,
    }
