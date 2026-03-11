"""Chat AI — rule-based intent detection, ERP data queries, action execution.

Handles natural language → structured response:
  navigate: "show me customers" → redirect to /customer
  create:   "new invoice for Acme" → open create form with prefilled data
  query:    "how many overdue invoices?" → count from ERP DB
  action:   "submit order SO-00012" → execute skill action
  help:     "what can I do?" → list capabilities
"""

import json
import re
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel

from db import get_erp_db

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Load layout for entity context
LAYOUTS_DIR = Path(__file__).parent / "layouts"
_entity_cache: dict[str, dict] = {}  # entity_key → {label, labelPlural, columns, actions, table}


def _load_entity_context():
    """Build entity catalog from layout JSONs for intent matching."""
    if _entity_cache:
        return
    for f in LAYOUTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            for key, edef in data.get("entities", {}).items():
                _entity_cache[key] = {
                    "key": key,
                    "label": edef["label"],
                    "label_plural": edef["labelPlural"],
                    "columns": [c["field"] for c in edef.get("columns", [])],
                    "column_defs": edef.get("columns", []),
                    "actions": edef.get("actions", []),
                    "create_action": edef.get("createForm", {}).get("action", f"add-{key.replace('_', '-')}"),
                    "skill": data["name"],
                }
        except (json.JSONDecodeError, KeyError):
            pass


# Entity key → actual SQLite table name
TABLE_MAP = {
    "customer": "customer",
    "supplier": "supplier",
    "sales_order": "sales_order",
    "sales_invoice": "sales_invoice",
    "purchase_order": "purchase_order",
    "purchase_invoice": "purchase_invoice",
    "item": "item",
    "employee": "employee",
    "account": "account",
    "warehouse": "warehouse",
    "journal_entry": "journal_entry",
    "payment": "payment_entry",
}

# Common aliases for entity matching
ENTITY_ALIASES = {
    "customers": "customer",
    "invoices": "sales_invoice",
    "invoice": "sales_invoice",
    "orders": "sales_order",
    "order": "sales_order",
    "sales orders": "sales_order",
    "purchase orders": "purchase_order",
    "pos": "purchase_order",
    "po": "purchase_order",
    "items": "item",
    "products": "item",
    "product": "item",
    "employees": "employee",
    "staff": "employee",
    "suppliers": "supplier",
    "vendors": "supplier",
    "vendor": "supplier",
    "accounts": "account",
    "warehouses": "warehouse",
    "journals": "journal_entry",
    "journal entries": "journal_entry",
    "payments": "payment",
    "bills": "purchase_invoice",
    "bill": "purchase_invoice",
    "purchase invoices": "purchase_invoice",
    "sales invoices": "sales_invoice",
}


class ChatRequest(BaseModel):
    message: str
    vertical: str = "erpclaw"
    context: dict | None = None
    history: list[dict] | None = None


class ChatResponse(BaseModel):
    type: str  # navigate, create, query, action, help, error
    message: str
    href: str | None = None
    data: list[dict] | None = None
    action: dict | None = None
    suggestions: list[str] | None = None


def _match_entity(text: str) -> str | None:
    """Match entity from user text using aliases and layout definitions."""
    lower = text.lower()

    # Check aliases first (longest match wins)
    for alias in sorted(ENTITY_ALIASES.keys(), key=len, reverse=True):
        if alias in lower:
            return ENTITY_ALIASES[alias]

    # Check layout entity labels
    _load_entity_context()
    for key, edef in _entity_cache.items():
        if edef["label"].lower() in lower or edef["label_plural"].lower() in lower:
            return key

    return None


