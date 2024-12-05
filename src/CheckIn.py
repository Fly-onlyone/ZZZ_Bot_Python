from datetime import datetime

import Mission
import RetryHelper


def handle_check_in(new_page):
    print("Handling sign-in...")
    # Close the popup dialog
    try:
        new_page.locator(
            ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
        ).click()
    except Exception as e:
        print(e)
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
        success_message.screenshot(path="./../screenshot/login_reward.png")
    else:
        print("Login failed")
        Mission.Mission.check_in_result = "Login Failed"
