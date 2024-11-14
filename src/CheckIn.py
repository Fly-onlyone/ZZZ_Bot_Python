from datetime import datetime

from playwright.sync_api import Page

from RetryHelper import RetryHelper


def handle_check_in(new_page: Page):
    """Synchronous handling of popup page when it appears."""

    # If the popup matches the target URL, handle the popup

    print('Target popup detected, handling sign-in...')

    # Close the popup dialog
    close_popup_button = new_page.locator('.components-pc-assets-__dialog_---dialog-close---3G9gO2')
    if close_popup_button.is_visible():
        close_popup_button.click()

    # Get current day number
    current_day = datetime.now().day
    day_text = f'Day {current_day}'

    # Click on the current day button
    day_button = new_page.get_by_text(day_text, exact=True)
    success_message = new_page.locator("div.components-pc-assets-__dialog_---dialog-body---1SieDs").filter(
        has_text="Check-In Successful!")

    # Retry clicking until the success message appears
    if RetryHelper.retry_until_screen_appears(success_message, day_button):
        print('Check-In Successful!')
        # self.check_in_result = 'Login Success'
        success_message.screenshot(path='./screenshot/login_reward.png')
    else:
        print('Login failed')
        # self.check_in_result = 'Login Failed'
