import base64
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
    # Try to get the `style` attribute
    style = locator_selector.get_attribute("style")
    image_url = None

    if style and "background-image" in style:
        # Extract the URL from the style attribute
        url_start = style.find('url("') + len('url("')
        url_end = style.find('")', url_start)
        image_url = style[url_start:url_end]
    else:
        # If `style` doesn't contain background-image, fall back to computed style
        computed_style = locator_selector.evaluate(
            "(el) => window.getComputedStyle(el).backgroundImage"
        )
        if computed_style and computed_style.startswith("url("):
            # Extract the URL from the computed style
            url_start = computed_style.find('url("') + len('url("')
            url_end = computed_style.find('")', url_start)
            image_url = computed_style[url_start:url_end]

    if not image_url:
        raise ValueError(f"Image URL not found for locator: {locator_selector}")

    # Check if the URL is Base64-encoded
    if image_url.startswith("data:image/"):
        # Split the Base64 header from the actual data
        header, base64_data = image_url.split(",", 1)
        try:
            # Decode Base64 data
            image_data = base64.b64decode(base64_data)
            image_array = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode Base64 image.")
            return image
        except Exception as e:
            raise ValueError(f"Error decoding Base64 image: {e}")
    else:
        # Resolve relative URLs using the page's base URL
        if not image_url.startswith("http://") and not image_url.startswith("https://"):
            image_url = urljoin(page.url, image_url)  # Combine with the page's base URL

        print(f"Resolved image URL: {image_url}")

        # Fetch image data using requests
        response = requests.get(image_url)
        response.raise_for_status()  # Ensure the request was successful
        image_data = np.frombuffer(response.content, np.uint8)

        # Decode the image to an OpenCV format
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Failed to decode image from URL: {image_url}")

        return image


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
