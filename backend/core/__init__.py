"""
Core Package

Core application modules including main bot logic, global variables, and configuration.
"""

# Do not import Bot here to avoid circular imports
# Bot.py should be run directly as the main entry point

from .ManualLogin import *
from .Notification import *
from .constants import *

__all__ = [
    "GlobalVar",
    "constants",
    "Notification",
    "ManualLogin",
]
