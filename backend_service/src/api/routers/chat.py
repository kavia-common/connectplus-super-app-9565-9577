from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from src.core.auth import AuthUser, get_current_user
from src.core.db import get_db
from src.core.rate_limit import InMemoryRateLimiter, RateLimitConfig
from src.core.settings import get_settings
from src.core.utils import now_utc, oid, serialize_doc
from src.models.chat import ChatHistoryOut, ChatMessageOut, ChatSendIn, ChatSendOut

router = APIRouter(prefix="/api/chat", tags=["Chat"])

_settings = get_settings()
_rate_limiter = InMemoryRateLimiter(
    RateLimitConfig(limit=_settings.chat_rate_limit_per_minute, window_seconds=60)
)


def _get_or_create_conversation(db: Database, user_id: str) -> Dict[str, Any]:
    conv = db.conversations.find_one({"user_id": user_id}, sort=[("last_message_at", -1)])
    if conv:
        return conv
    ts = now_utc()
    res = db.conversations.insert_one({"user_id": user_id, "started_at": ts, "last_message_at": ts, "meta": {}})
    return db.conversations.find_one({"_id": res.inserted_id})


def _store_message(db: Database, conversation_id: ObjectId, sender: str, text: Optional[str], payload: Optional[dict]):
    ts = now_utc()
    res = db.messages.insert_one(
        {
            "conversation_id": str(conversation_id),
            "sender": sender,
            "text": text,
            "payload": payload,
            "created_at": ts,
        }
    )
    db.conversations.update_one({"_id": conversation_id}, {"$set": {"last_message_at": ts}})
    return db.messages.find_one({"_id": res.inserted_id})


async def _call_ai_engine(user: AuthUser, message: str, context: Optional[dict]) -> Dict[str, Any]:
    # Contract: POST {message, context, user_id}. ai_nlp_engine should respond with:
    # { reply: str, suggested_actions?: [...] }
    url = f"{_settings.ai_engine_base_url.rstrip('/')}/webhook"
    payload = {"message": message, "context": context or {}, "user_id": user.user_id}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="AI engine error")
        data = resp.json()
        if not isinstance(data, dict) or "reply" not in data:
            # Keep contract stable even if AI engine changes
            raise HTTPException(status_code=502, detail="AI engine response invalid")
        return data


@router.post(
    "/send",
    response_model=ChatSendOut,
    summary="Send chat message",
    description="Send a message to ai_nlp_engine, persist the conversation + turns, and return AI reply + suggested actions.",
    operation_id="chatSend",
)
async def chat_send(
    body: ChatSendIn,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    _rate_limiter.check(user.user_id)

    conv = _get_or_create_conversation(db, user.user_id)
    conv_id = conv["_id"]

    user_msg = _store_message(db, conv_id, "user", body.message, {"context": body.context} if body.context else None)

    ai_data = await _call_ai_engine(user, body.message, body.context)
    reply_text = str(ai_data.get("reply", ""))
    suggested_actions = ai_data.get("suggested_actions") or []
    if not isinstance(suggested_actions, list):
        suggested_actions = []

    ai_msg = _store_message(
        db,
        conv_id,
        "ai",
        reply_text,
        {"suggested_actions": suggested_actions} if suggested_actions else None,
    )

    return ChatSendOut(
        reply=reply_text,
        suggested_actions=suggested_actions,
        conversation_id=str(conv_id),
        message_id=str(user_msg["_id"]),
        reply_message_id=str(ai_msg["_id"]),
    )


@router.get(
    "/history",
    response_model=ChatHistoryOut,
    summary="Get chat history",
    description="Fetch chat history for current user's latest conversation (cursor pagination by message id).",
    operation_id="chatHistory",
)
def chat_history(
    user: AuthUser = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="Message id cursor (fetch messages before this id)."),
    db: Database = Depends(get_db),
):
    conv = db.conversations.find_one({"user_id": user.user_id}, sort=[("last_message_at", -1)])
    if not conv:
        return ChatHistoryOut(conversation_id="", user_id=user.user_id, messages=[], next_cursor=None)

    q: Dict[str, Any] = {"conversation_id": str(conv["_id"])}
    if cursor:
        q["_id"] = {"$lt": oid(cursor)}

    docs = list(db.messages.find(q).sort("_id", -1).limit(limit))
    # reverse to chronological
    docs = list(reversed(docs))

    messages = [
        ChatMessageOut(
            id=str(d["_id"]),
            sender=d.get("sender", "system"),
            text=d.get("text"),
            payload=d.get("payload"),
            created_at=d.get("created_at"),
        )
        for d in docs
    ]

    next_cursor = str(docs[0]["_id"]) if docs and len(docs) == limit else None
    return ChatHistoryOut(
        conversation_id=str(conv["_id"]),
        user_id=user.user_id,
        messages=messages,
        next_cursor=next_cursor,
    )
