import json
import os
from dataclasses import asdict
from datetime import datetime
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


def prepare_data(output_folder: str, output_file: str):
    # Create bot data folder if it doesn't exist
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


def maintain_mission_data(previous_data: list, output_file: str):
    # Maintain a maximum of 5 days' worth of data
    if len(previous_data) > 5:
        previous_data = previous_data[-5:]  # Keep only the last 5 elements

    # Save the updated data back to the JSON file
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(previous_data, file, ensure_ascii=False, indent=2)
    print("Mission data saved.")
