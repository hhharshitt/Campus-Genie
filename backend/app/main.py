"""
CampusGenie Backend — FastAPI Application Entry Point
ETT Course Project
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.logger import setup_logging
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes import documents, chat, health, analytics

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    setup_logging()
    logger.info("CampusGenie backend starting up", extra={"version": "1.0.0"})
    yield
    logger.info("CampusGenie backend shutting down")


app = FastAPI(
    title="CampusGenie API",
    description=(
        "RAG-based AI assistant for campus documents. "
        "Answers questions from uploaded PDFs with source citations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters — outermost first) ───────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router,     prefix="/api",            tags=["health"])
app.include_router(documents.router,  prefix="/api/documents",  tags=["documents"])
app.include_router(chat.router,       prefix="/api/chat",       tags=["chat"])
app.include_router(analytics.router,  prefix="/api/analytics",  tags=["analytics"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "CampusGenie API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
