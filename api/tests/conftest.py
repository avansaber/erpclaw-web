"""Test fixtures for erpclaw-web API tests."""

import os
import sys
import tempfile

import pytest

# Ensure api/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use a temp database for tests
_tmp_dir = tempfile.mkdtemp()
os.environ["ERPCLAW_WEB_DB"] = os.path.join(_tmp_dir, "test_web.sqlite")


@pytest.fixture(autouse=True)
def fresh_db():
    """Reset the web database before each test."""
    import sqlite3

    db_path = os.environ["ERPCLAW_WEB_DB"]

    # Drop all tables
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for (name,) in tables:
            conn.execute(f"DROP TABLE IF EXISTS {name}")
        conn.commit()
        conn.close()

    # Re-initialize
    from init_db import init_web_db
    init_web_db()
    yield


@pytest.fixture()
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture()
def admin_user(client):
    """Create an admin user and return credentials."""
    resp = client.post("/api/auth/setup", json={
        "username": "testadmin",
        "email": "admin@test.com",
        "full_name": "Test Admin",
        "password": "StrongPass1!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    return {
        "email": "admin@test.com",
        "password": "StrongPass1!",
        "user_id": data["user_id"],
    }


@pytest.fixture()
def auth_headers(client, admin_user):
    """Login and return Authorization headers."""
    resp = client.post("/api/auth/login", json={
        "email": admin_user["email"],
        "password": admin_user["password"],
    })
    data = resp.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}
