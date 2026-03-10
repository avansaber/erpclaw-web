"""Auth API routes — setup, login, refresh, logout, me."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, EmailStr

from db import get_web_db
from auth.passwords import hash_password, verify_password, validate_password
from auth.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_session,
    get_user_roles,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SetupRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/check-setup")
def check_setup():
    """Check if initial setup has been done (any users exist)."""
    conn = get_web_db()
    try:
        count = conn.execute("SELECT COUNT(*) as c FROM web_user").fetchone()["c"]
        return {"setup_required": count == 0}
    finally:
        conn.close()


@router.post("/setup")
def setup(req: SetupRequest):
    """Create the first admin user. Only works when no users exist."""
    conn = get_web_db()
    try:
        count = conn.execute("SELECT COUNT(*) as c FROM web_user").fetchone()["c"]
        if count > 0:
            return {"error": "Setup already completed"}, 400

        # Validate password
        pw_error = validate_password(req.password)
        if pw_error:
            return {"error": pw_error}

        user_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO web_user (id, username, email, full_name, password_hash)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, req.username, req.email, req.full_name, hash_password(req.password)),
        )

        # Assign System Manager role
        role = conn.execute("SELECT id FROM web_role WHERE name = 'System Manager'").fetchone()
        if role:
            conn.execute(
                "INSERT INTO web_user_role (id, user_id, role_id) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), user_id, role["id"]),
            )

        conn.commit()
        return {"message": "Admin user created", "user_id": user_id}
    finally:
        conn.close()


@router.post("/login")
def login(req: LoginRequest, request: Request, response: Response):
    """Login with email + password. Returns access token, sets refresh cookie."""
    conn = get_web_db()
    try:
        user = conn.execute(
            "SELECT * FROM web_user WHERE email = ?", (req.email,)
        ).fetchone()

        if not user:
            return {"error": "Invalid email or password"}

        # Check lockout
        if user["locked_until"]:
            locked = datetime.fromisoformat(user["locked_until"])
            if locked.tzinfo is None:
                locked = locked.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < locked:
                return {"error": "Account locked. Try again later."}
            else:
                # Lockout expired, reset
                conn.execute(
                    "UPDATE web_user SET locked_until = NULL, failed_login_attempts = 0 WHERE id = ?",
                    (user["id"],),
                )
                conn.commit()

        if not verify_password(req.password, user["password_hash"]):
            # Increment failed attempts
            attempts = (user["failed_login_attempts"] or 0) + 1
            if attempts >= 5:
                from datetime import timedelta
                locked_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                conn.execute(
                    "UPDATE web_user SET failed_login_attempts = ?, locked_until = ? WHERE id = ?",
                    (attempts, locked_until, user["id"]),
                )
            else:
                conn.execute(
                    "UPDATE web_user SET failed_login_attempts = ? WHERE id = ?",
                    (attempts, user["id"]),
                )
            conn.commit()
            return {"error": "Invalid email or password"}

        if user["status"] != "active":
            return {"error": "Account is inactive"}

        # Reset failed attempts on success
        conn.execute(
            "UPDATE web_user SET failed_login_attempts = 0, locked_until = NULL, last_login = datetime('now') WHERE id = ?",
            (user["id"],),
        )
        conn.commit()

        # Get roles
        roles = get_user_roles(user["id"])

        # Create tokens
        access_token = create_access_token(user["id"], user["username"], roles)
        refresh_token = create_refresh_token(
            user["id"],
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
        )

        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "roles": roles,
            },
        }
    finally:
        conn.close()


@router.post("/refresh")
def refresh(request: Request, response: Response):
    """Refresh access token using refresh cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return {"error": "No refresh token"}

    user_info = verify_refresh_token(refresh_token)
    if not user_info:
        response.delete_cookie("refresh_token", path="/")
        return {"error": "Invalid or expired refresh token"}

    # Rotate: revoke old, create new
    revoke_session(refresh_token)
    roles = get_user_roles(user_info["user_id"])

    access_token = create_access_token(user_info["user_id"], user_info["username"], roles)
    new_refresh = create_refresh_token(
        user_info["user_id"],
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(request: Request, response: Response):
    """Logout — clear session and cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        revoke_session(refresh_token)
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}


@router.get("/me")
def me(request: Request):
    """Get current user info from access token."""
    # Auth middleware sets request.state.user
    user = getattr(request.state, "user", None)
    if not user:
        return {"error": "Not authenticated"}
    return {"user": user}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, request: Request):
    """Change the current user's password."""
    user = getattr(request.state, "user", None)
    if not user:
        return {"error": "Not authenticated"}

    conn = get_web_db()
    try:
        row = conn.execute(
            "SELECT password_hash FROM web_user WHERE id = ?", (user["id"],)
        ).fetchone()

        if not row or not verify_password(req.current_password, row["password_hash"]):
            return {"error": "Current password is incorrect"}

        pw_error = validate_password(req.new_password)
        if pw_error:
            return {"error": pw_error}

        conn.execute(
            "UPDATE web_user SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
            (hash_password(req.new_password), user["id"]),
        )
        conn.commit()
        return {"message": "Password changed successfully"}
    finally:
        conn.close()
