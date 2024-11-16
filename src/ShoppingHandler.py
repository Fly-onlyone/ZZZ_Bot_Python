import re
from datetime import datetime, timedelta

from src.RetryHelper import RetryHelper


def calculate_return_time(input_time_str):
    # Parse the input string (format: "hour:min:sec")
    input_time_parts = list(map(int, input_time_str.split(':')))

    # Extract the hours, minutes, and seconds from the input
    input_hours = input_time_parts[0]
    input_minutes = input_time_parts[1]
    input_seconds = input_time_parts[2]

    # Create a timedelta from the input
    time_delta = timedelta(hours=input_hours, minutes=input_minutes, seconds=input_seconds)

    # Get the current time
    current_time = datetime.now()

    # Calculate the return time by adding the time delta to the current time
    return_time = current_time + time_delta

    # Format the return time in the format "hour:min dd/mm/yy"
    return return_time.strftime('%H:%M %d/%m/%y')


def check_and_process_item(page, item_locator):
    # Get the current points
    current_point_text = page.locator(".txt-EK942w").nth(1).inner_text()
    current_point = int(current_point_text.replace(',', ''))  # Assume it's a comma-separated number

    # Get the shopping button and screen locators
    shopping_button_locator = page.get_by_role("img").nth(1)
    screen_locator = page.locator(".wrapper-O3T67n")

    # Ensure the button is visible on the screen
    RetryHelper.retry_until_screen_appears(screen_locator, shopping_button_locator)

    # Get the item price
    item_price_text = item_locator.locator('.itemPriceNum-cd1EE-').inner_text()
    item_price = int(item_price_text.replace(',', ''))  # Assume it's a comma-separated number

    # Get the shopping button text
    shopping_button_text = item_locator.locator('.itemBtn-gTL1Rd').inner_text()

    # Compare current points with item price
    if current_point > item_price:
        # Check if the shopping button text matches the hour:min:sec format
        time_pattern = re.compile(r'^\d{1,2}:\d{2}:\d{2}$')

        if time_pattern.match(shopping_button_text):
            # Calculate and print the return time
            return_time = calculate_return_time(shopping_button_text)
            print("Return time:", return_time)
        else:
            # Click the shopping button if it doesn't contain a time
            item_locator.locator('.itemBtn-gTL1Rd').click()
            print("Button clicked")
