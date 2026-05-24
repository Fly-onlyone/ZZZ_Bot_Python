from core.GlobalVar import accounts, ensure_accounts_loaded
from playwright.sync_api import Page


def run(page: Page):
    ensure_accounts_loaded()

    page.locator("#hyv-account-frame").content_frame.locator('input[name="username"]').fill(
        accounts.hoyo_username
    )
    page.locator("#hyv-account-frame").content_frame.locator('input[name="password"]').fill(
        accounts.hoyo_password
    )
    page.locator("#hyv-account-frame").content_frame.get_by_role("button", name="Log In").click()
    page.wait_for_timeout(5000)
