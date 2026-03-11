"""Execute ERPClaw skill actions via subprocess."""

import asyncio
import json
import os
import sqlite3
import sys
from pathlib import Path

# Where skills are installed
SKILLS_DIR = os.path.expanduser("~/clawd/skills")
MODULES_DIR = os.path.expanduser("~/.openclaw/erpclaw/modules")
ERPCLAW_LIB = os.path.expanduser("~/.openclaw/erpclaw/lib")
ERP_DB_PATH = os.path.expanduser("~/.openclaw/erpclaw/data.sqlite")
WEB_DB_PATH = os.path.expanduser("~/.openclaw/erpclaw-web/web.sqlite")

# Timeout for action execution
ACTION_TIMEOUT = 30  # seconds
SLOW_ACTIONS = {"seed-demo-data", "initialize-database", "import-customers", "import-items"}
SLOW_TIMEOUT = 120


def _find_script(skill: str) -> str | None:
    """Find db_query.py for a skill."""
    # Primary: installed skill
    primary = Path(SKILLS_DIR) / skill / "scripts" / "db_query.py"
    if primary.exists():
        return str(primary)

    # Fallback: erpclaw modules directory
    fallback = Path(MODULES_DIR) / skill / "scripts" / "db_query.py"
    if fallback.exists():
        return str(fallback)

    # ERPClaw core: it might be at the skill name itself
    core = Path(SKILLS_DIR) / "erpclaw" / "scripts" / "db_query.py"
    if skill == "erpclaw" and core.exists():
        return str(core)

    return None


def _build_args(action: str, params: dict) -> list[str]:
    """Build CLI arguments from action + params dict."""
    args = ["--action", action]
    for key, value in params.items():
        if key.startswith("_"):
            continue  # Skip internal params
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                args.append(flag)
        elif value is not None:
            args.extend([flag, str(value)])
    return args


def _get_default_company_id() -> str | None:
    """Get the default company ID for auto-injection.

    Priority: web_config 'default_company_id' > single company > first company.
    """
    # 1. Check web_config for explicit default
    if Path(WEB_DB_PATH).exists():
        try:
            conn = sqlite3.connect(WEB_DB_PATH)
            row = conn.execute(
                "SELECT value FROM web_config WHERE key='default_company_id'"
            ).fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass

    # 2. Fall back to ERP database
    if not Path(ERP_DB_PATH).exists():
        return None
    try:
        conn = sqlite3.connect(ERP_DB_PATH)
        row = conn.execute("SELECT id FROM company ORDER BY created_at LIMIT 1").fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return None


async def execute_action(
    skill: str, action: str, params: dict | None = None
) -> dict:
    """Execute a skill action and return the parsed result."""
    script = _find_script(skill)
    if not script:
        return {"error": f"Skill '{skill}' not found"}

    params = params or {}

    # Auto-inject company_id if not provided and a single company exists
    if "company_id" not in params:
        cid = _get_default_company_id()
        if cid:
            params["company_id"] = cid

    cmd = [sys.executable, script] + _build_args(action, params)

    # Set up environment
    env = os.environ.copy()
    script_dir = str(Path(script).parent)
    python_path = [script_dir, ERPCLAW_LIB]
    if "PYTHONPATH" in env:
        python_path.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path)

    timeout = SLOW_TIMEOUT if action in SLOW_ACTIONS else ACTION_TIMEOUT

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        return {"error": f"Action '{action}' timed out after {timeout}s"}
    except FileNotFoundError:
        return {"error": f"Python interpreter not found"}

    stdout_text = stdout.decode().strip()
    stderr_text = stderr.decode().strip()

    if proc.returncode != 0:
        # Try to parse error from stdout (ERPClaw convention)
        try:
            result = json.loads(stdout_text)
            if "error" in result:
                return result
        except (json.JSONDecodeError, ValueError):
            pass
        return {"error": stderr_text or stdout_text or f"Action failed with exit code {proc.returncode}"}

    # Parse JSON output
    try:
        return json.loads(stdout_text)
    except (json.JSONDecodeError, ValueError):
        if stdout_text:
            return {"result": stdout_text}
        return {"result": "OK"}