def _detect_intent(text: str) -> str:
    """Classify user message into intent category."""
    lower = text.lower().strip()

    # Help
    if any(w in lower for w in ["help", "what can", "how do", "how to", "capabilities"]):
        return "help"

    # Create/Add
    if any(lower.startswith(w) for w in ["create ", "new ", "add ", "make "]):
        return "create"
    if re.search(r"\b(create|add|new)\b.*\b(customer|invoice|order|item|employee|supplier|payment|journal|warehouse)\b", lower):
        return "create"

    # Submit/Cancel actions
    if re.search(r"\b(submit|cancel|approve|reject|delete)\b", lower):
        return "action"

    # Count queries
    if re.search(r"\b(how many|count|total number|number of)\b", lower):
        return "count"

    # Aggregate queries
    if re.search(r"\b(total|sum|average|avg|revenue|amount|balance|outstanding)\b", lower):
        return "aggregate"

    # Navigation (show me X, go to X) — before query so "show me customers" navigates
    if re.search(r"\b(go to|open|navigate|take me|show me)\b", lower):
        entity = _match_entity(lower)
        if entity:
            # If there's also a filter keyword, treat as query
            if re.search(r"\b(overdue|pending|draft|unpaid|open|active|inactive|closed)\b", lower):
                return "query"
            return "navigate"

    # List/Show queries (with filter words or explicit list/find)
    if re.search(r"\b(overdue|pending|draft|unpaid|open|active|inactive)\b", lower):
        return "query"
    if any(lower.startswith(w) for w in ["list ", "find ", "get ", "display "]):
        return "query"
    if any(lower.startswith(w) for w in ["show ", "view "]):
        # "show" without "me" and with an entity = query
        if "me" not in lower and _match_entity(lower):
            return "query"

    # Dashboard
    if any(w in lower for w in ["dashboard", "home", "overview"]):
        return "navigate"

    # If we can match an entity, default to navigate
    if _match_entity(lower):
        return "navigate"

    return "help"


def _extract_filters(text: str) -> dict:
    """Extract filter conditions from natural language."""
    lower = text.lower()
    filters = {}

    # Status filters
    status_words = {
        "overdue": "Overdue",
        "pending": "Pending",
        "draft": "Draft",
        "submitted": "Submitted",
        "cancelled": "Cancelled",
        "paid": "Paid",
        "unpaid": "Unpaid",
        "active": "Active",
        "inactive": "Inactive",
        "open": "Open",
        "closed": "Closed",
    }
    for word, status in status_words.items():
        if word in lower:
            filters["status"] = status
            break

    # Top N
    top_match = re.search(r"\btop\s+(\d+)\b", lower)
    if top_match:
        filters["_limit"] = int(top_match.group(1))

    # Date filters
    if "this month" in lower:
        filters["_date_filter"] = "this_month"
    elif "this week" in lower:
        filters["_date_filter"] = "this_week"
    elif "today" in lower:
        filters["_date_filter"] = "today"
    elif "this year" in lower:
        filters["_date_filter"] = "this_year"
    elif "last month" in lower:
        filters["_date_filter"] = "last_month"

    return filters


def _build_date_clause(date_filter: str, date_col: str = "creation") -> str:
    """Build SQL date clause from filter key."""
    clauses = {
        "today": f"DATE({date_col}) = DATE('now')",
        "this_week": f"{date_col} >= DATE('now', 'weekday 0', '-7 days')",
        "this_month": f"{date_col} >= DATE('now', 'start of month')",
        "last_month": f"{date_col} >= DATE('now', 'start of month', '-1 month') AND {date_col} < DATE('now', 'start of month')",
        "this_year": f"{date_col} >= DATE('now', 'start of year')",
    }
    return clauses.get(date_filter, "1=1")


def _get_date_column(entity_key: str) -> str:
    """Get the primary date column for an entity."""
    date_cols = {
        "sales_order": "order_date",
        "sales_invoice": "posting_date",
        "purchase_order": "order_date",
        "purchase_invoice": "posting_date",
        "journal_entry": "posting_date",
        "payment": "posting_date",
        "employee": "date_of_joining",
    }
    return date_cols.get(entity_key, "creation")


