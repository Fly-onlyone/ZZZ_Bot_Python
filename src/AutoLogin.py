from playwright.sync_api import Page


def run(page: Page):
    from src.GlobalVar import accounts

    page.locator("#hyv-account-frame").content_frame.locator(
        'input[name="username"]'
    ).fill(accounts.username + "@gmail.com")
    page.locator("#hyv-account-frame").content_frame.locator(
        'input[name="password"]'
    ).fill(accounts.password)
    page.locator("#hyv-account-frame").content_frame.get_by_role(
        "button", name="Log In"
    ).click()
    page.wait_for_timeout(5000)
