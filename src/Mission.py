from datetime import datetime

from playwright.sync_api import Page, Locator

import RetryHelper
from DataHandler import maintain_mission_data
from GlobalVar import CONFIG
from ImageProcessor import ImageProcessor
from ImageProcessor import find_correct_avatar


class Mission:
    check_in_result = "Link isn't opened"

    @classmethod
    def update_check_in_result(cls, new_result, todays_data):
        """Updates check_in_result globally and in todays_data."""
        if new_result in ["Login Success", "Login Failed"]:
            cls.check_in_result = new_result
            todays_data["check_in"] = new_result  # Ensure persistent storage
            print(f"Check-in result updated: {new_result}")

    def __init__(self, page: Page, initial_check_in_result: str):
        self.page = page
        if initial_check_in_result in ["Login Success", "Login Failed"]:
            Mission.update_check_in_result(initial_check_in_result, {})

    def attach_page_listener(self):
        self.page.context.on("page", handle_pop_up)

    def perform_mission(self, mission_button: Locator, max_retries: int = 5):
        retry_count = 0

        while retry_count < max_retries:
            if mission_button.is_enabled():
                print("Attempting to do mission...")
                mission_button.click()
                self.page.wait_for_timeout(2000)  # Allow popups to appear
                retry_count += 1

                if retry_count < max_retries:
                    print(f"Retry {retry_count}...")

            # Check if the "Claimed!" popup appeared (reward was claimed)
            claimed_popup = self.page.locator("text=Claimed!")
            if claimed_popup.is_visible():
                print("Reward claimed")
                return {
                    "mission_completed": True,
                    "check_in_result": Mission.check_in_result,
                }

            if retry_count == max_retries:
                print("Unable to complete this mission.")
                return {
                    "mission_completed": False,
                    "check_in_result": Mission.check_in_result,
                }

            self.page.wait_for_timeout(1000)

        return {"mission_completed": False, "check_in_result": Mission.check_in_result}


def open_mission_screen(page: Page):
    target_screen_locator = page.locator(".wrapper-O3T67n")
    mission_button = page.locator("text=Carry out missions to earn")
    RetryHelper.retry_until_screen_appears(target_screen_locator, mission_button)


def count_mission(page: Page):
    zzz_avatar = find_correct_avatar(page)
    if not zzz_avatar:
        return 0
    zzz_avatar.click()

    mission_count = RetryHelper.retry_until_non_zero_count(
        page.locator(".taskItemPcLeft-Aetp6m")
    )
    print(f"Mission count: {mission_count}")
    return mission_count


def doing_mission(mission_count: int, page: Page, todays_data: dict):
    check_in_result = todays_data.get("check_in", "Link isn't opened")
    Mission.check_in_result = check_in_result  # Ensure consistency across instances

    if mission_count == 0:
        login_page = page.context.new_page()
        login_page.goto(
            "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
        )

        new_result = handle_check_in(login_page, todays_data)
        Mission.update_check_in_result(new_result, todays_data)

    else:
        for i in range(1, mission_count + 1):
            mission_text_locator = page.locator(
                f"div:nth-child({i}) > .taskItemPcLeft-Aetp6m > .top-ohhwaM"
            )
            mission_button_locator = page.locator(
                f"div:nth-child({i}) > .taskItemPcRight-3-Kwr1 > .icon2-Y7R3Mu"
            )

            mission_text = mission_text_locator.inner_text()

            existing_mission = next(
                (m for m in todays_data["missions"] if m["name"] == mission_text), None
            )
            if existing_mission and existing_mission["state"] == "Finished":
                print(f"Skipping already finished mission: {mission_text}")
                continue

            button_image = ImageProcessor(page, mission_button_locator)
            button_state = button_image.detect_button_state()

            if button_state == "Finished":
                print(f"Skipping already finished mission: {mission_text}")
                mission_state = "Finished"
            else:
                print(f"Starting mission: {mission_text}")
                mission_helper = Mission(page, initial_check_in_result=check_in_result)
                if i == 1:
                    mission_helper.attach_page_listener()
                result = mission_helper.perform_mission(mission_button_locator)

                if Mission.check_in_result == "Link isn't opened":
                    Mission.update_check_in_result(
                        result["check_in_result"], todays_data
                    )

                mission_state = (
                    "Finished" if result["mission_completed"] else "Unfinished"
                )

            if existing_mission:
                existing_mission["state"] = mission_state
            else:
                todays_data["missions"].append(
                    {"name": mission_text, "state": mission_state}
                )

    if Mission.check_in_result == "Link isn't opened":
        print("Wait for Check-in activity")
        page.wait_for_timeout(10000)
        todays_data["check_in"] = (
            Mission.check_in_result
        )  # 🔥 Ensure update before saving
    print(f"Final Check-in result: {Mission.check_in_result}")


def run(output_file, page, previous_data, todays_data):
    open_mission_screen(page)
    mission_count = count_mission(page)
    doing_mission(mission_count, page, todays_data)
    maintain_mission_data(previous_data, output_file, todays_data)


def handle_check_in(new_page: Page, todays_data):
    print("Handling sign-in...")
    new_page.wait_for_timeout(5000)

    # Close the popup dialog if it appears
    close_button = new_page.locator(
        ".components-pc-assets-__dialog_---dialog-close---3G9gO2"
    )
    if close_button.is_visible():
        close_button.click()

    # Get current day number
    current_day = datetime.now().day
    day_text = f"Day {current_day}"
    day_button = new_page.get_by_text(day_text, exact=True)
    success_message = new_page.locator(
        "div.components-pc-assets-__dialog_---dialog-body---1SieDs"
    )

    if RetryHelper.retry_until_screen_appears(success_message, day_button):
        print("Check-In Successful!")
        success_message.screenshot(
            path=CONFIG["SCREENSHOT_FOLDER"] + "/login_reward.png"
        )
        Mission.update_check_in_result("Login Success", todays_data)
        return "Login Success"
    else:
        print("Login failed")
        Mission.update_check_in_result("Login Failed", todays_data)
        return "Login Failed"


def handle_pop_up(new_page: Page):
    popup_url = new_page.url
    target_popup_url = (
        "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html"
    )

    if target_popup_url in popup_url:
        handle_check_in(new_page, {})
    else:
        print("Closing unrelated popup...")
    new_page.close()
