"""Sales Intelligence Agent System — FastAPI Backend."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import auth, leads, research, briefs, alerts, analytics, admin, intelligence, agents
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()
    log.info(f"Starting Sales Intelligence API ({settings.app_env})")
    start_scheduler()
    yield
    stop_scheduler()
    log.info("Shutting down Sales Intelligence API")


app = FastAPI(
    title="Sales Intelligence Agent API",
    description="AI-powered sales intelligence for Onsite Teams",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS (strip whitespace so "url1, url2" works)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(briefs.router, prefix="/api/briefs", tags=["briefs"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["intelligence"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])


@app.get("/")
async def root():
    return {
        "service": "Sales Intelligence API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sales-intelligence-api"}
