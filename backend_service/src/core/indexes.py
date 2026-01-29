from __future__ import annotations

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from src.core.db import get_db


# PUBLIC_INTERFACE
def ensure_indexes(db: Database) -> None:
    """Create required MongoDB indexes (idempotent).

    This matches database_service/mongodb_schema.md guidance.
    """
    # users
    db.users.create_index([("mobile_enc", ASCENDING)], unique=True, name="uniq_mobile_enc")
    db.users.create_index(
        [("email_enc", ASCENDING)],
        unique=True,
        name="uniq_email_enc",
        partialFilterExpression={"email_enc": {"$ne": None}},
    )

    # plans
    db.plans.create_index([("areas", ASCENDING)], name="idx_plans_areas")
    db.plans.create_index([("price", ASCENDING)], name="idx_plans_price")
    db.plans.create_index([("speed_mbps", ASCENDING)], name="idx_plans_speed")
    db.plans.create_index([("status", ASCENDING)], name="idx_plans_status")

    # service_areas
    db.service_areas.create_index([("pincode", ASCENDING)], unique=True, name="uniq_servicearea_pincode")
    db.service_areas.create_index([("status", ASCENDING)], name="idx_servicearea_status")

    # engineers
    db.engineers.create_index([("areas", ASCENDING)], name="idx_engineers_areas")
    db.engineers.create_index([("skills", ASCENDING)], name="idx_engineers_skills")
    db.engineers.create_index([("status", ASCENDING), ("workload", ASCENDING)], name="idx_engineers_status_workload")

    # orders
    db.orders.create_index([("user_id", ASCENDING)], name="idx_orders_user")
    db.orders.create_index([("status", ASCENDING)], name="idx_orders_status")
    db.orders.create_index([("assigned_engineer_id", ASCENDING)], name="idx_orders_assigned_engineer")

    # tickets
    db.tickets.create_index([("user_id", ASCENDING)], name="idx_tickets_user")
    db.tickets.create_index([("status", ASCENDING)], name="idx_tickets_status")
    db.tickets.create_index([("issue_type", ASCENDING)], name="idx_tickets_issue_type")
    db.tickets.create_index([("created_at", DESCENDING)], name="idx_tickets_created_at")

    # conversations/messages
    db.conversations.create_index([("user_id", ASCENDING)], name="idx_conversations_user")
    db.conversations.create_index([("last_message_at", DESCENDING)], name="idx_conversations_last_message_at")
    db.messages.create_index([("conversation_id", ASCENDING)], name="idx_messages_conversation")
    db.messages.create_index([("created_at", DESCENDING)], name="idx_messages_created_at")


# PUBLIC_INTERFACE
def ensure_indexes_startup() -> None:
    """Convenience startup hook to ensure indexes exist."""
    ensure_indexes(get_db())
