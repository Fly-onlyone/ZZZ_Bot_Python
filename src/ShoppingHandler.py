import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas
from playwright.sync_api import Page

import RetryHelper
from Bot import CONFIG
from src.ImageProcessor import find_correct_avatar


def extract_number_from_string(input_string):
    import re

    # Use regex to find the first sequence of digits in the string
    match = re.search(r"\d+", input_string)
    return int(match.group()) if match else None


def extract_and_convert_duration(input_string):
    import re

    # Regex to capture the start and end dates
    match = re.search(r"Duration:\s*(\d+/\d+)\s*–\s*(\d+/\d+)", input_string)
    if match:
        start_date, end_date = match.groups()

        # Convert each date to day/month format
        start_day, start_month = start_date.split("/")
        end_day, end_month = end_date.split("/")

        # Return the result in day/month format
        return {"Start": f"{start_month}/{start_day}", "End": f"{end_month}/{end_day}"}
    return None  # Return None if the pattern doesn't match


def calculate_return_time(input_time_str):
    # Parse the input string (format: "hour:min:sec")
    input_time_parts = list(map(int, input_time_str.split(":")))

    # Extract the hours, minutes, and seconds from the input
    input_hours = input_time_parts[0]
    input_minutes = input_time_parts[1]
    input_seconds = input_time_parts[2]

    # Create a timedelta from the input
    time_delta = timedelta(
        hours=input_hours, minutes=input_minutes, seconds=input_seconds
    )

    # Get the current time
    current_time = datetime.now()

    # Calculate the return time by adding the time delta to the current time
    return_time = current_time + time_delta

    # Format the return time in the format "hour:min dd/mm/yy"
    return return_time.strftime("%H:%M %d/%m/%y")


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
        item_data["Available"] = "Yes"
    return item_data


def init(page):
    # Get the current points
    current_point_text = page.locator(".txt-EK942w").nth(1).inner_text()
    current_point = int(
        current_point_text.replace(",", "")
    )  # Assume it's a comma-separated number
    # Get the shopping button and screen locators
    shopping_button_locator = page.get_by_role("img").nth(1)
    screen_locator = page.locator(".wrapper-O3T67n")
    # Ensure the button is visible on the screen
    RetryHelper.retry_until_screen_appears(screen_locator, shopping_button_locator)
    return current_point


def run(page: Page):
    point = init(page)

    zzz_avatar = find_correct_avatar(page)
    zzz_avatar.click()

    rows = []
    number_item = RetryHelper.retry_until_non_zero_count(page.locator(".item-6Owrjq"))
    for i in range(number_item):
        row = check_and_process_item(page.locator(".item-6Owrjq").nth(i))
        rows.append(row)

    dataframe = pandas.DataFrame(rows)

    duration_text = page.locator(".bubbleExpire-L4jUSs").inner_text()
    shopping_data = {
        "Point": point,
        "Duration": extract_and_convert_duration(duration_text),
        "Item's list": dataframe.to_dict(orient="index"),
    }

    file_path = Path(CONFIG["SHOPPING_FILE"])
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(shopping_data, file, indent=4, ensure_ascii=False)
