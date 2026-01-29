from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TicketCreateIn(BaseModel):
    """Create support ticket request."""
    category: str = Field(..., description="Ticket category/issue_type (e.g., speed, outage, billing).")
    description: str = Field(..., description="User problem description.")
    attachments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional attachments placeholder objects (future file upload support).",
    )


class TicketAssignIn(BaseModel):
    """Assign ticket to an agent/engineer."""
    assigned_to_user_id: str = Field(..., description="User id of agent/engineer.")


class TicketStatusUpdateIn(BaseModel):
    """Update ticket status."""
    status: str = Field(..., description="open|assigned|in_progress|resolved|closed.")


class TicketCommentIn(BaseModel):
    """Add a ticket comment/update."""
    message: str = Field(..., description="Comment text.")


class TicketOut(BaseModel):
    """Ticket response (PII-safe)."""
    id: str = Field(..., description="Ticket id.")
    user_id: str = Field(..., description="Ticket owner user id.")
    issue_type: str = Field(..., description="Issue type/category.")
    status: str = Field(..., description="Ticket status.")
    severity: str = Field(..., description="Severity (low|medium|high).")
    assigned_to: Optional[Dict[str, Any]] = Field(None, description="Assignment metadata.")
    notes: List[Dict[str, Any]] = Field(default_factory=list, description="Audit trail / comments.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")
