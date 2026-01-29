from __future__ import annotations

from pymongo.database import Database

from src.core.utils import now_utc


# PUBLIC_INTERFACE
def seed_core_data(db: Database) -> None:
    """Seed minimal core data using idempotent upserts.

    Creates:
    - plans
    - service_areas
    - engineers
    """
    ts = now_utc()

    # Plans
    plans = [
        {
            "name": "Starter 100",
            "speed_mbps": 100,
            "price": 699,
            "data_cap_gb": None,
            "ott": [],
            "areas": ["560034", "560001"],
            "status": "ACTIVE",
        },
        {
            "name": "Night Streaming 300",
            "speed_mbps": 300,
            "price": 999,
            "data_cap_gb": None,
            "ott": ["ExampleOTT"],
            "areas": ["560034"],
            "status": "ACTIVE",
        },
        {
            "name": "Ultra 500",
            "speed_mbps": 500,
            "price": 1499,
            "data_cap_gb": None,
            "ott": ["ExampleOTT", "ExampleSports"],
            "areas": ["560001", "560034"],
            "status": "ACTIVE",
        },
    ]
    for p in plans:
        db.plans.update_one(
            {"name": p["name"]},
            {"$setOnInsert": {**p, "created_at": ts, "updated_at": ts}},
            upsert=True,
        )

    # Service areas
    service_areas = [
        {"pincode": "560034", "city": "Bengaluru", "status": "ACTIVE"},
        {"pincode": "560001", "city": "Bengaluru", "status": "ACTIVE"},
    ]
    for sa in service_areas:
        db.service_areas.update_one(
            {"pincode": sa["pincode"]},
            {"$setOnInsert": {**sa, "created_at": ts, "updated_at": ts}},
            upsert=True,
        )

    # Engineers
    engineers = [
        {
            "name": "Asha R",
            "phone": "+91-90000-00001",
            "skills": ["install", "support"],
            "areas": ["560034"],
            "workload": 0,
            "status": "ACTIVE",
        },
        {
            "name": "Rohit K",
            "phone": "+91-90000-00002",
            "skills": ["install"],
            "areas": ["560001", "560034"],
            "workload": 0,
            "status": "ACTIVE",
        },
    ]
    for e in engineers:
        db.engineers.update_one(
            {"phone": e["phone"]},
            {"$setOnInsert": {**e, "created_at": ts, "updated_at": ts}},
            upsert=True,
        )
