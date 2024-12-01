from playwright.async_api import Playwright


def run(playwright: Playwright) -> None:
    browser = playwright.firefox.launch(headless=False)
    context = browser.new_context(storage_state="./authentication data/hoyo.json")
    page = context.new_page()
    page.goto(
        "https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?from=zzz&hyl_presentation_style=fullscreen&hyl_auth_required=true&hyl_portrait=true&hyl_hide_status_bar=true&lang=en-us&bbs_theme=dark&bbs_theme_device=1"
    )

    div_gain_code = page.locator("div.gainCodeCopyInput-QcgdvD")
    div_copy = page.locator("div.gainCodeCopyBtn-Lwk9eR")
