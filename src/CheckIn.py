from datetime import datetime

from playwright.sync_api import Page

import Mission
import RetryHelper
from GlobalVar import CONFIG


def handle_check_in(new_page: Page):
    print("Handling sign-in...")
    new_page.wait_for_timeout(5000)

    # Close the popup dialog
    close_button = new_page.locator(
        ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
    )
    if close_button.is_visible():
        close_button.click()

    # Get current day number
    current_day = datetime.now().day
    day_text = f"Day {current_day}"
    # Click on the current day button
    day_button = new_page.get_by_text(day_text, exact=True)
    success_message = new_page.locator(
        "div.components-pc-assets-__dialog_---dialog-body---1SieDs"
    )
    # Retry clicking until the success message appears
    if RetryHelper.retry_until_screen_appears(success_message, day_button):
        print("Check-In Successful!")
        Mission.Mission.check_in_result = "Login Success"
        success_message.screenshot(
            path=CONFIG["SCREENSHOT_FOLDER"] + "/login_reward.png"
        )
    else:
        print("Login failed")
        Mission.Mission.check_in_result = "Login Failed"
