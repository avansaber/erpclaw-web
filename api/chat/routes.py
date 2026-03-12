"""Chat API routes -- session CRUD and SSE streaming.

Adapted for erpclaw-web: uses web.sqlite for chat tables, erpclaw-web's
auth middleware (request.state.user), and the OpenClaw gateway for AI.
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from db import get_web_db
from .ai_client import stream_chat, single_chat
from .composition import detect_write_intent, extract_params_from_message, build_composition_text
from .entity_resolver import resolve_entity

router = APIRouter(prefix="/api/chat", tags=["chat"])

MAX_HISTORY = 50  # messages to include in AI context window


def _get_user(request: Request) -> dict | None:
    """Extract user info from request state (set by AuthMiddleware).

    Returns dict with at least 'id', 'username', 'roles', or None.
    """
    return getattr(request.state, "user", None)


def _require_user(request: Request) -> tuple[str, None] | tuple[None, JSONResponse]:
    """Return (user_id, None) on success or (None, error_response) on failure."""
    user = _get_user(request)
    if not user:
        return None, JSONResponse(
            {"status": "error", "message": "Authentication required"}, status_code=401
        )
    return user["id"], None


# -- Schema migration: create chat tables if they don't exist --

_tables_initialized = False


def _ensure_chat_tables():
    """Create chat_session and chat_message tables if they don't exist.

    These live in erpclaw-web's web.sqlite alongside auth tables.
    Called lazily on first request to avoid import-time DB access.
    """
    global _tables_initialized
    if _tables_initialized:
        return

    conn = get_web_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_session (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES web_user(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'New Chat',
                context TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_message (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES chat_session(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                context TEXT DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_chat_session_user
                ON chat_session(user_id, updated_at DESC);

            CREATE INDEX IF NOT EXISTS idx_chat_message_session
                ON chat_message(session_id, created_at ASC);
        """)
        conn.commit()
        _tables_initialized = True
    finally:
        conn.close()


# -- Session CRUD ---------------------------------------------------------------


