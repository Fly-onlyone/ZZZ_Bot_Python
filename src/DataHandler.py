import json
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypeVar, Type

T = TypeVar("T", bound="Serializable")


class Serializable:
    """Base class for enabling save and load methods."""

    def save(self, file_path: str):
        """Save instance data to a JSON file."""
        with open(file_path, "w") as f:
            json.dump(asdict(self), f, indent=4)

    @classmethod
    def load(cls: Type[T], file_path: str) -> T:
        """Load instance data from a JSON file or create a default one."""
        file_path = Path(file_path)
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            default_instance = cls()
            default_instance.save(file_path)
            return default_instance

        with open(file_path, "r") as f:
            data = json.load(f)
        return cls(**data)


def prepare_mission_data(output_folder: str, output_file: str):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load previous mission data
    previous_data = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as file:
            previous_data = json.load(file)

    # Get today's date in the format dd/mm/yyyy
    today_str = datetime.now().strftime("%d/%m/%Y")

    # Check if today's data already exists and skip finished missions
    todays_data = next(
        (item for item in previous_data if item["day"] == today_str), None
    )
    if not todays_data:
        todays_data = {
            "day": today_str,
            "check_in": "Link isn't opened",
            "missions": [],
        }
        previous_data.append(todays_data)

    return previous_data, todays_data


def maintain_mission_data(previous_data: list, output_file: str, todays_data: dict):
    # Ensure today's data is updated correctly
    if previous_data and previous_data[-1]["day"] == todays_data["day"]:
        previous_data[-1] = todays_data  # Update latest day's data
    else:
        previous_data.append(todays_data)  # Add new day if not found

    # Maintain a maximum of 5 days' worth of data
    if len(previous_data) > 5:
        previous_data = previous_data[-5:]  # Keep only the last 5 elements

    # Save the updated data back to the JSON file
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(previous_data, file, ensure_ascii=False, indent=2)

    print("✅ Mission data saved with updated check-in result.")


def load_shopping_data(file_path):
    """Load shopping data from the specified file path."""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return None


def save_shopping_data(file_path, shopping_data):
    """
    Update or add shopping data in the specified file path without deleting existing key-value pairs.

    Parameters:
        file_path (Path): Path to the JSON file.
        shopping_data (dict): New shopping data to update or add.
    """
    file_path = Path(file_path)

    # Ensure the parent directory exists
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data if the file exists
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Update existing data with new shopping data
    existing_data.update(shopping_data)

    # Save the updated data back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, indent=4, ensure_ascii=False)


def save_redeem_data(item_name, code_text, current_day, redeem_file_path, state):
    redeem_data = load_redeem_data(redeem_file_path)

    # Filter out entries older than 30 days
    today = datetime.strptime(current_day, "%H:%M %d/%m/%Y")
    thirty_days_ago = today - timedelta(days=30)

    filtered_data = [
        entry
        for entry in redeem_data
        if isinstance(entry, dict)
        and "day" in entry
        and datetime.strptime(entry["day"], "%H:%M %d/%m/%Y") > thirty_days_ago
    ]

    # Add new entry
    new_entry = {
        "item_name": item_name,
        "code": code_text,
        "day": current_day,
        "state": state,  # Success or failure
    }
    filtered_data.append(new_entry)

    # Save updated data back to file
    redeem_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(redeem_file_path, "w", encoding="utf-8") as file:
        json.dump(filtered_data, file, indent=4, ensure_ascii=False)

    print(f"Redeem data saved to {redeem_file_path}")


def load_redeem_data(redeem_file_path):
    # Load existing redeem data
    if redeem_file_path.exists():
        with open(redeem_file_path, "r", encoding="utf-8") as file:
            try:
                redeem_data = json.load(file)
                if not isinstance(redeem_data, list):
                    redeem_data = []  # Ensure it's a list
            except json.JSONDecodeError:
                redeem_data = []
    else:
        redeem_data = []
    return redeem_data
