"""Layout computation — serves VerticalLayout JSON per role.

Phase 3: Returns static layout from compiled UI.yaml configs.
Phase 4+: Will dynamically compute from installed modules + role permissions.
"""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/layout", tags=["layout"])

# Load compiled layouts from JSON files
LAYOUTS_DIR = Path(__file__).parent / "layouts"

_layout_cache: dict[str, dict] = {}


def _load_layouts():
    """Load all layout JSON files from the layouts/ directory."""
    if _layout_cache:
        return
    if not LAYOUTS_DIR.exists():
        return
    for f in LAYOUTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            _layout_cache[data["name"]] = data
        except (json.JSONDecodeError, KeyError):
            pass


def _apply_role_filter(layout: dict, roles: list[str]) -> dict:
    """Filter layout based on user roles.

    Role overrides can hide sidebar items, entities, KPIs.
    If user has System Manager role, return full layout.
    """
    if "System Manager" in roles or not layout.get("roles"):
        return layout

    # Find the most permissive role override
    role_config = None
    for role_name in roles:
        if role_name in layout.get("roles", {}):
            role_config = layout["roles"][role_name]
            break

    if not role_config:
        return layout  # No role-specific overrides, return full layout

    result = {**layout}

    # Hide sidebar items
    if "sidebar_hide" in role_config:
        hidden = set(role_config["sidebar_hide"])
        result["sidebar"] = []
        for group in layout["sidebar"]:
            filtered_items = [i for i in group["items"] if i["key"] not in hidden]
            if filtered_items:
                result["sidebar"].append({**group, "items": filtered_items})

    # Hide entities
    if "entity_hide" in role_config:
        hidden = set(role_config["entity_hide"])
        result["entities"] = {k: v for k, v in layout["entities"].items() if k not in hidden}
        if "mockData" in layout:
            result["mockData"] = {k: v for k, v in layout["mockData"].items() if k not in hidden}

    # Hide KPIs
    if "kpi_hide" in role_config:
        hidden = set(role_config["kpi_hide"])
        result["kpis"] = [k for k in layout["kpis"] if k["label"] not in hidden]

    return result


@router.get("/verticals")
def list_verticals():
    """List available verticals (names + labels only)."""
    _load_layouts()
    return {
        "verticals": [
            {"name": v["name"], "label": v["label"], "icon": v["icon"], "color": v["color"]}
            for v in _layout_cache.values()
        ]
    }


@router.get("/{vertical}")
def get_layout(vertical: str, request: Request):
    """Get the full layout for a vertical, filtered by current user's roles."""
    _load_layouts()

    if vertical not in _layout_cache:
        return {"error": f"Vertical '{vertical}' not found"}

    layout = _layout_cache[vertical]

    # Apply role filtering if user is authenticated
    user = getattr(request.state, "user", None)
    roles = user.get("roles", []) if user else ["System Manager"]

    return _apply_role_filter(layout, roles)


@router.post("/reload")
def reload_layouts():
    """Force reload all layout configs from disk."""
    _layout_cache.clear()
    _load_layouts()
    return {"message": f"Reloaded {len(_layout_cache)} layouts"}
