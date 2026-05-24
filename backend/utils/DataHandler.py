import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Type, TypeVar

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
    """Load mission data from the database; create today's record if missing."""
    from repositories import DataStore

    today_str = datetime.now().strftime("%d/%m/%Y")
    previous_data = DataStore.get_missions()

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
    """Upsert today's mission record; records older than 5 days are swept."""
    from repositories import DataStore

    DataStore.save_mission_day(todays_data)
    logger.info("Mission data saved to the database.")


def load_shopping_data(file_path):
    """Load shopping data from the database (file_path arg kept for compatibility)."""
    from repositories import DataStore

    return DataStore.get_shopping()


def save_shopping_data(file_path, shopping_data):
    """Merge and save shopping data to the database.

    Parameters:
        file_path: Unused (kept for call-site compatibility).
        shopping_data: New shopping data to merge into existing record.
    """
    from repositories import DataStore

    existing = DataStore.get_shopping() or {}
    existing.update(shopping_data)
    DataStore.save_shopping(existing)


def save_redeem_data(
    item_name,
    code_text,
    current_day,
    redeem_file_path,
    state,
    detail=None,
    status=None,
    record_id=None,
):
    """Append a redemption entry; records older than 30 days are swept."""
    from repositories import DataStore

    entry = {
        "item_name": item_name,
        "code": code_text,
        "day": current_day,
        "state": state,
    }
    if detail:
        entry["detail"] = detail
    if status:
        entry["status"] = status

    if record_id is None:
        record_id = DataStore.save_redemption(entry)
    else:
        DataStore.update_redemption(record_id, entry)
    logger.info(
        "Redeem data saved to the database for %s with state=%s status=%s detail=%s record_id=%s",
        item_name,
        state,
        status,
        detail,
        record_id,
    )
    return record_id


def load_redeem_data(redeem_file_path):
    """Load all redemption records from the database (file_path arg kept for compatibility)."""
    from repositories import DataStore

    return DataStore.get_redemptions()
