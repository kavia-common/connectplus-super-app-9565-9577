from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PlanOut(BaseModel):
    """Plan response model."""
    id: str = Field(..., description="Plan id.")
    name: str = Field(..., description="Plan name.")
    speed_mbps: int = Field(..., description="Speed in Mbps.")
    price: int = Field(..., description="Monthly price in INR.")
    areas: List[str] = Field(default_factory=list, description="Serviceable pincodes.")
    status: str = Field(..., description="Plan status (e.g., ACTIVE).")
    data_cap_gb: Optional[int] = Field(None, description="Optional data cap.")
    ott: List[str] = Field(default_factory=list, description="Optional OTT bundle identifiers.")
