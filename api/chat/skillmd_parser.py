"""Lightweight SKILL.md parser for chat action schema injection.

Reads SKILL.md files from installed skills to extract action names,
parameters (required/optional), and descriptions. Used by action_schemas.py
and composition.py to give the AI knowledge of available actions.

This is a simplified version of webclaw's full skillmd_parser — it only
extracts what the chat module needs (action metadata for composition blocks).
"""
from __future__ import annotations

import os
import re

import yaml

from skills.executor import SKILLS_DIR

# Cache: skill_name -> (mtime, parsed_data)
_cache: dict[str, tuple[float, dict]] = {}


def get_cached_params(skill: str, skill_md_path: str | None = None) -> dict | None:
    """Get parsed action params for a skill, with mtime-based cache.

    Returns dict with "actions" key mapping action names to metadata:
        {"actions": {"add-customer": {"required": [...], "optional": [...], "description": "..."}}}

    Returns None if SKILL.md doesn't exist or can't be parsed.
    """
    if skill_md_path is None:
        skill_md_path = os.path.join(SKILLS_DIR, skill, "SKILL.md")

    if not os.path.exists(skill_md_path):
        return None

    mtime = os.path.getmtime(skill_md_path)
    cached = _cache.get(skill)
    if cached and cached[0] == mtime:
        return cached[1]

    try:
        with open(skill_md_path, "r") as f:
            content = f.read()
    except Exception:
        return None

    result = _parse_skill_md(content)
    if result:
        _cache[skill] = (mtime, result)
    return result


def _parse_skill_md(content: str) -> dict | None:
    """Parse a SKILL.md file and extract action metadata."""
    if not content.startswith("---"):
        return None

    try:
        end = content.index("---", 3)
        frontmatter_text = content[3:end]
        body = content[end + 3:].strip()
    except ValueError:
        return None

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return None

    if not frontmatter:
        return None

    actions_dict: dict[str, dict] = {}

    # Strategy 1: YAML body format — actions with body[] param arrays in frontmatter
    fm_actions = frontmatter.get("actions", [])
    if isinstance(fm_actions, list):
        for act in fm_actions:
            if isinstance(act, dict):
                name = act.get("name", "")
                if not name:
                    continue
                desc = act.get("description", "")
                required = []
                optional = []
                for param in act.get("body", []):
                    if isinstance(param, dict):
                        p = {
                            "name": param.get("name", ""),
                            "type": param.get("type", "string"),
                            "description": param.get("description", ""),
                            "required": param.get("required", False),
                        }
                        if p["required"]:
                            required.append(p)
                        else:
                            optional.append(p)
                actions_dict[name] = {
                    "required": required,
                    "optional": optional,
                    "description": desc,
                }
            elif isinstance(act, str):
                # Simple action name, no params
                actions_dict[act] = {"required": [], "optional": [], "description": ""}

    # Strategy 2: Markdown table format in body (erpclaw-style)
    if not actions_dict and body:
        actions_dict = _parse_markdown_tables(body)

    # Strategy 3: Just extract action names from frontmatter actions list
    if not actions_dict and isinstance(fm_actions, list):
        for act in fm_actions:
            if isinstance(act, str):
                actions_dict[act] = {"required": [], "optional": [], "description": ""}

    if not actions_dict:
        return None

    return {"actions": actions_dict}


def _parse_markdown_tables(body: str) -> dict[str, dict]:
    """Parse markdown tables for action definitions.

    Looks for tables with columns like: Action | Description | Required Params | Optional Params
    """
    actions: dict[str, dict] = {}

    # Find table rows (lines starting with |)
    lines = body.split("\n")
    table_lines = []
    in_table = False
    header_cols: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                # This is the header row
                header_cols = [c.lower() for c in cells]
                in_table = True
                continue
            # Skip separator row (|---|---|)
            if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
                continue
            table_lines.append(cells)
        else:
            if in_table and table_lines:
                # Process the table we just finished
                _extract_actions_from_table(header_cols, table_lines, actions)
                table_lines = []
                header_cols = []
            in_table = False

    # Process any remaining table
    if in_table and table_lines:
        _extract_actions_from_table(header_cols, table_lines, actions)

    return actions


def _extract_actions_from_table(
    headers: list[str], rows: list[list[str]], actions: dict[str, dict]
) -> None:
    """Extract action metadata from a parsed markdown table."""
    # Find relevant column indices
    action_idx = None
    desc_idx = None
    params_idx = None

    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        if "action" in h_lower or "command" in h_lower:
            action_idx = i
        elif "desc" in h_lower:
            desc_idx = i
        elif "param" in h_lower or "arg" in h_lower or "field" in h_lower:
            params_idx = i

    if action_idx is None:
        return

    for row in rows:
        if action_idx >= len(row):
            continue
        action_name = row[action_idx].strip().strip("`")
        if not action_name or action_name.startswith("-"):
            continue

        desc = row[desc_idx].strip() if desc_idx is not None and desc_idx < len(row) else ""

        required = []
        optional = []
        if params_idx is not None and params_idx < len(row):
            params_text = row[params_idx].strip()
            # Parse param list: "name*, email, phone" or "name (required), email"
            for param_str in re.split(r"[,;]", params_text):
                param_str = param_str.strip().strip("`")
                if not param_str:
                    continue
                is_required = "*" in param_str or "required" in param_str.lower()
                name = re.sub(r"[\*\(\)required]", "", param_str, flags=re.I).strip()
                if not name:
                    continue
                p = {"name": name, "type": "string", "required": is_required}
                if is_required:
                    required.append(p)
                else:
                    optional.append(p)

        actions[action_name] = {
            "required": required,
            "optional": optional,
            "description": desc,
        }