@router.post("/sessions")
async def create_session(request: Request):
    """Create a new chat session."""
    user_id, err = _require_user(request)
    if err:
        return err
    _ensure_chat_tables()

    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = str(uuid.uuid4())
    title = body.get("title", "New Chat")
    context = json.dumps(body.get("context", {}))
    now = datetime.now(timezone.utc).isoformat()

    conn = get_web_db()
    try:
        conn.execute(
            """INSERT INTO chat_session (id, user_id, title, context, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, title, context, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "status": "ok",
        "session": {
            "id": session_id,
            "title": title,
            "context": body.get("context", {}),
            "created_at": now,
        },
    }


@router.get("/sessions")
async def list_sessions(request: Request):
    """List current user's chat sessions, most recent first."""
    user_id, err = _require_user(request)
    if err:
        return err
    _ensure_chat_tables()

    conn = get_web_db()
    try:
        rows = conn.execute(
            """SELECT id, title, context, created_at, updated_at
               FROM chat_session WHERE user_id = ? ORDER BY updated_at DESC LIMIT 50""",
            (user_id,),
        ).fetchall()

        sessions = []
        for r in rows:
            ctx = r["context"]
            sessions.append({
                "id": r["id"],
                "title": r["title"],
                "context": json.loads(ctx) if ctx else {},
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            })
    finally:
        conn.close()

    return {"status": "ok", "sessions": sessions}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, request: Request):
    """Get messages for a chat session (owner only)."""
    user_id, err = _require_user(request)
    if err:
        return err
    _ensure_chat_tables()

    conn = get_web_db()
    try:
        # Verify ownership
        session = conn.execute(
            "SELECT id FROM chat_session WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
        if not session:
            return JSONResponse(
                {"status": "error", "message": "Session not found"}, status_code=404
            )

        rows = conn.execute(
            """SELECT id, role, content, context, created_at
               FROM chat_message WHERE session_id = ? ORDER BY created_at ASC""",
            (session_id,),
        ).fetchall()

        messages = []
        for r in rows:
            ctx = r["context"]
            messages.append({
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "context": json.loads(ctx) if ctx else {},
                "created_at": r["created_at"],
            })
    finally:
        conn.close()

    return {"status": "ok", "messages": messages}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    """Delete a chat session and all its messages (owner only)."""
    user_id, err = _require_user(request)
    if err:
        return err
    _ensure_chat_tables()

    conn = get_web_db()
    try:
        # Verify ownership
        session = conn.execute(
            "SELECT id FROM chat_session WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
        if not session:
            return JSONResponse(
                {"status": "error", "message": "Session not found"}, status_code=404
            )

        # CASCADE handles messages
        conn.execute("DELETE FROM chat_session WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

    return {"status": "ok", "message": "Session deleted"}


# -- Entity Resolution ---------------------------------------------------------


@router.post("/resolve-entity")
async def resolve_entity_endpoint(request: Request):
    """Resolve a natural language entity reference to DB matches.

    Body: { entity_type?: string, query: string, limit?: int }
    Returns: { matches: [{id, name, entity_type, confidence, source_detail}] }
    """
    user_id, err = _require_user(request)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"status": "error", "message": "Invalid request body"}, status_code=400
        )

    query = body.get("query", "").strip()
    if not query:
        return JSONResponse(
            {"status": "error", "message": "Query is required"}, status_code=400
        )

    entity_type = body.get("entity_type")
    limit = min(body.get("limit", 5), 20)

    matches = resolve_entity(entity_type, query, limit)
    return {"status": "ok", "query": query, "matches": matches}


# -- SSE Streaming -------------------------------------------------------------


def _save_message(
    conn, session_id: str, role: str, content: str, context: dict | None = None
) -> str:
    """Persist a chat message to the database. Returns message id."""
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO chat_message (id, session_id, role, content, context, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (msg_id, session_id, role, content, json.dumps(context or {}), now),
    )
    # Update session timestamp
    conn.execute(
        "UPDATE chat_session SET updated_at = ? WHERE id = ?", (now, session_id)
    )
    conn.commit()
    return msg_id


@router.post("/stream")
async def chat_stream(request: Request):
    """Stream an AI response via SSE. Creates session if needed, persists messages."""
    user_id, err = _require_user(request)
    if err:
        return err
    _ensure_chat_tables()

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"status": "error", "message": "Invalid request body"}, status_code=400
        )

    message = body.get("message", "").strip()
    if not message:
        return JSONResponse(
            {"status": "error", "message": "Message is required"}, status_code=400
        )

    context = body.get("context", {})
    # Merge resolved entities into context for AI system prompt
    resolved_entities = body.get("resolved_entities")
    if resolved_entities:
        context["resolved_entities"] = resolved_entities
    session_id = body.get("session_id")

    conn = get_web_db()
    try:
        # Auto-create session if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            # Use first ~50 chars of message as title
            title = message[:50] + ("..." if len(message) > 50 else "")
            conn.execute(
                """INSERT INTO chat_session (id, user_id, title, context, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, user_id, title, json.dumps(context), now, now),
            )
            conn.commit()
        else:
            # Verify ownership
            session = conn.execute(
                "SELECT id FROM chat_session WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
            if not session:
                return JSONResponse(
                    {"status": "error", "message": "Session not found"}, status_code=404
                )

        # Save user message
        _save_message(conn, session_id, "user", message, context)

        # Load conversation history
        history_rows = conn.execute(
            """SELECT role, content FROM chat_message
               WHERE session_id = ? ORDER BY created_at ASC""",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()

    # Build messages for AI (last N messages)
    ai_messages = []
    rows_to_use = history_rows[-MAX_HISTORY:]
    for r in rows_to_use:
        role = r["role"]
        content = r["content"]
        if role in ("user", "assistant"):
            ai_messages.append({"role": role, "content": content})

    # Auto-resolve entities from message if none provided
    if not resolved_entities and context.get("skill"):
        try:
            auto_matches = resolve_entity(None, message, 3)
            high_conf = [m for m in auto_matches if m.get("confidence", 0) >= 0.8]
            if high_conf:
                context["resolved_entities"] = high_conf
        except Exception:
            pass  # Non-critical

    # -- Write-action interception -------------------------------------------
    # Detect write intent and return a composition block instead of letting
    # the OpenClaw gateway execute the action directly via tool-calling.
    skill = context.get("skill", "")
    write_intent = detect_write_intent(message, skill) if skill else None

    if write_intent:
        resolved, unresolved = extract_params_from_message(
            message, write_intent["meta"], context
        )
        composition_text = build_composition_text(
            write_intent["action"], skill, resolved, unresolved
        )

        async def composition_generator():
            yield f"data: {json.dumps({'type': 'delta', 'text': composition_text})}\n\n"
            save_conn = get_web_db()
            try:
                _save_message(save_conn, session_id, "assistant", composition_text, context)
            finally:
                save_conn.close()
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

        return StreamingResponse(
            composition_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # -- Normal AI streaming (read queries, questions, general chat) -----------

    async def event_generator():
        full_response = []
        try:
            async for chunk in stream_chat(ai_messages, context):
                full_response.append(chunk)
                yield f"data: {json.dumps({'type': 'delta', 'text': chunk})}\n\n"
        except Exception as e:
            error_text = f"[Error: {str(e)[:200]}]"
            full_response.append(error_text)
            yield f"data: {json.dumps({'type': 'delta', 'text': error_text})}\n\n"

        # Persist assistant response
        complete_text = "".join(full_response)
        if complete_text:
            save_conn = get_web_db()
            try:
                _save_message(save_conn, session_id, "assistant", complete_text, context)
            finally:
                save_conn.close()

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# -- Smart Context Suggestions -------------------------------------------------


@router.post("/suggest-next")
async def suggest_next(request: Request):
    """Suggest a logical next action after a completed action.

    Body: { completed_action: str, skill: str, response_data?: dict }
    Returns: { suggestion: str, actions?: [{action, label}] }
    """
    user_id, err = _require_user(request)
    if err:
        return err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"status": "error", "message": "Invalid request body"}, status_code=400
        )

    completed_action = body.get("completed_action", "")
    skill = body.get("skill", "")
    if not completed_action or not skill:
        return JSONResponse(
            {"status": "error", "message": "completed_action and skill are required"},
            status_code=400,
        )

    response_data = body.get("response_data", {})
    record_id = response_data.get("id", "")

    prompt = (
        f"The user just completed the action '{completed_action}' in the '{skill}' skill."
    )
    if record_id:
        prompt += f" The created/updated record ID is '{record_id}'."
    prompt += (
        " Suggest 1-2 logical next steps as a brief sentence."
        " Focus on the most common workflow continuation."
        " Keep it under 50 words."
    )

    context = {"skill": skill}
    try:
        suggestion = await single_chat(
            [{"role": "user", "content": prompt}],
            context,
            max_tokens=200,
        )
    except Exception:
        suggestion = ""

    if not suggestion:
        return {"status": "ok", "suggestion": None}

    return {"status": "ok", "suggestion": suggestion.strip()}
