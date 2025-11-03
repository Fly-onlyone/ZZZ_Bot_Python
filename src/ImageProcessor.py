import base64
import os
from urllib.parse import urljoin

import cv2
import numpy as np
import requests
from playwright.sync_api import Locator, Page

import RetryHelper
from GlobalVar import CONFIG


def compare_images(arg1, arg2):
    # Check if the inputs are file paths (str), then read the images
    if isinstance(arg1, str) and isinstance(arg2, str):
        img1 = cv2.imread(arg1)
        img2 = cv2.imread(arg2)
    # If inputs are already OpenCV images (numpy arrays), use them directly
    elif isinstance(arg1, np.ndarray) and isinstance(arg2, np.ndarray):
        img1 = arg1
        img2 = arg2
    else:
        raise ValueError(
            "Arguments must both be file paths (str) or OpenCV images (numpy.ndarray)."
        )

    # Resize images to the same size for comparison (optional if sizes differ)
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    # Compute the difference between the images
    difference = cv2.absdiff(img1, img2)

    # Convert the difference image to grayscale
    gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # Apply a binary threshold to the grayscale difference image
    _, threshold_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

    # Calculate the percentage of different pixels
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
        except Exception:
            pass

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
        raise ValueError(f"Image URL not found for locator: {locator_selector}")

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
    print(f"Resolved image URL: {image_url}")

    # 6. Fetch & decode via requests + OpenCV
    resp = requests.get(image_url)
    resp.raise_for_status()
    arr = np.frombuffer(resp.content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to decode image from URL: {image_url}")

    return img


def find_correct_avatar(page: Page):
    avatar_count = RetryHelper.retry_until_non_zero_count(
        page.locator("div.avatarsItemImg-AiUG1h")
    )
    print(f"Avatar count: {avatar_count}")
    zzz_icon_path = CONFIG["ZZZ_ICON"]
    for i in range(avatar_count):
        avatar_icon_locator = page.locator("div.avatarsItemImg-AiUG1h").nth(i)
        avatar_image = fetch_image_from_locator(page, avatar_icon_locator)
        diff = compare_images(avatar_image, cv2.imread(zzz_icon_path))
        print(f"Difference from ZZZ Avatar: {diff}%")
        if diff < 5:
            print("This is ZZZ avatar")
            return avatar_icon_locator
        else:
            print("This is NOT ZZZ avatar")
    return None


def find_correct_lottery_logo(page: Page):
    zzz_icon_img = cv2.imread(CONFIG["ZZZ_ICON"])
    for i in range(4):
        lottery_logo_locator = page.locator("div.lotteryLogo-269XTi")
        lottery_logo_img = fetch_image_from_locator(page, lottery_logo_locator)
        diff = compare_images(lottery_logo_img, zzz_icon_img)
        print(f"Difference from ZZZ Avatar: {diff}%")
        if diff < 5:
            print("This is ZZZ avatar")
            return True
        else:
            print("This is NOT ZZZ avatar")
            page.locator(".lotterySwitch-LdUVnT").click()
    return False


def detect_reward(page: Page, img_locator: Locator):
    # Fetch the image from the locator
    target_img = fetch_image_from_locator(page, img_locator)

    # Get list of available reward images
    reward_images = [
        f for f in os.listdir(CONFIG["REWARD_FOLDER"]) if f.endswith(".png")
    ]

    if not reward_images:
        raise ValueError("No reward images found in the configured reward folder.")

    best_match = "Unknown reward"

    for reward_img_name in reward_images:
        reward_img_path = os.path.join(CONFIG["REWARD_FOLDER"], reward_img_name)
        diff = compare_images(target_img, reward_img_path)

        if diff == 0:  # Exact match found
            return os.path.splitext(reward_img_name)[0]

    return best_match  # Return "Unknown reward" if no exact match


class ImageProcessor:
    def __init__(self, page, button):
        self.button = button
        self.page = page

    def detect_button_state(self):
        tick_image = cv2.imread(CONFIG["SAMPLE_FOLDER"] + "/Finished.png")
        arrow_image = cv2.imread(CONFIG["SAMPLE_FOLDER"] + "/Unfinished.png")
        reward_image = cv2.imread(CONFIG["SAMPLE_FOLDER"] + "/Reward.png")

        buttom_img = fetch_image_from_locator(self.page, self.button)

        tick_diff = compare_images(buttom_img, tick_image)
        arrow_diff = compare_images(buttom_img, arrow_image)
        reward_diff = compare_images(buttom_img, reward_image)

        print(f"Difference with Finished (tick) image: {tick_diff}%")
        print(f"Difference with Unfinished (arrow) image: {arrow_diff}%")
        print(f"Difference with Reward image: {reward_diff}%")

        diffs = {"Finished": tick_diff, "Unfinished": arrow_diff, "Reward": reward_diff}

        closest_state = min(diffs, key=diffs.get)

        if diffs[closest_state] < 5:  # Set a threshold for detection
            print(f"Button detected as {closest_state}")
            return closest_state
        else:
            print("Unknown button state")
            return "unknown"
