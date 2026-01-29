from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import HTTPException


# PUBLIC_INTERFACE
def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


# PUBLIC_INTERFACE
def oid(value: str) -> ObjectId:
    """Parse a string into a MongoDB ObjectId.

    Raises:
        HTTPException: 400 if invalid.
    """
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")


# PUBLIC_INTERFACE
def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Serialize a MongoDB document to JSON-friendly dict (ObjectId -> str)."""
    if doc is None:
        return None
    out: Dict[str, Any] = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    # convert common ObjectId fields if present
    for k, v in list(out.items()):
        if isinstance(v, ObjectId):
            out[k] = str(v)
    return out
