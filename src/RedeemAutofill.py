from datetime import datetime
from pathlib import Path

from playwright.sync_api import BrowserContext
from plyer import notification

import AutoLogin
import RetryHelper
from DataHandler import save_redeem_data
from GlobalVar import CONFIG, settings


def run(context: BrowserContext, code, item_name):
    current_day = datetime.now().strftime("%H:%M %d/%m/%Y")
    redeem_file_path = Path(CONFIG["REDEEM_FILE"])
    redeem_page = context.new_page()
    redeem_page.goto("https://zenless.hoyoverse.com/redemption")
    redeem_page.wait_for_timeout(5000)
    if redeem_page.get_by_text("Please Log in to Redeem").is_visible():
        login_screen = redeem_page.locator(
            "#hyv-account-frame"
        ).content_frame.get_by_text("Account Log In")
        server_select_button = redeem_page.locator(".web-cdkey-form__select--toggle")
        if RetryHelper.retry_until_screen_appears(login_screen, server_select_button):
            AutoLogin.run(redeem_page)
            if (
                redeem_page.locator("#hyv-account-frame")
                .content_frame.get_by_text("Slide to complete the puzzle")
                .is_visible()
            ):
                notification.notify(
                    title="ZZZ Bot",
                    message="Captcha detected. Please complete manual login.",
                    app_icon=CONFIG["SAD_ICON"],
                )
                return

            redeem_page.wait_for_timeout(5000)
            select_server = redeem_page.get_by_text("Select a server")
            if select_server.is_visible():
                select_server.click()
                redeem_page.get_by_text("Asia").click()

    redeem_page.get_by_placeholder("Enter redemption code").fill(code)
    redeem_page.get_by_role("button", name="Redeem").click()
    redeem_page.wait_for_timeout(5000)

    # Check if the success popup appears
    if redeem_page.get_by_text(
        "Successfully redeemed. Please claim rewards from in-game mail."
    ).is_visible():
        redeem_state = True
        notification.notify(
            title="ZZZ Bot",
            message=f"Redeemed {item_name} successfully.",
            app_icon=CONFIG["ICON_PATH"],
        )
    else:
        redeem_state = False
        notification.notify(
            title="ZZZ Bot",
            message=f"Redeemed {item_name} failed.",
            app_icon=CONFIG["SAD_ICON"],
        )
    context.storage_state(path=CONFIG["STORAGE_PATH"])

    # Save redeem data with state
    save_redeem_data(item_name, code, current_day, redeem_file_path, state=redeem_state)
    if not settings.headless_mode:
        redeem_page.wait_for_timeout(2000)
    redeem_page.close()
