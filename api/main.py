"""ERPClaw Web API — FastAPI application."""

import os
import sys
from pathlib import Path

# Ensure api/ directory is on the Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.middleware import AuthMiddleware
from auth.routes import router as auth_router
from skills.routes import router as skills_router
from layout import router as layout_router
from chat import router as chat_router
from ws import router as ws_router
from init_db import init_web_db

# Initialize database on startup
init_web_db()

# Production mode disables Swagger UI
_is_production = os.environ.get("ERPCLAW_ENV", "development") == "production"

app = FastAPI(
    title="ERPClaw Web API",
    version="1.0.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

# CORS — configurable origins via environment variable
_default_origins = "http://localhost:5173,http://localhost:5180,http://localhost:4173"
_origins = os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Auth middleware (after CORS so preflight passes)
app.add_middleware(AuthMiddleware)

# Mount routers
app.include_router(auth_router)
app.include_router(layout_router)
app.include_router(skills_router)
app.include_router(chat_router)
app.include_router(ws_router)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