def _query_erp(entity_key: str, filters: dict, mode: str = "list") -> dict:
    """Query the ERP database for entity data. Returns {count, rows, total}."""
    table = TABLE_MAP.get(entity_key)
    if not table:
        return {"error": f"Unknown entity: {entity_key}"}
    # Defense-in-depth: validate table name is a safe SQL identifier
    if not table.replace("_", "").isalnum():
        return {"error": f"Invalid table name: {entity_key}"}

    try:
        conn = get_erp_db()
    except FileNotFoundError:
        return {"error": "ERP database not available"}

    try:
        # Build WHERE clause
        where_parts = []
        params = []

        if "status" in filters:
            where_parts.append("status = ?")
            params.append(filters["status"])

        date_filter = filters.get("_date_filter")
        if date_filter:
            date_col = _get_date_column(entity_key)
            # Validate column name is a safe identifier
            if not date_col.replace("_", "").isalnum():
                return {"error": f"Invalid column name: {date_col}"}
            # Check if column exists
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if date_col in cols:
                where_parts.append(_build_date_clause(date_filter, date_col))

        where_sql = " AND ".join(where_parts) if where_parts else "1=1"
        limit = filters.get("_limit", 20)

        if mode == "count":
            row = conn.execute(f"SELECT COUNT(*) as c FROM {table} WHERE {where_sql}", params).fetchone()
            return {"count": row[0]}

        elif mode == "aggregate":
            # Try common amount columns
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            amount_col = None
            for candidate in ["grand_total", "total_debit", "outstanding_amount", "total_amount", "base_total", "amount"]:
                if candidate in cols:
                    amount_col = candidate
                    break

            # Validate amount_col is a safe identifier (from PRAGMA, not user input)
            if amount_col and not amount_col.replace("_", "").isalnum():
                amount_col = None
            if amount_col:
                row = conn.execute(
                    f"SELECT COUNT(*) as cnt, SUM(CAST({amount_col} AS REAL)) as total FROM {table} WHERE {where_sql}",
                    params,
                ).fetchone()
                return {"count": row[0], "total": round(row[1] or 0, 2)}
            else:
                row = conn.execute(f"SELECT COUNT(*) as c FROM {table} WHERE {where_sql}", params).fetchone()
                return {"count": row[0]}

        else:  # list
            rows = conn.execute(
                f"SELECT * FROM {table} WHERE {where_sql} ORDER BY rowid DESC LIMIT ?",
                params + [limit],
            ).fetchall()
            cols = [desc[0] for desc in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
            result_rows = [dict(zip(cols, row)) for row in rows]
            return {"count": len(result_rows), "rows": result_rows}

    except sqlite3.OperationalError as e:
        return {"error": str(e)}
    finally:
        conn.close()


def _handle_navigate(text: str) -> ChatResponse:
    """Handle navigation intent."""
    lower = text.lower()

    if any(w in lower for w in ["dashboard", "home", "overview"]):
        return ChatResponse(
            type="navigate", message="Taking you to the dashboard.", href="/"
        )

    entity = _match_entity(lower)
    if entity:
        _load_entity_context()
        edef = _entity_cache.get(entity, {})
        label = edef.get("label_plural", entity)
        return ChatResponse(
            type="navigate", message=f"Opening {label}.", href=f"/{entity}"
        )

    return ChatResponse(
        type="help", message="I'm not sure where to navigate. Try 'show me customers' or 'go to dashboard'."
    )


def _handle_create(text: str) -> ChatResponse:
    """Handle create/add intent."""
    entity = _match_entity(text)
    if not entity:
        return ChatResponse(
            type="help",
            message="What would you like to create? Try 'new customer', 'new invoice', or 'new order'.",
            suggestions=["New customer", "New sales order", "New invoice", "New item"],
        )

    _load_entity_context()
    edef = _entity_cache.get(entity, {})
    label = edef.get("label", entity)
    return ChatResponse(
        type="navigate",
        message=f"Opening the new {label} form.",
        href=f"/{entity}/new",
    )


def _handle_count(text: str) -> ChatResponse:
    """Handle count queries."""
    entity = _match_entity(text)
    if not entity:
        return ChatResponse(type="help", message="Count what? Try 'how many customers?' or 'how many overdue invoices?'")

    filters = _extract_filters(text)
    result = _query_erp(entity, filters, mode="count")

    if "error" in result:
        return ChatResponse(type="error", message=result["error"])

    _load_entity_context()
    edef = _entity_cache.get(entity, {})
    label = edef.get("label_plural", entity)

    status_desc = f" {filters['status'].lower()}" if "status" in filters else ""
    date_desc = ""
    df = filters.get("_date_filter", "")
    if df:
        date_desc = f" {df.replace('_', ' ')}"

    return ChatResponse(
        type="query",
        message=f"You have **{result['count']}**{status_desc} {label.lower()}{date_desc}.",
        href=f"/{entity}",
    )


def _handle_aggregate(text: str) -> ChatResponse:
    """Handle aggregate queries (totals, revenue, sums)."""
    entity = _match_entity(text)
    if not entity:
        # Default to sales_invoice for revenue queries
        lower = text.lower()
        if any(w in lower for w in ["revenue", "sales", "income"]):
            entity = "sales_invoice"
        elif any(w in lower for w in ["expense", "spending", "cost"]):
            entity = "purchase_invoice"
        else:
            return ChatResponse(type="help", message="What would you like to total? Try 'total revenue this month' or 'outstanding invoices'.")

    filters = _extract_filters(text)
    result = _query_erp(entity, filters, mode="aggregate")

    if "error" in result:
        return ChatResponse(type="error", message=result["error"])

    _load_entity_context()
    edef = _entity_cache.get(entity, {})
    label = edef.get("label_plural", entity)

    status_desc = f" {filters.get('status', '').lower()}" if "status" in filters else ""
    date_desc = ""
    df = filters.get("_date_filter", "")
    if df:
        date_desc = f" {df.replace('_', ' ')}"

    if "total" in result and result["total"]:
        return ChatResponse(
            type="query",
            message=f"**{result['count']}**{status_desc} {label.lower()}{date_desc} totaling **${result['total']:,.2f}**.",
            href=f"/{entity}",
        )
    else:
        return ChatResponse(
            type="query",
            message=f"**{result['count']}**{status_desc} {label.lower()}{date_desc}.",
            href=f"/{entity}",
        )


def _handle_query(text: str) -> ChatResponse:
    """Handle list/find queries."""
    entity = _match_entity(text)
    if not entity:
        return ChatResponse(type="help", message="What would you like to find? Try 'show overdue invoices' or 'list active customers'.")

    filters = _extract_filters(text)
    result = _query_erp(entity, filters, mode="list")

    if "error" in result:
        return ChatResponse(type="error", message=result["error"])

    _load_entity_context()
    edef = _entity_cache.get(entity, {})
    label = edef.get("label_plural", entity)
    rows = result.get("rows", [])

    status_desc = f" {filters.get('status', '').lower()}" if "status" in filters else ""

    if not rows:
        return ChatResponse(
            type="query",
            message=f"No{status_desc} {label.lower()} found.",
            href=f"/{entity}",
        )

    # Format top rows as a summary
    summary_lines = []
    # Pick display columns: name/id + status + amount
    display_fields = _pick_display_fields(entity, rows[0] if rows else {})

    for row in rows[:5]:
        parts = []
        for field in display_fields:
            val = row.get(field, "")
            if val and val != "None":
                parts.append(str(val))
        if parts:
            summary_lines.append(" | ".join(parts))

    more = f"\n\n...and {len(rows) - 5} more." if len(rows) > 5 else ""
    listing = "\n".join(f"- {line}" for line in summary_lines)

    return ChatResponse(
        type="query",
        message=f"Found **{result['count']}**{status_desc} {label.lower()}:\n\n{listing}{more}",
        data=rows[:10],
        href=f"/{entity}",
    )


def _pick_display_fields(entity_key: str, sample_row: dict) -> list[str]:
    """Pick the best fields to display in a chat summary."""
    # Priority fields per entity type
    priority = {
        "customer": ["name", "customer_name", "customer_type", "status"],
        "supplier": ["name", "supplier_name", "supplier_type", "status"],
        "sales_order": ["naming_series", "customer_name", "grand_total", "status"],
        "sales_invoice": ["naming_series", "customer_name", "grand_total", "status", "outstanding_amount"],
        "purchase_order": ["naming_series", "supplier_name", "grand_total", "status"],
        "purchase_invoice": ["naming_series", "supplier_name", "grand_total", "status"],
        "item": ["item_code", "item_name", "item_group_id", "standard_rate"],
        "employee": ["naming_series", "full_name", "department_name", "status"],
        "account": ["name", "account_number", "root_type", "is_group"],
        "warehouse": ["name", "warehouse_type"],
        "journal_entry": ["naming_series", "posting_date", "entry_type", "total_debit"],
        "payment": ["naming_series", "posting_date", "party_name", "paid_amount"],
    }

    fields = priority.get(entity_key, [])
    # Filter to fields that exist in the row
    return [f for f in fields if f in sample_row]


def _handle_action(text: str) -> ChatResponse:
    """Handle action execution intent (submit, cancel, etc.)."""
    lower = text.lower()

    # Extract action verb
    action_verb = None
    for verb in ["submit", "cancel", "approve", "reject", "delete"]:
        if verb in lower:
            action_verb = verb
            break

    entity = _match_entity(lower)
    if not entity or not action_verb:
        return ChatResponse(
            type="help",
            message="What action would you like to take? Try 'submit order SO-00012' or 'cancel invoice SI-00005'.",
        )

    # Extract document ID (e.g., SO-00012, SI-00005)
    id_match = re.search(r"\b([A-Z]{2,4}-\d{3,})\b", text)
    doc_id = id_match.group(1) if id_match else None

    _load_entity_context()
    edef = _entity_cache.get(entity, {})
    label = edef.get("label", entity)
    action_name = f"{action_verb}-{entity.replace('_', '-')}"

    if doc_id:
        return ChatResponse(
            type="action",
            message=f"Ready to {action_verb} {label} **{doc_id}**. Execute this action?",
            action={"skill": edef.get("skill", "erpclaw"), "action": action_name, "params": {"id": doc_id}},
            href=f"/{entity}",
        )
    else:
        return ChatResponse(
            type="help",
            message=f"Which {label.lower()} would you like to {action_verb}? Please provide the document ID (e.g., {action_verb} {label} SO-00001).",
        )


def _handle_help(text: str) -> ChatResponse:
    """Return help message with capabilities."""
    _load_entity_context()
    entity_list = ", ".join(sorted(set(e["label_plural"].lower() for e in _entity_cache.values())))

    return ChatResponse(
        type="help",
        message=(
            "I can help you with:\n\n"
            "**Navigate** — \"show me customers\", \"go to dashboard\"\n"
            "**Create** — \"new invoice\", \"add customer\"\n"
            "**Query** — \"how many overdue invoices?\", \"total revenue this month\"\n"
            "**Find** — \"show draft orders\", \"list active employees\"\n"
            "**Actions** — \"submit order SO-00012\", \"cancel invoice SI-00005\"\n\n"
            f"Available entities: {entity_list}."
        ),
        suggestions=[
            "Show me customers",
            "How many overdue invoices?",
            "New sales order",
            "Total revenue this month",
            "List draft orders",
        ],
    )


@router.post("")
def chat(req: ChatRequest, request: Request):
    """Process a chat message and return a structured response."""
    text = req.message.strip()
    if not text:
        return ChatResponse(type="error", message="Please enter a message.")

    intent = _detect_intent(text)

    handlers = {
        "navigate": _handle_navigate,
        "create": _handle_create,
        "count": _handle_count,
        "aggregate": _handle_aggregate,
        "query": _handle_query,
        "action": _handle_action,
        "help": _handle_help,
    }

    handler = handlers.get(intent, _handle_help)
    return handler(text)
