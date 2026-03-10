"""JWT token creation and verification."""

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from db import get_web_db

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    """Get or create the JWT secret from web_config table."""
    conn = get_web_db()
    try:
        row = conn.execute(
            "SELECT value FROM web_config WHERE key = 'jwt_secret'"
        ).fetchone()
        if row:
            return row["value"]

        # Generate and store new secret
        secret = secrets.token_hex(32)
        conn.execute(
            "INSERT INTO web_config (key, value) VALUES ('jwt_secret', ?)", (secret,)
        )
        conn.commit()
        return secret
    finally:
        conn.close()


def create_access_token(user_id: str, username: str, roles: list[str]) -> str:
    """Create a short-lived access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=ALGORITHM)


def create_refresh_token(user_id: str, ip_address: str = "", user_agent: str = "") -> str:
    """Create a refresh token and store session in DB."""
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    conn = get_web_db()
    try:
        # Enforce max 5 sessions per user
        sessions = conn.execute(
            "SELECT id FROM web_session WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()
        if len(sessions) >= 5:
            conn.execute("DELETE FROM web_session WHERE id = ?", (sessions[0]["id"],))

        conn.execute(
            """INSERT INTO web_session (id, user_id, refresh_token_hash, expires_at, ip_address, user_agent)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), user_id, token_hash, expires_at.isoformat(), ip_address, user_agent),
        )
        conn.commit()
    finally:
        conn.close()

    return token


def verify_access_token(token: str) -> dict | None:
    """Verify and decode an access token. Returns payload or None."""
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> dict | None:
    """Verify a refresh token against the session table. Returns user info or None."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_web_db()
    try:
        row = conn.execute(
            """SELECT s.id as session_id, s.user_id, s.expires_at,
                      u.username, u.email, u.full_name, u.status
               FROM web_session s
               JOIN web_user u ON s.user_id = u.id
               WHERE s.refresh_token_hash = ?""",
            (token_hash,),
        ).fetchone()

        if not row:
            return None

        # Check expiry
        expires = datetime.fromisoformat(row["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            conn.execute("DELETE FROM web_session WHERE id = ?", (row["session_id"],))
            conn.commit()
            return None

        # Check user status
        if row["status"] != "active":
            return None

        # Update last_active_at
        conn.execute(
            "UPDATE web_session SET last_active_at = datetime('now') WHERE id = ?",
            (row["session_id"],),
        )
        conn.commit()

        return dict(row)
    finally:
        conn.close()


def revoke_session(token: str):
    """Delete a session by refresh token."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_web_db()
    try:
        conn.execute("DELETE FROM web_session WHERE refresh_token_hash = ?", (token_hash,))
        conn.commit()
    finally:
        conn.close()


def get_user_roles(user_id: str) -> list[str]:
    """Get all role names for a user."""
    conn = get_web_db()
    try:
        rows = conn.execute(
            """SELECT r.name FROM web_role r
               JOIN web_user_role ur ON r.id = ur.role_id
               WHERE ur.user_id = ?""",
            (user_id,),
        ).fetchall()
        return [r["name"] for r in rows]
    finally:
        conn.close()
