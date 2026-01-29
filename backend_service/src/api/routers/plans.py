from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from src.core.auth import AuthUser, get_current_user
from src.core.db import get_db
from src.core.utils import oid, serialize_doc
from src.models.plans import PlanOut

router = APIRouter(prefix="/api/plans", tags=["Plans"])


@router.get(
    "",
    response_model=List[PlanOut],
    summary="List plans",
    description="List active plans with optional filters by price range, speed range, and service area (pincode).",
    operation_id="listPlans",
)
def list_plans(
    min_price: Optional[int] = Query(None, ge=0, description="Minimum monthly price."),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum monthly price."),
    min_speed: Optional[int] = Query(None, ge=0, description="Minimum speed in Mbps."),
    max_speed: Optional[int] = Query(None, ge=0, description="Maximum speed in Mbps."),
    service_area: Optional[str] = Query(None, description="Filter by pincode in plan.areas."),
    _: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    q = {"status": "ACTIVE"}
    if service_area:
        q["areas"] = service_area
    if min_price is not None or max_price is not None:
        q["price"] = {}
        if min_price is not None:
            q["price"]["$gte"] = min_price
        if max_price is not None:
            q["price"]["$lte"] = max_price
    if min_speed is not None or max_speed is not None:
        q["speed_mbps"] = {}
        if min_speed is not None:
            q["speed_mbps"]["$gte"] = min_speed
        if max_speed is not None:
            q["speed_mbps"]["$lte"] = max_speed

    docs = list(db.plans.find(q).sort("price", 1).limit(200))
    return [PlanOut(**serialize_doc(d)) for d in docs]


@router.get(
    "/{plan_id}",
    response_model=PlanOut,
    summary="Get plan by id",
    description="Fetch a single plan by its id.",
    operation_id="getPlanById",
)
def get_plan_by_id(
    plan_id: str,
    _: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    doc = db.plans.find_one({"_id": oid(plan_id)})
    if not doc or doc.get("status") != "ACTIVE":
        raise HTTPException(status_code=404, detail="Plan not found")
    return PlanOut(**serialize_doc(doc))
