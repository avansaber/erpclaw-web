"""Skill action execution API routes."""

import fnmatch

from fastapi import APIRouter, Request
from pydantic import BaseModel

from db import get_web_db
from skills.executor import execute_action
from ws import notify_action, notify_data_change

router = APIRouter(prefix="/api/action", tags=["actions"])


class ActionRequest(BaseModel):
    params: dict | None = None


def _check_permission(user: dict, skill: str, action: str) -> bool:
    """Check if user has permission to execute this action."""
    if "System Manager" in user.get("roles", []):
        return True

    conn = get_web_db()
    try:
        rows = conn.execute(
            """SELECT rp.skill, rp.action_pattern, rp.allowed
               FROM web_role_permission rp
               JOIN web_role r ON rp.role_id = r.id
               JOIN web_user_role ur ON r.id = ur.role_id
               WHERE ur.user_id = ?""",
            (user["id"],),
        ).fetchall()

        for row in rows:
            perm_skill = row["skill"]
            perm_pattern = row["action_pattern"]

            # Check skill match (wildcard or exact)
            skill_match = perm_skill == "*" or perm_skill == skill
            # Check action match (wildcard or fnmatch pattern)
            action_match = perm_pattern == "*" or fnmatch.fnmatch(action, perm_pattern)

            if skill_match and action_match:
                return bool(row["allowed"])

        return False
    finally:
        conn.close()


@router.post("/{skill}/{action}")
async def run_action(skill: str, action: str, body: ActionRequest, request: Request):
    """Execute a skill action (with RBAC check)."""
    user = getattr(request.state, "user", None)
    if not user:
        return {"error": "Not authenticated"}

    if not _check_permission(user, skill, action):
        return {"error": f"Permission denied for {skill}/{action}"}

    result = await execute_action(skill, action, body.params)

    # Audit log
    conn = get_web_db()
    try:
        import uuid
        conn.execute(
            """INSERT INTO web_audit_log (id, user_id, action, entity_type, description, ip_address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                user["id"],
                action,
                skill,
                f"{skill}/{action}",
                request.client.host if request.client else "",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Broadcast WebSocket notification
    success = "error" not in result
    await notify_action(skill, action, success)
    if success and any(action.startswith(p) for p in ("add-", "create-", "update-", "submit-", "cancel-", "delete-")):
        # Extract entity from action name (e.g., add-customer → customer)
        entity = action.split("-", 1)[1] if "-" in action else action
        change_type = action.split("-", 1)[0] if "-" in action else "update"
        await notify_data_change(entity, change_type)

    return result
