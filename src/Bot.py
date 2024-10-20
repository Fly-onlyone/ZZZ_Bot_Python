import os
import json
from playwright.sync_api import sync_playwright
from MissionHelper import count_mission, doing_mission, maintain_mission_data, open_mission_screen, prepare_data

def main():
    storage_path = './authentication data/hoyo.json'
    output_folder = './output'
    output_file = os.path.join(output_folder, 'missions.json')

    # Prepare data for today's missions
    previous_data, todays_data = prepare_data(output_folder, output_file)

    # Launch the browser and start Playwright
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context_options = {"storage_state": storage_path} if os.path.exists(storage_path) else {}
        context = browser.new_context(**context_options)
        page = context.new_page()

        page.goto('https://act.hoyolab.com/bbs/event/bbs-event-20230908mimo/index.html?from=zzz&hyl_presentation_style=fullscreen&hyl_auth_required=true&hyl_portrait=true&hyl_hide_status_bar=true&lang=en-us&bbs_theme=dark&bbs_theme_device=1')

        # If storage path doesn't exist, prompt the user to log in manually
        if not os.path.exists(storage_path):
            print('Please log in manually...')
            page.wait_for_timeout(120000)  # Wait 2 minutes for manual login
            context.storage_state(path=storage_path)
            print('Login session saved.')

        open_mission_screen(page)
        mission_count = count_mission(page)
        doing_mission(mission_count, page, todays_data)
        maintain_mission_data(previous_data, output_file)


if __name__ == "__main__":
    main()
