from playwright.sync_api import Page, Locator

import RetryHelper
from CheckIn import handle_check_in
from DataHandler import maintain_mission_data
from ImageProcessor import ImageProcessor
from src.ImageProcessor import find_correct_avatar


class Mission:
    check_in_result = "Link isn't opened"

    def __init__(self, page: Page, initial_check_in_result: str):
        self.page = page
        if initial_check_in_result in ["Login Success", "Login Failed"]:
            Mission.check_in_result = initial_check_in_result

    def attach_page_listener(self):
        self.page.context.on("page", handle_pop_up)

    def perform_mission(self, mission_button: Locator, max_retries: int = 5):
        retry_count = 0

        while retry_count < max_retries:
            if mission_button.is_enabled():
                print("Attempting to do mission...")
                mission_button.click()

                # Wait briefly to allow any popups to appear
                self.page.wait_for_timeout(2000)

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

            # If max retries reached
            if retry_count == max_retries:
                print("Unable to complete this mission.")
                return {
                    "mission_completed": False,
                    "check_in_result": Mission.check_in_result,
                }

            # Short pause before retrying
            self.page.wait_for_timeout(1000)

        return {"mission_completed": False, "check_in_result": Mission.check_in_result}


def handle_pop_up(new_page: Page):
    """Synchronous handling of popup page when it appears."""
    popup_url = new_page.url
    target_popup_url = "https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_campaign=mimo&utm_source=h5&utm_medium=task&utm_id=8"

    # If the popup matches the target URL, handle the popup
    if target_popup_url in popup_url:
        handle_check_in(new_page)
    else:
        print("Closing unrelated popup...")
    new_page.close()


def open_mission_screen(page: Page):
    target_screen_locator = page.locator(".wrapper-O3T67n")
    mission_button = page.locator("text=Carry out missions to earn")
    RetryHelper.retry_until_screen_appears(target_screen_locator, mission_button)


def count_mission(page: Page):
    mission_count = RetryHelper.retry_until_non_zero_count(
        page.locator(".taskItemPcLeft-Aetp6m")
    )
    print(f"Mission count: {mission_count}")
    return mission_count


def doing_mission(mission_count: int, page: Page, todays_data: dict):
    zzz_avatar = find_correct_avatar(page)
    zzz_avatar.click()

    check_in_result = todays_data.get(
        "check_in", "Link isn't opened"
    )  # Get the initial check-in state

    for i in range(1, mission_count + 1):
        # Locate the mission text and button
        mission_text_locator = page.locator(
            f"div:nth-child({i}) > .taskItemPcLeft-Aetp6m > .top-ohhwaM"
        )
        mission_button_locator = page.locator(
            f"div:nth-child({i}) > .taskItemPcRight-3-Kwr1 > .icon2-Y7R3Mu"
        )

        mission_text = mission_text_locator.inner_text()

        # Check if the mission has already been recorded as finished today in todays_data
        existing_mission = next(
            (
                mission
                for mission in todays_data["missions"]
                if mission["name"] == mission_text
            ),
            None,
        )
        if existing_mission and existing_mission["state"] == "Finished":
            print(f"Skipping already finished mission from todays_data: {mission_text}")
            continue

        # Check the button image state
        button_image_path = f"./../mission button/mission {i}.png"
        button_image = ImageProcessor(mission_button_locator, button_image_path)
        button_state = button_image.detect_button_state()

        # If the button state indicates "Finished" (tick), skip performing the mission
        if button_state == "Finished":
            print(
                f"Skipping already finished mission (based on button state): {mission_text}"
            )
            mission_state = "Finished"  # Set mission state as Finished
        else:
            print(f"Starting mission: {mission_text}")
            # Perform the mission if it hasn't been marked as finished
            mission_helper = Mission(page, initial_check_in_result=check_in_result)
            if i == 1:
                mission_helper.attach_page_listener()
            result = mission_helper.perform_mission(mission_button_locator)

            # Update the check-in result only if it's still in its initial state
            if check_in_result == "Link isn't opened":
                check_in_result = result["check_in_result"]  # Set it only once
                print(f"Check-in result updated: {check_in_result}")

            # Set the mission state based on whether it was completed or not
            mission_state = "Finished" if result["mission_completed"] else "Unfinished"

        # Update todays_data with the current mission state
        if existing_mission:
            existing_mission["state"] = mission_state
        else:
            todays_data["missions"].append(
                {"name": mission_text, "state": mission_state}
            )

    # Store the final check-in result in todays_data
    todays_data["check_in"] = check_in_result


def run(output_file, page, previous_data, todays_data):
    open_mission_screen(page)
    mission_count = count_mission(page)
    doing_mission(mission_count, page, todays_data)
    maintain_mission_data(previous_data, output_file)
