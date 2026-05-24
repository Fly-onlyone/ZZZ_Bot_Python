"""Repository package.

DataStore is the runtime storage backend (embedded SQLite).
Legacy JSON repository classes remain in DataRepository.py for test fixtures.
"""

from . import DataStore

__all__ = ["DataStore"]
