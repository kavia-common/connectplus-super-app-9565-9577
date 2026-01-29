from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OrderCreateIn(BaseModel):
    """Create order request."""
    plan_id: str = Field(..., description="Selected plan id.")
    address: Dict[str, Any] = Field(..., description="Installation address object.")
    pincode: str = Field(..., description="Pincode for serviceability and assignment.")
    preferred_slot: str = Field(..., description="Preferred time slot (ISO string or human readable).")


class OrderStatusUpdateIn(BaseModel):
    """Order status update request."""
    status: str = Field(..., description="New status: scheduled|in_progress|completed|cancelled.")


class OrderOut(BaseModel):
    """Order response model (PII-safe)."""
    id: str = Field(..., description="Order id.")
    user_id: str = Field(..., description="Owner user id.")
    plan_id: str = Field(..., description="Plan id.")
    price: int = Field(..., description="Price captured at order time.")
    status: str = Field(..., description="Order status.")
    slot: str = Field(..., description="Scheduled slot.")
    assigned_engineer_id: Optional[str] = Field(None, description="Assigned engineer id.")
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Status timeline events.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")
