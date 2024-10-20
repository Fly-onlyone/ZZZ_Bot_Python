import json
import os
from datetime import datetime

from playwright.sync_api import Page, Locator

from RetryHelper import RetryHelper
from src.ImageProcessor import ImageProcessor


class MissionHelper:
    def __init__(self, page: Page, initial_check_in_result: str):
        self.page = page
        self.popup_detected = False
        # Set the initial check-in result. It defaults to "Link isn't opened" only if it's not already "Login Success" or "Login Failed"
        if initial_check_in_result in ['Login Success', 'Login Failed']:
            self.check_in_result = initial_check_in_result
        else:
            self.check_in_result = "Link isn't opened"

    def perform_mission(self, mission_button: Locator, max_retries: int = 5):
        retry_count = 0

        # Listen for new pages (popups)
        self.page.context.on('page', self._handle_new_page)

        while retry_count < max_retries:
            if mission_button.is_enabled():
                print('Attempting to do mission...')
                mission_button.click()

                self.page.wait_for_timeout(2000)  # Short wait for popups

                if self.popup_detected:
                    print('Popup handled, retrying mission button click...')
                    mission_button.click()
                    self.popup_detected = False

                retry_count += 1

                if retry_count < max_retries:
                    print(f'Retry {retry_count}...')

            if not self.popup_detected:
                claimed_popup = self.page.locator('text=Claimed!')
                if claimed_popup.is_visible():
                    print('Reward claimed')
                    return {'mission_completed': True, 'check_in_result': self.check_in_result}
            else:
                self.popup_detected = False

            if retry_count == max_retries:
                print('Unable to do this mission')
                return {'mission_completed': False, 'check_in_result': self.check_in_result}

            self.page.wait_for_timeout(1000)

        return {'mission_completed': False, 'check_in_result': self.check_in_result}

    def _handle_new_page(self, new_page):
        popup_url = new_page.url
        target_popup_url = 'https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html?act_id=e202406031448091&hyl_auth_required=true&hyl_presentation_style=fullscreen&utm_campaign=mimo&utm_source=h5&utm_medium=task&utm_id=8'

        if target_popup_url in popup_url:
            self.popup_detected = True
            print('Target popup detected, handling sign-in...')

            # Close the popup dialog
            new_page.locator('.components-pc-assets-__dialog_---dialog-close---3G9gO2').click()

            # Get current day number
            current_day = datetime.now().day
            day_text = f'Day {current_day}'

            # Click on the current day
            day_button = new_page.locator(f'text={day_text}')
            success_message = new_page.locator('text=Check-In Successful!')

            if RetryHelper.retry_until_screen_appears(success_message, day_button):
                print('Check-In Successful!')
                self.check_in_result = 'Login Success'
            else:
                print('Login failed')
                self.check_in_result = 'Login Failed'
        else:
            print('Closing unrelated popup...')
            new_page.close()


def prepare_data(output_folder: str, output_file: str):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load previous mission data
    previous_data = []
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as file:
            previous_data = json.load(file)

    # Get today's date in the format dd/mm/yyyy
    today_str = datetime.now().strftime('%d/%m/%Y')

    # Check if today's data already exists and skip finished missions
    todays_data = next((item for item in previous_data if item['day'] == today_str), None)
    if not todays_data:
        todays_data = {'day': today_str, 'check_in': 'Login Failed', 'missions': []}
        previous_data.append(todays_data)

    return previous_data, todays_data


def open_mission_screen(page: Page):
    target_screen_locator = page.locator('.wrapper-O3T67n')
    mission_button = page.locator('text=Carry out missions to earn')
    RetryHelper.retry_until_screen_appears(target_screen_locator, mission_button)


def count_mission(page: Page):
    mission_count = RetryHelper.retry_until_non_zero_count(page.locator('.taskItemPcLeft-Aetp6m'))
    print(f'Mission count: {mission_count}')
    return mission_count


def doing_mission(mission_count: int, page: Page, todays_data: dict):
    check_in_result = todays_data.get('check_in', "Link isn't opened")  # Get the initial check-in state

    for i in range(1, mission_count + 1):
        # Locate the mission text and button
        mission_text_locator = page.locator(f'div:nth-child({i}) > .taskItemPcLeft-Aetp6m > .top-ohhwaM')
        mission_button_locator = page.locator(f'div:nth-child({i}) > .taskItemPcRight-3-Kwr1 > .icon2-Y7R3Mu')

        mission_text = mission_text_locator.inner_text()

        # Check if the mission has already been recorded as finished today in todays_data
        existing_mission = next((mission for mission in todays_data['missions'] if mission['name'] == mission_text), None)
        if existing_mission and existing_mission['state'] == 'Finished':
            print(f'Skipping already finished mission from todays_data: {mission_text}')
            continue

        # Check the button image state
        button_image_path = f'./mission button/mission {i}.png'
        button_image = ImageProcessor(mission_button_locator, button_image_path)
        button_state = button_image.detect_button_state()

        # If the button state indicates "Finished" (tick), skip performing the mission
        if button_state == "tick":
            print(f'Skipping already finished mission (based on button state): {mission_text}')
            mission_state = 'Finished'  # Set mission state as Finished
        else:
            print(f'Starting mission: {mission_text}')
            # Perform the mission if it hasn't been marked as finished
            mission_helper = MissionHelper(page, initial_check_in_result=check_in_result)
            result = mission_helper.perform_mission(mission_button_locator)

            # Update the check-in result only if it's still in its initial state
            if check_in_result == "Link isn't opened":
                check_in_result = result['check_in_result']  # Set it only once
                print(f"Check-in result updated: {check_in_result}")

            # Set the mission state based on whether it was completed or not
            mission_state = 'Finished' if result['mission_completed'] else 'Unfinished'

        # Update todays_data with the current mission state
        if existing_mission:
            existing_mission['state'] = mission_state
        else:
            todays_data['missions'].append({'name': mission_text, 'state': mission_state})

    # Store the final check-in result in todays_data
    todays_data['check_in'] = check_in_result



def maintain_mission_data(previous_data: list, output_file: str):
    # Maintain a maximum of 5 days' worth of data
    if len(previous_data) > 5:
        previous_data = previous_data[-5:]  # Keep only the last 5 elements

    # Save the updated data back to the JSON file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(previous_data, file, ensure_ascii=False, indent=2)
    print('Mission data saved.')
