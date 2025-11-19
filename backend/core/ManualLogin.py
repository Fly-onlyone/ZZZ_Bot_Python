import threading
import time

from playwright.sync_api import sync_playwright

from utils import NotificationHelper
from .GlobalVar import CONFIG

playState = False
playState_lock = threading.Lock()


def run(url):
    global playState
    print(f"Run function started with URL: {url}")
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)
            context = browser.new_context(storage_state=CONFIG["STORAGE_PATH"])
            page = context.new_page()
            page.goto(url)

            print("Browser opened and navigated to:", url)

            NotificationHelper.notify(
                title="ZZZ Bot",
                message="Start manual login",
                app_icon=CONFIG["SAD_ICON"],
            )

            while True:
                with playState_lock:
                    if not playState:  # Exit the loop when playState is False
                        print("Exiting run loop; playState is now False.")
                        break
                time.sleep(1)

            # Save the session
            context.storage_state(path=CONFIG["STORAGE_PATH"])
            print("Session saved.")
            NotificationHelper.notify(
                title="ZZZ Bot",
                message="Login session saved",
                app_icon=CONFIG["ICON_PATH"],
            )
            browser.close()

    except Exception as e:
        # Log and reset playState on error
        print(f"Error in run function: {e}")
        NotificationHelper.notify(
            title="ZZZ Bot Error",
            message=f"An error occurred: {str(e)}",
            app_icon=CONFIG["SAD_ICON"],
        )
        with playState_lock:
            playState = False
