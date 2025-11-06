import re
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page

import RedeemAutofill
import RetryHelper
from DataHandler import load_shopping_data, save_shopping_data
from GlobalVar import CONFIG, settings
from ImageProcessor import find_correct_avatar
from StringUtil import (
    extract_number_from_string,
    extract_and_convert_duration,
    calculate_return_time,
)


def is_current_time_in_duration(duration):
    try:
        # Parse the start and end dates
        start_date = datetime.strptime(duration.get("Start", ""), "%d/%m")
        end_date = datetime.strptime(duration.get("End", ""), "%d/%m")

        # Update with the current year
        current_year = datetime.now().year
        start_date = start_date.replace(year=current_year)
        end_date = end_date.replace(year=current_year)

        # Get current time
        current_time = datetime.now()

        # Check if current time is within range
        return start_date <= current_time <= end_date
    except (ValueError, TypeError) as e:
        # Handle missing or invalid date format
        print(f"Invalid duration format: {e}")
        return False


def check_and_process_item(item_locator):
    item_data = {}

    item_name = item_locator.locator(".itemName-NypcHW").inner_text()
    item_data["Name"] = item_name
    # Get the item price
    item_price_text = item_locator.locator(".itemPriceNum-cd1EE-").inner_text()
    item_price = int(
        item_price_text.replace(",", "")
    )  # Assume it's a comma-separated number
    item_data["Price"] = item_price

    # Get the shopping button text
    shopping_button_text = item_locator.locator(".itemBtn-gTL1Rd").inner_text()

    # Check if the shopping button text matches the hour:min:sec format
    time_pattern = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")

    if time_pattern.match(shopping_button_text):
        # Calculate and print the return time
        return_time = calculate_return_time(shopping_button_text)
        print("Return time:", return_time)
        item_data["Inventory"] = 0
        item_data["Available"] = return_time
    else:
        item_inventory = extract_number_from_string(
            item_locator.locator(".itemCnt-7wIR4D").inner_text()
        )
        item_data["Inventory"] = item_inventory
        item_data["Available"] = shopping_button_text
    return item_data


def init(page):
    # Get the shopping button and screen locators
    shopping_button_locator = page.get_by_role("img").nth(1)
    screen_locator = page.locator(".wrapper-O3T67n")
    # Ensure the button is visible on the screen
    RetryHelper.retry_until_screen_appears(screen_locator, shopping_button_locator)
    current_point_text = page.locator(".bubbleCnt-hsQFy-").inner_text()
    current_point_text = current_point_text[1:]
    current_point = int(current_point_text)
    print(f"Current points: {current_point}")

    return current_point


def run(page: Page):
    point = init(page)

    zzz_avatar = find_correct_avatar(page)
    zzz_avatar.click()

    file_path = Path(CONFIG["SHOPPING_FILE"])
    shopping_data = load_shopping_data(file_path)

    if shopping_data:
        duration = shopping_data.get("Duration", {})
        if is_current_time_in_duration(duration):
            print("Current time is within the duration. Updating data.")
            shopping_data.update(gather_data(page, point))
        else:
            print("Current time is outside the duration. Gathering new data.")
            shopping_data = gather_data(page, point)
    else:
        print("No existing data. Gathering new data.")
        shopping_data = gather_data(page, point)

    # Save updated shopping_data to file
    save_shopping_data(file_path, shopping_data)
    shopping_data = load_shopping_data(file_path)

    # Shopping part
    if settings.redeem_after_gather_data:
        run_shopping(page, shopping_data)
    else:
        print("Redeem canceled due to setting.")


def gather_data(page: Page, point: int):
    rows = {}
    number_item = RetryHelper.retry_until_non_zero_count(page.locator(".item-6Owrjq"))
    for i in range(number_item):
        item_locator = page.locator(".item-6Owrjq").nth(i)
        row = check_and_process_item(item_locator)

        item_name = row["Name"]  # Use the Name field as the key
        if item_name in rows:
            print(f"Duplicate item name detected: {item_name}. Skipping.")
        else:
            rows[item_name] = row

    duration_text = page.locator(".bubbleExpire-L4jUSs").inner_text()

    shopping_data = {
        "Point": point,
        "Duration": extract_and_convert_duration(duration_text),
        "Item's list": rows,  # Use Name as keys
    }

    return shopping_data


def run_shopping(page: Page, shopping_data):
    selected = shopping_data["Selected"]

    # Check if any item is selected
    if not selected:
        print("No item selected. Exiting.")
        return

    # Loop through selected items if buy_all is enabled, else process the first item
    items_to_process = selected if settings.buy_all else [selected[0]]

    for item_name in items_to_process:
        # Find the item in the shopping data
        item_data = next(
            (
                item
                for item in shopping_data["Item's list"].values()
                if item["Name"] == item_name
            ),
            None,
        )

        if not item_data:
            print(f"Item '{item_name}' not found in the shopping data. Skipping.")
            continue

        print(f"Processing item: {item_name}")

        # Locate and interact with the item in the browser
        item_locator = page.locator(".item-6Owrjq").filter(
            has=page.get_by_text(item_name, exact=True)
        )
        if item_locator.count() == 0:
            print(f"Item '{item_name}' not found on the page. Skipping.")
            continue

        shopping_button_locator = item_locator.locator(".itemBtn-gTL1Rd")
        if shopping_button_locator.inner_text() == "Exchange":
            shopping_button_locator.click()

            # Handle the confirm dialog if it appears
            if page.locator(".confirm-5fGU8Q").is_visible():
                print("Confirm screen detected.")
                confirm_ok = page.locator(".confirmOk-vBKGy6")
                confirm_ok.click()

                # Extract and copy the redeem code
                code_text = page.locator("div.gainCodeCopyInput-QcgdvD").inner_text()
                page.locator("div.gainCodeCopyBtn-Lwk9eR").click()

                RedeemAutofill.run(page.context, code_text, item_name)
                close_button = page.locator(".gainClose-7Q0hz8")
                close_button.click()
                print("Closing confirm dialog.")
        else:
            print("Can't exchange item")
