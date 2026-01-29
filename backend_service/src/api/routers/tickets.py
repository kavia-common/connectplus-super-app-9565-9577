from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.database import Database

from src.core.auth import AuthUser, get_current_user, require_roles
from src.core.db import get_db
from src.core.utils import now_utc, oid, serialize_doc
from src.models.tickets import (
    TicketAssignIn,
    TicketCommentIn,
    TicketCreateIn,
    TicketOut,
    TicketStatusUpdateIn,
)

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketOut,
    summary="Create ticket",
    description="Create a support ticket for the current user.",
    operation_id="createTicket",
)
def create_ticket(
    body: TicketCreateIn,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    ts = now_utc()
    doc = {
        "user_id": user.user_id,
        "issue_type": body.category,
        "severity": "medium",
        "status": "open",
        "assigned_to": None,
        "notes": [{"ts": ts, "by": user.user_id, "type": "created", "message": body.description}],
        "attachments": body.attachments or [],
        "created_at": ts,
        "updated_at": ts,
    }
    res = db.tickets.insert_one(doc)
    saved = db.tickets.find_one({"_id": res.inserted_id})
    return TicketOut(**serialize_doc(saved))


@router.get(
    "",
    response_model=List[TicketOut],
    summary="List my tickets",
    description="List tickets for the current user.",
    operation_id="listTicketsForUser",
)
def list_tickets_for_user(
    user: AuthUser = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db),
):
    docs = list(db.tickets.find({"user_id": user.user_id}).sort("created_at", -1).limit(limit))
    return [TicketOut(**serialize_doc(d)) for d in docs]


@router.get(
    "/{ticket_id}",
    response_model=TicketOut,
    summary="Get ticket by id",
    description="Get a ticket by id. Owner or admin/agent/engineer only.",
    operation_id="getTicketById",
)
def get_ticket_by_id(
    ticket_id: str,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.tickets.find_one({"_id": oid(ticket_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_owner = doc.get("user_id") == user.user_id
    is_privileged = any(r in user.roles for r in ["admin", "agent", "engineer"])
    if not (is_owner or is_privileged):
        raise HTTPException(status_code=403, detail="Not authorized")

    return TicketOut(**serialize_doc(doc))


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketOut,
    summary="Update ticket status",
    description="Update ticket status (open, assigned, in_progress, resolved, closed). Owner can only close; staff can move workflow forward.",
    operation_id="updateTicketStatus",
)
def update_ticket_status(
    ticket_id: str,
    body: TicketStatusUpdateIn,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    allowed = {"open", "assigned", "in_progress", "resolved", "closed"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    doc = db.tickets.find_one({"_id": oid(ticket_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_owner = doc.get("user_id") == user.user_id
    is_staff = any(r in user.roles for r in ["admin", "agent", "engineer"])

    if body.status == "closed" and not (is_owner or is_staff):
        raise HTTPException(status_code=403, detail="Not authorized to close")
    if body.status != "closed" and not is_staff:
        raise HTTPException(status_code=403, detail="Only staff can update workflow status")

    ts = now_utc()
    updated = db.tickets.find_one_and_update(
        {"_id": oid(ticket_id)},
        {
            "$set": {"status": body.status, "updated_at": ts},
            "$push": {"notes": {"ts": ts, "by": user.user_id, "type": "status", "message": body.status}},
        },
        return_document=ReturnDocument.AFTER,
    )
    return TicketOut(**serialize_doc(updated))


@router.post(
    "/{ticket_id}/assign",
    response_model=TicketOut,
    summary="Assign ticket",
    description="Assign a ticket to an agent/engineer. Staff only.",
    operation_id="assignTicket",
)
def assign_ticket(
    ticket_id: str,
    body: TicketAssignIn,
    _: AuthUser = Depends(require_roles(["admin", "agent", "engineer"])),
    db: Database = Depends(get_db),
):
    ts = now_utc()
    updated = db.tickets.find_one_and_update(
        {"_id": oid(ticket_id)},
        {
            "$set": {
                "assigned_to": {"user_id": body.assigned_to_user_id},
                "status": "assigned",
                "updated_at": ts,
            },
            "$push": {"notes": {"ts": ts, "by": "staff", "type": "assign", "message": body.assigned_to_user_id}},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketOut(**serialize_doc(updated))


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketOut,
    summary="Add ticket comment",
    description="Add an update/comment to a ticket. Owner or staff.",
    operation_id="addTicketComment",
)
def add_ticket_comment(
    ticket_id: str,
    body: TicketCommentIn,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.tickets.find_one({"_id": oid(ticket_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_owner = doc.get("user_id") == user.user_id
    is_privileged = any(r in user.roles for r in ["admin", "agent", "engineer"])
    if not (is_owner or is_privileged):
        raise HTTPException(status_code=403, detail="Not authorized")

    ts = now_utc()
    updated = db.tickets.find_one_and_update(
        {"_id": oid(ticket_id)},
        {
            "$set": {"updated_at": ts},
            "$push": {"notes": {"ts": ts, "by": user.user_id, "type": "comment", "message": body.message}},
        },
        return_document=ReturnDocument.AFTER,
    )
    return TicketOut(**serialize_doc(updated))
