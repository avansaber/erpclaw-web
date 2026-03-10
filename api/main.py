"""ERPClaw Web API — FastAPI application."""

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

app = FastAPI(
    title="ERPClaw Web API",
    version="1.0.0",
    docs_url="/docs",
)

# CORS — allow SvelteKit dev + production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5180",
        "http://localhost:4173",
        "https://test1.erpclaw.ai",
        "http://test1.erpclaw.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
