"""Database connection management for erpclaw-web API."""

import os
import sqlite3
from pathlib import Path

# Web app's own database (users, sessions, roles)
WEB_DB_PATH = os.environ.get(
    "ERPCLAW_WEB_DB",
    os.path.expanduser("~/.openclaw/erpclaw-web/web.sqlite"),
)

# ERPClaw's data database (the actual ERP data)
ERP_DB_PATH = os.environ.get(
    "ERPCLAW_DB",
    os.path.expanduser("~/.openclaw/erpclaw/data.sqlite"),
)


def get_web_db() -> sqlite3.Connection:
    """Get connection to the web app's own database (auth, sessions)."""
    Path(WEB_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(WEB_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def get_erp_db() -> sqlite3.Connection:
    """Get read-only connection to ERPClaw's data database."""
    if not Path(ERP_DB_PATH).exists():
        raise FileNotFoundError(f"ERPClaw database not found at {ERP_DB_PATH}")
    conn = sqlite3.connect(f"file:{ERP_DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
