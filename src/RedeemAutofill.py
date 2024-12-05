from playwright.sync_api import BrowserContext
from plyer import notification

from src import RetryHelper, AutoLogin


def run(context: BrowserContext, code="AAAAAA"):
    from Bot import CONFIG

    redeem_page = context.new_page()
    redeem_page.goto("https://zenless.hoyoverse.com/redemption")
    if not redeem_page.locator(".web-cdkey-user__name").is_visible():
        login_screen = redeem_page.locator(".web-cdkey-form")
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
                    message="Capcha detected , please do manual login",
                    app_icon=CONFIG["SAD_ICON"],
                )
                return
    redeem_page.get_by_text("Select a server").click()
    redeem_page.get_by_text("Asia").click()
    redeem_page.get_by_placeholder("Enter redemption code").fill(code)
    redeem_page.get_by_text("Redeem").click()
    context.storage_state(path=CONFIG["STORAGE_PATH"])
