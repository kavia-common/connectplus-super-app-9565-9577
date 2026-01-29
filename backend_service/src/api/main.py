from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.db import get_db
from src.core.indexes import ensure_indexes
from src.core.seed import seed_core_data
from src.api.routers.chat import router as chat_router
from src.api.routers.orders import router as orders_router
from src.api.routers.plans import router as plans_router
from src.api.routers.tickets import router as tickets_router

openapi_tags = [
    {"name": "Plans", "description": "Plan discovery and filtering."},
    {"name": "Orders", "description": "New connection setup orders and scheduling."},
    {"name": "Tickets", "description": "Support ticketing workflows."},
    {"name": "Chat", "description": "Chat orchestration with ai_nlp_engine + conversation persistence."},
]

app = FastAPI(
    title="ConnectPlus Backend API",
    description="Backend APIs for plans, orders/setup, tickets, and chat orchestration.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    """Initialize indexes and seed core data."""
    db = get_db()
    ensure_indexes(db)
    seed_core_data(db)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


app.include_router(plans_router)
app.include_router(orders_router)
app.include_router(tickets_router)
app.include_router(chat_router)
