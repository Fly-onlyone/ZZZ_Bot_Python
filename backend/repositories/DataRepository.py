"""
Data Repository Pattern Implementation

Centralizes data access logic following the Repository Pattern.
Provides a clean abstraction layer for data operations.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from typing import TypeVar, Generic, Dict, Any, Optional, List

logger = logging.getLogger(__name__)

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Repository interface defining data access contract.

    Follows the Repository Pattern to abstract storage mechanisms
    and enable easy testing and storage backend swapping.
    """

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """Retrieve entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieve all entities."""
        pass

    @abstractmethod
    def save(self, entity: T, id: str) -> None:
        """Save or update entity."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if entity exists."""
        pass


class JsonFileRepository(IRepository[Dict[str, Any]]):
    """
    JSON file-based repository implementation.

    Stores data as JSON files in a configured directory.
    Provides CRUD operations with automatic file management.
    """

    def __init__(self, storage_dir: str):
        """
        Initialize repository with storage directory.

        Args:
            storage_dir: Directory to store JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"JsonFileRepository initialized at {self.storage_dir}")

    def _get_file_path(self, id: str) -> Path:
        """Get full file path for an entity ID."""
        return self.storage_dir / f"{id}.json"

    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data by ID (filename without extension).

        Args:
            id: Entity identifier (e.g., 'settings', 'shopping')

        Returns:
            Dict with data or None if not found
        """
        file_path = self._get_file_path(id)
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded data from {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Retrieve all JSON files in the storage directory.

        Returns:
            List of all data dictionaries
        """
        all_data = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_id"] = file_path.stem  # Add ID from filename
                    all_data.append(data)
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        logger.info(f"Loaded {len(all_data)} files from {self.storage_dir}")
        return all_data

    def save(self, entity: Dict[str, Any], id: str) -> None:
        """
        Save data to JSON file.

        Args:
            entity: Data to save (dict or dataclass)
            id: Entity identifier (filename without extension)
        """
        file_path = self._get_file_path(id)

        try:
            # Convert dataclass to dict if needed
            if hasattr(entity, "__dataclass_fields__"):
                data = asdict(entity)
            else:
                data = entity

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            logger.info(f"Saved data to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save data to {file_path}: {e}")
            raise

    def delete(self, id: str) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity identifier

        Returns:
            bool: True if deleted, False if not found
        """
        file_path = self._get_file_path(id)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted {file_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
                return False
        else:
            logger.warning(f"Cannot delete, file not found: {file_path}")
            return False

    def exists(self, id: str) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity identifier

        Returns:
            bool: True if file exists
        """
        return self._get_file_path(id).exists()

    def get_or_create(self, id: str, default_factory: callable) -> Dict[str, Any]:
        """
        Get entity or create with default if not exists.

        Args:
            id: Entity identifier
            default_factory: Function that returns default entity

        Returns:
            Entity data
        """
        if self.exists(id):
            return self.get_by_id(id)
        else:
            default_entity = default_factory()
            self.save(default_entity, id)
            logger.info(f"Created default entity: {id}")
            return default_entity


class SettingsRepository(JsonFileRepository):
    """
    Specialized repository for application settings.

    Provides type-safe access to settings with validation.
    """

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings or create default."""
        return self.get_or_create(
            "settings",
            lambda: {
                "schedule_times": ["08:00", "20:00"],
                "exit_after_run": False,
                "hide_browser": True,
                "run_task": False,
                "gather_shopping_data": True,
                "exchange_good": True,
                "buy_all": True,
                "draw_item": True,
                "enable_hunt_mode": False,
                "stop_on_failed_exchange": False,
                "hunt_poll_max_wait_seconds": 180,
                "hunt_poll_interval_seconds": 1,
                "hunt_poll_backoff_enabled": True,
                "hunt_early_exit_on_unavailable": False,
                "theme": "purple",
            },
        )

    def update_settings(self, updates: Dict[str, Any]) -> None:
        """Update specific settings."""
        current = self.get_settings()
        current.update(updates)
        self.save(current, "settings")
        logger.info(f"Updated settings: {list(updates.keys())}")


class ShoppingRepository(JsonFileRepository):
    """
    Specialized repository for shopping data.

    Handles shopping items, selections, and hunt mode data.
    """

    def get_shopping_data(self) -> Dict[str, Any]:
        """Get shopping data."""
        return self.get_by_id("shopping") or {
            "Selected": [],
            "Hunt": [],
            "Item's list": {},
            "Purchased": [],
            "Point": 0,
            "Duration": {"Start": "", "End": ""},
        }

    def update_selected_items(self, selected: List[str]) -> None:
        """Update selected shopping items."""
        data = self.get_shopping_data()
        data["Selected"] = selected
        self.save(data, "shopping")
        logger.info(f"Updated selected items: {len(selected)} items")

    def update_hunt_items(self, hunt: List[str]) -> None:
        """Update hunt mode items."""
        data = self.get_shopping_data()
        data["Hunt"] = hunt
        self.save(data, "shopping")
        logger.info(f"Updated hunt items: {len(hunt)} items")
