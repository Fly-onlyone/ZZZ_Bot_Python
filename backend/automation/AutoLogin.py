from playwright.sync_api import Page

from core.GlobalVar import accounts


def run(page: Page):

    page.locator("#hyv-account-frame").content_frame.locator(
        'input[name="username"]'
    ).fill(accounts.hoyo_username)
    page.locator("#hyv-account-frame").content_frame.locator(
        'input[name="password"]'
    ).fill(accounts.hoyo_password)
    page.locator("#hyv-account-frame").content_frame.get_by_role(
        "button", name="Log In"
    ).click()
    page.wait_for_timeout(5000)
