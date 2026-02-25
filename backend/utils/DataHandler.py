import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypeVar, Type

logger = logging.getLogger(__name__)

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
    """Load mission data from MongoDB; create today's record if missing."""
    import repositories.MongoRepository as mongo

    today_str = datetime.now().strftime("%d/%m/%Y")
    previous_data = mongo.get_missions()

    todays_data = next((d for d in previous_data if d["day"] == today_str), None)
    if not todays_data:
        todays_data = {
            "day": today_str,
            "check_in": "Link isn't opened",
            "missions": [],
        }
        previous_data.append(todays_data)

    return previous_data, todays_data


def maintain_mission_data(previous_data: list, output_file: str, todays_data: dict):
    """Upsert today's mission record in MongoDB. TTL index handles 5-day rotation."""
    import repositories.MongoRepository as mongo

    mongo.save_mission_day(todays_data)
    logger.info("Mission data saved to MongoDB.")


def load_shopping_data(file_path):
    """Load shopping data from MongoDB (file_path arg kept for compatibility)."""
    import repositories.MongoRepository as mongo

    return mongo.get_shopping()


def save_shopping_data(file_path, shopping_data):
    """Merge and save shopping data to MongoDB.

    Parameters:
        file_path: Unused (kept for call-site compatibility).
        shopping_data: New shopping data to merge into existing record.
    """
    import repositories.MongoRepository as mongo

    existing = mongo.get_shopping() or {}
    existing.update(shopping_data)
    mongo.save_shopping(existing)


def save_redeem_data(item_name, code_text, current_day, redeem_file_path, state):
    """Append a redemption entry to MongoDB. TTL index handles 30-day cleanup."""
    import repositories.MongoRepository as mongo

    entry = {
        "item_name": item_name,
        "code": code_text,
        "day": current_day,
        "state": state,
    }
    mongo.save_redemption(entry)
    logger.info("Redeem data saved to MongoDB for %s", item_name)


def load_redeem_data(redeem_file_path):
    """Load all redemption records from MongoDB (file_path arg kept for compatibility)."""
    import repositories.MongoRepository as mongo

    return mongo.get_redemptions()
