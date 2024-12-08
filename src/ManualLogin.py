from playwright.sync_api import sync_playwright
from plyer import notification


def run(url):
    with sync_playwright() as p:
        from src.GlobalVar import CONFIG

        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=CONFIG["STORAGE_PATH"])
        page = context.new_page()
        page.goto(url)
        notification.notify(
            title="ZZZ Bot", message="Start manual login", app_icon=CONFIG["SAD_ICON"]
        )
        input("Press ENTER to exit...")
        context.storage_state(path=CONFIG["STORAGE_PATH"])
        notification.notify(
            title="ZZZ Bot", message="Login session saved", app_icon=CONFIG["ICON_PATH"]
        )
        browser.close()
