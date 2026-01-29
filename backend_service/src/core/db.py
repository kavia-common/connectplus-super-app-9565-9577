from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from src.core.settings import get_settings


@lru_cache(maxsize=1)
def _mongo_client() -> MongoClient:
    """Create a singleton MongoClient.

    MongoClient is thread-safe; caching prevents connection storms.
    """
    settings = get_settings()
    return MongoClient(settings.mongodb_uri)


# PUBLIC_INTERFACE
def get_db() -> Database[Any]:
    """Get the MongoDB database handle.

    Returns:
        pymongo.database.Database: Database instance.
    """
    settings = get_settings()
    return _mongo_client()[settings.mongodb_db]
