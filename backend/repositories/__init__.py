"""Repository package.

MongoRepository is the runtime storage backend.
Legacy JSON repository classes remain in DataRepository.py for migration/compat tools.
"""

from . import MongoRepository

__all__ = ["MongoRepository"]
