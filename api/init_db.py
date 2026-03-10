"""Initialize the erpclaw-web database schema (auth, sessions, roles)."""

import uuid
from db import get_web_db


SCHEMA_SQL = """
-- Web users (separate from erp_user — this is for web dashboard access)
CREATE TABLE IF NOT EXISTS web_user (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TEXT,
    last_login TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Sessions (refresh token tracking)
CREATE TABLE IF NOT EXISTS web_session (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES web_user(id) ON DELETE CASCADE,
    refresh_token_hash TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_active_at TEXT NOT NULL DEFAULT (datetime('now')),
    ip_address TEXT,
    user_agent TEXT,
    revoked_at TEXT,
    grace_until TEXT
);

-- Roles
CREATE TABLE IF NOT EXISTS web_role (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_system INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- User-Role mapping
CREATE TABLE IF NOT EXISTS web_user_role (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES web_user(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL REFERENCES web_role(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, role_id)
);

-- Role permissions (skill + action pattern matching)
CREATE TABLE IF NOT EXISTS web_role_permission (
    id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL REFERENCES web_role(id) ON DELETE CASCADE,
    skill TEXT NOT NULL DEFAULT '*',
    action_pattern TEXT NOT NULL DEFAULT '*',
    allowed INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(role_id, skill, action_pattern)
);

-- App config (JWT secret, settings)
CREATE TABLE IF NOT EXISTS web_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Audit log
CREATE TABLE IF NOT EXISTS web_audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    user_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    description TEXT,
    ip_address TEXT
);
"""

SEED_ROLES = [
    ("System Manager", "Full system access — all skills, all actions", True),
    ("Sales Manager", "Sales module: customers, quotations, orders, invoices", False),
    ("Accountant", "Accounting module: GL, journals, payments, reports", False),
    ("Warehouse Manager", "Inventory module: items, warehouses, stock entries", False),
    ("Viewer", "Read-only access to all modules", False),
]

ROLE_PERMISSIONS = {
    "System Manager": [("*", "*")],
    "Sales Manager": [
        ("erpclaw", "list-*"),
        ("erpclaw", "get-*"),
        ("erpclaw", "add-customer"),
        ("erpclaw", "update-customer"),
        ("erpclaw", "add-quotation"),
        ("erpclaw", "submit-quotation"),
        ("erpclaw", "convert-quotation-to-so"),
        ("erpclaw", "add-sales-order"),
        ("erpclaw", "submit-sales-order"),
        ("erpclaw", "create-delivery-note"),
        ("erpclaw", "submit-delivery-note"),
        ("erpclaw", "create-sales-invoice"),
        ("erpclaw", "submit-sales-invoice"),
        ("erpclaw", "create-credit-note"),
        ("erpclaw", "add-payment"),
        ("erpclaw", "submit-payment"),
    ],
    "Accountant": [
        ("erpclaw", "list-*"),
        ("erpclaw", "get-*"),
        ("erpclaw", "add-journal-entry"),
        ("erpclaw", "submit-journal-entry"),
        ("erpclaw", "cancel-journal-entry"),
        ("erpclaw", "add-payment"),
        ("erpclaw", "submit-payment"),
        ("erpclaw", "cancel-payment"),
        ("erpclaw", "trial-balance"),
        ("erpclaw", "profit-and-loss"),
        ("erpclaw", "balance-sheet"),
        ("erpclaw", "general-ledger"),
        ("erpclaw", "ar-aging"),
        ("erpclaw", "ap-aging"),
    ],
    "Warehouse Manager": [
        ("erpclaw", "list-*"),
        ("erpclaw", "get-*"),
        ("erpclaw", "add-item"),
        ("erpclaw", "update-item"),
        ("erpclaw", "add-warehouse"),
        ("erpclaw", "add-stock-entry"),
        ("erpclaw", "submit-stock-entry"),
        ("erpclaw", "create-purchase-receipt"),
        ("erpclaw", "submit-purchase-receipt"),
        ("erpclaw", "create-delivery-note"),
        ("erpclaw", "submit-delivery-note"),
    ],
    "Viewer": [
        ("*", "list-*"),
        ("*", "get-*"),
    ],
}


def init_web_db():
    """Create all tables and seed default roles."""
    conn = get_web_db()
    try:
        conn.executescript(SCHEMA_SQL)

        # Migration: add revoked_at and grace_until columns for existing DBs
        try:
            conn.execute("ALTER TABLE web_session ADD COLUMN revoked_at TEXT")
        except:
            pass
        try:
            conn.execute("ALTER TABLE web_session ADD COLUMN grace_until TEXT")
        except:
            pass

        # Seed roles
        for name, desc, is_system in SEED_ROLES:
            existing = conn.execute(
                "SELECT id FROM web_role WHERE name = ?", (name,)
            ).fetchone()
            if not existing:
                role_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO web_role (id, name, description, is_system) VALUES (?, ?, ?, ?)",
                    (role_id, name, desc, int(is_system)),
                )
                # Seed permissions for this role
                if name in ROLE_PERMISSIONS:
                    for skill, pattern in ROLE_PERMISSIONS[name]:
                        conn.execute(
                            "INSERT INTO web_role_permission (id, role_id, skill, action_pattern) VALUES (?, ?, ?, ?)",
                            (str(uuid.uuid4()), role_id, skill, pattern),
                        )

        conn.commit()
        print(f"Web database initialized at {conn.execute('PRAGMA database_list').fetchone()[2]}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_web_db()
