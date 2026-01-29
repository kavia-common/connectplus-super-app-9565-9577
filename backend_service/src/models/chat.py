from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatSendIn(BaseModel):
    """Chat send request."""
    message: str = Field(..., min_length=1, description="User message text.")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional contextual payload.")


class ChatSendOut(BaseModel):
    """Chat send response."""
    reply: str = Field(..., description="AI assistant reply text.")
    suggested_actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Optional suggested actions from AI (buttons/cards).",
    )
    conversation_id: str = Field(..., description="Conversation id.")
    message_id: str = Field(..., description="Stored user message id.")
    reply_message_id: str = Field(..., description="Stored AI message id.")


class ChatMessageOut(BaseModel):
    """Chat message record."""
    id: str = Field(..., description="Message id.")
    sender: str = Field(..., description="user|ai|system.")
    text: Optional[str] = Field(None, description="Text content.")
    payload: Optional[Dict[str, Any]] = Field(None, description="Optional structured payload.")
    created_at: datetime = Field(..., description="Timestamp.")


class ChatHistoryOut(BaseModel):
    """Chat history response."""
    conversation_id: str = Field(..., description="Conversation id.")
    user_id: str = Field(..., description="Owner user id.")
    messages: List[ChatMessageOut] = Field(default_factory=list, description="Message page.")
    next_cursor: Optional[str] = Field(None, description="Pagination cursor (message id).")
