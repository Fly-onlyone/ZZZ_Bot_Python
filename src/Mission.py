from datetime import datetime

from playwright.sync_api import Page, Locator

import RetryHelper
from DataHandler import maintain_mission_data
from GlobalVar import CONFIG
from ImageProcessor import ImageProcessor, find_correct_avatar


# --- Check-in Handler ---
def handle_check_in(new_page: Page, todays_data: dict):
    """
    Performs the daily check-in and updates todays_data['check_in'] directly.
    """
    print("Handling sign-in...")
    new_page.wait_for_timeout(5000)
    # Close any dialog
    try:
        close_btn = new_page.locator(
            ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
        )
        if close_btn.is_visible():
            close_btn.click()
    except Exception:
        pass

    # Compute current day label
    today = datetime.now().day
    day_text = f"Day {today}"
    # Click on the current day button
    day_btn = new_page.get_by_text(day_text, exact=True)
    success_msg = new_page.locator(
        "div.components-pc-assets-__dialog_---dialog-body---1SieDs"
    )

    # Retry until success appears
    clicked = RetryHelper.retry_until_screen_appears(success_msg, day_btn)
    if clicked:
        print("Check-In Successful!")
        todays_data["check_in"] = "Login Success"
        success_msg.screenshot(path=CONFIG["SCREENSHOT_FOLDER"] + "/login_reward.png")
    else:
        print("Login Failed")
        todays_data["check_in"] = "Login Failed"


# --- Mission Logic ---
class Mission:
    def __init__(self, page: Page, todays_data: dict):
        self.page = page
        self.todays_data = todays_data

    def attach_page_listener(self):
        # Pop-up handler will update todays_data when check-in occurs
        self.page.context.on(
            "page", lambda new_page: handle_pop_up(new_page, self.todays_data)
        )

    def perform_mission(self, mission_button: Locator, max_retries: int = 5) -> bool:
        retries = 0
        while retries < max_retries:
            if mission_button.is_enabled():
                mission_button.click()
                self.page.wait_for_timeout(2000)
                retries += 1
            # Check for "Claimed!" popup
            if self.page.locator("text=Claimed!").is_visible():
                print("Reward claimed")
                return True
            if retries >= max_retries:
                print("Unable to complete this mission.")
                return False
            self.page.wait_for_timeout(1000)
        return False


def handle_pop_up(new_page: Page, todays_data: dict):
    target_url = "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
    if target_url in new_page.url:
        handle_check_in(new_page, todays_data)
    else:
        print("Closing unrelated popup...")
    new_page.close()


def open_mission_screen(page: Page):
    target = page.locator(".wrapper-O3T67n")
    btn = page.locator("text=Carry out missions to earn")
    RetryHelper.retry_until_screen_appears(target, btn)


def count_mission(page: Page) -> int:
    avatar = find_correct_avatar(page)
    if not avatar:
        return 0
    avatar.click()
    count = RetryHelper.retry_until_non_zero_count(
        page.locator(".taskItemPcLeft-Aetp6m")
    )
    print(f"Mission count: {count}")
    return count


def doing_mission(mission_count: int, page: Page, todays_data: dict):
    # If no missions unlocked, perform check-in directly
    if mission_count == 0:
        p = page.context.new_page()
        p.goto(
            "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091&hyl_auth_required=true"
        )
        handle_check_in(p, todays_data)
    else:
        for idx in range(1, mission_count + 1):
            text_loc = page.locator(
                f"div:nth-child({idx}) > .taskItemPcLeft-Aetp6m > .top-ohhwaM"
            )
            btn_loc = page.locator(
                f"div:nth-child({idx}) > .taskItemPcRight-3-Kwr1 > .icon2-Y7R3Mu"
            )
            name = text_loc.inner_text()

            # Skip if recorded finished
            existing = next(
                (m for m in todays_data.get("missions", []) if m["name"] == name), None
            )
            if existing and existing.get("state") == "Finished":
                continue

            # Detect button state
            state = ImageProcessor(page, btn_loc).detect_button_state()
            if state == "Finished":
                mission_done = True
            else:
                if idx == 1:
                    Mission(page, todays_data).attach_page_listener()
                mission_done = Mission(page, todays_data).perform_mission(btn_loc)

            # Update record
            state_str = "Finished" if mission_done else "Unfinished"
            if existing:
                existing["state"] = state_str
            else:
                todays_data.setdefault("missions", []).append(
                    {"name": name, "state": state_str}
                )

    # todays_data["check_in"] is updated in handle_check_in
    if todays_data["check_in"] == "Link isn't opened":
        print("Mission check failed. Waiting for 5 seconds...")
        page.wait_for_timeout(5000)
    print("Today check-in status:", todays_data["check_in"])


def run(output_file: str, page: Page, previous_data: dict, todays_data: dict):
    open_mission_screen(page)
    cnt = count_mission(page)
    doing_mission(cnt, page, todays_data)
    maintain_mission_data(previous_data, output_file, todays_data)
