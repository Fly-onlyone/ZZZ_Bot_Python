import json
import os
from datetime import datetime


def prepare_data(output_folder: str, output_file: str):
    # Create bot data folder if it doesn't exist
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
        todays_data = {'day': today_str, 'check_in': "Link isn't opened", 'missions': []}
        previous_data.append(todays_data)

    return previous_data, todays_data


def maintain_mission_data(previous_data: list, output_file: str):
    # Maintain a maximum of 5 days' worth of data
    if len(previous_data) > 5:
        previous_data = previous_data[-5:]  # Keep only the last 5 elements

    # Save the updated data back to the JSON file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(previous_data, file, ensure_ascii=False, indent=2)
    print('Mission data saved.')
