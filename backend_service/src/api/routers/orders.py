from __future__ import annotations

from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.database import Database

from src.core.auth import AuthUser, get_current_user, require_roles
from src.core.db import get_db
from src.core.utils import now_utc, oid, serialize_doc
from src.models.orders import OrderCreateIn, OrderOut, OrderStatusUpdateIn

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def _pick_engineer_for_area(db: Database, pincode: str) -> Optional[dict]:
    # lowest workload ACTIVE engineer who can install in that area
    return db.engineers.find_one(
        {"status": "ACTIVE", "areas": pincode, "skills": "install"},
        sort=[("workload", 1)],
    )


@router.post(
    "",
    response_model=OrderOut,
    summary="Create order (setup request)",
    description="Create a new connection setup order; auto-assign an engineer based on pincode availability and lowest workload.",
    operation_id="createOrder",
)
def create_order(
    body: OrderCreateIn,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    plan = db.plans.find_one({"_id": oid(body.plan_id), "status": "ACTIVE"})
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan_id")

    ts = now_utc()
    engineer = _pick_engineer_for_area(db, body.pincode)
    assigned_engineer_id: Optional[ObjectId] = engineer["_id"] if engineer else None

    order_doc = {
        "user_id": user.user_id,
        "plan_id": body.plan_id,
        "address": body.address,  # PII: only owner/admin/agent will see it
        "pincode": body.pincode,
        "price": int(plan["price"]),
        "status": "scheduled" if assigned_engineer_id else "scheduled",
        "slot": body.preferred_slot,
        "assigned_engineer_id": str(assigned_engineer_id) if assigned_engineer_id else None,
        "timeline": [{"status": "scheduled", "ts": ts, "by": user.user_id}],
        "created_at": ts,
        "updated_at": ts,
    }
    res = db.orders.insert_one(order_doc)

    # increment workload if assigned
    if assigned_engineer_id:
        db.engineers.update_one({"_id": assigned_engineer_id}, {"$inc": {"workload": 1}, "$set": {"updated_at": ts}})

    doc = db.orders.find_one({"_id": res.inserted_id})
    return OrderOut(**serialize_doc(doc))


@router.get(
    "",
    response_model=List[OrderOut],
    summary="List my orders",
    description="List orders for the current user (PII safe).",
    operation_id="listOrdersForUser",
)
def list_orders_for_user(
    user: AuthUser = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db),
):
    docs = list(db.orders.find({"user_id": user.user_id}).sort("created_at", -1).limit(limit))
    return [OrderOut(**serialize_doc(d)) for d in docs]


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    summary="Get order by id",
    description="Get order by id. Only the owner or admin/agent can access.",
    operation_id="getOrderById",
)
def get_order_by_id(
    order_id: str,
    user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.orders.find_one({"_id": oid(order_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")

    is_owner = doc.get("user_id") == user.user_id
    is_privileged = any(r in user.roles for r in ["admin", "agent", "engineer"])
    if not (is_owner or is_privileged):
        raise HTTPException(status_code=403, detail="Not authorized")

    # PII protection: if not owner/privileged, we'd strip address, but they can't reach here.
    return OrderOut(**serialize_doc(doc))


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    summary="Update order status",
    description="Update an order status. Only admin/agent/engineer can update.",
    operation_id="updateOrderStatus",
)
def update_order_status(
    order_id: str,
    body: OrderStatusUpdateIn,
    _: AuthUser = Depends(require_roles(["admin", "agent", "engineer"])),
    db: Database = Depends(get_db),
):
    allowed = {"scheduled", "in_progress", "completed", "cancelled"}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    ts = now_utc()
    doc = db.orders.find_one_and_update(
        {"_id": oid(order_id)},
        {
            "$set": {"status": body.status, "updated_at": ts},
            "$push": {"timeline": {"status": body.status, "ts": ts, "by": "staff"}},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut(**serialize_doc(doc))
