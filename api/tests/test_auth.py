"""Tests for auth API routes — setup, login, refresh, logout, me, change-password."""


class TestSetup:
    def test_check_setup_empty_db(self, client):
        resp = client.get("/api/auth/check-setup")
        assert resp.json()["setup_required"] is True

    def test_setup_creates_admin(self, client):
        resp = client.post("/api/auth/setup", json={
            "username": "admin",
            "email": "admin@test.com",
            "full_name": "Admin User",
            "password": "StrongPass1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Admin user created"
        assert "user_id" in data

    def test_setup_rejects_second_user(self, client, admin_user):
        resp = client.post("/api/auth/setup", json={
            "username": "admin2",
            "email": "admin2@test.com",
            "full_name": "Admin 2",
            "password": "StrongPass1",
        })
        # FastAPI returns the tuple as a list [dict, int]
        data = resp.json()
        if isinstance(data, list):
            assert data[0]["error"] == "Setup already completed"
        else:
            assert "error" in data

    def test_setup_rejects_weak_password(self, client):
        resp = client.post("/api/auth/setup", json={
            "username": "admin",
            "email": "admin@test.com",
            "full_name": "Admin User",
            "password": "weak",
        })
        data = resp.json()
        assert "error" in data

    def test_check_setup_after_creation(self, client, admin_user):
        resp = client.get("/api/auth/check-setup")
        assert resp.json()["setup_required"] is False


class TestLogin:
    def test_login_success(self, client, admin_user):
        resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == admin_user["email"]
        assert data["user"]["roles"] == ["System Manager"]

    def test_login_sets_refresh_cookie(self, client, admin_user):
        resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
        assert "refresh_token" in resp.cookies

    def test_login_wrong_password(self, client, admin_user):
        resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": "WrongPass1",
        })
        data = resp.json()
        assert data["error"] == "Invalid email or password"

    def test_login_nonexistent_email(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "nobody@test.com",
            "password": "Whatever1",
        })
        data = resp.json()
        assert data["error"] == "Invalid email or password"

    def test_login_lockout_after_5_failures(self, client, admin_user):
        for i in range(5):
            client.post("/api/auth/login", json={
                "email": admin_user["email"],
                "password": "WrongPass1",
            })

        # 6th attempt should say locked
        resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
        data = resp.json()
        assert "locked" in data["error"].lower()


class TestRefresh:
    def test_refresh_returns_new_access_token(self, client, admin_user):
        # Login first
        login_resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
        old_token = login_resp.json()["access_token"]
        refresh_cookie = login_resp.cookies.get("refresh_token")
        assert refresh_cookie is not None

        # Refresh using the cookie
        client.cookies.set("refresh_token", refresh_cookie)
        resp = client.post("/api/auth/refresh")
        data = resp.json()
        assert "access_token" in data
        assert data["access_token"] != old_token

    def test_refresh_without_cookie_fails(self, client):
        # Ensure no cookies
        client.cookies.clear()
        resp = client.post("/api/auth/refresh")
        data = resp.json()
        assert data["error"] == "No refresh token"


class TestLogout:
    def test_logout_clears_session(self, client, admin_user):
        # Login
        login_resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
        token = login_resp.json()["access_token"]
        refresh_cookie = login_resp.cookies.get("refresh_token")
        client.cookies.set("refresh_token", refresh_cookie)
        headers = {"Authorization": f"Bearer {token}"}

        # Logout
        resp = client.post("/api/auth/logout", headers=headers)
        assert resp.json()["message"] == "Logged out"

        # Refresh should fail now (session revoked)
        client.cookies.set("refresh_token", refresh_cookie)
        resp = client.post("/api/auth/refresh")
        data = resp.json()
        assert "error" in data


class TestMe:
    def test_me_returns_user_info(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        data = resp.json()
        assert "user" in data
        assert data["user"]["username"] == "testadmin"

    def test_me_without_token_fails(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestChangePassword:
    def test_change_password_success(self, client, admin_user, auth_headers):
        resp = client.post("/api/auth/change-password", json={
            "current_password": admin_user["password"],
            "new_password": "NewStrong1!",
        }, headers=auth_headers)
        data = resp.json()
        assert data["message"] == "Password changed successfully"

        # Old password no longer works
        resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": admin_user["password"],
        })
        assert resp.json()["error"] == "Invalid email or password"

        # New password works
        resp = client.post("/api/auth/login", json={
            "email": admin_user["email"],
            "password": "NewStrong1!",
        })
        assert "access_token" in resp.json()

    def test_change_password_wrong_current(self, client, auth_headers):
        resp = client.post("/api/auth/change-password", json={
            "current_password": "WrongCurrent1",
            "new_password": "NewStrong1!",
        }, headers=auth_headers)
        assert resp.json()["error"] == "Current password is incorrect"

    def test_change_password_weak_new(self, client, admin_user, auth_headers):
        resp = client.post("/api/auth/change-password", json={
            "current_password": admin_user["password"],
            "new_password": "weak",
        }, headers=auth_headers)
        assert "error" in resp.json()


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.json() == {"status": "ok", "version": "1.0.0"}
