"""
Repositories Package

Contains repository pattern implementations for data access.
Repositories abstract storage mechanisms and provide clean data access APIs.
"""

from .DataRepository import (
    IRepository,
    JsonFileRepository,
    SettingsRepository,
    ShoppingRepository,
)

__all__ = [
    "IRepository",
    "JsonFileRepository",
    "SettingsRepository",
    "ShoppingRepository",
]
