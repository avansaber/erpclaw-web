"""Tests for chat AI endpoint — intent detection, navigation, queries."""


class TestIntentDetection:
    def test_navigate_customers(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "show me customers"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] == "navigate"
        assert data["href"] == "/customer"

    def test_navigate_dashboard(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "go to dashboard"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] == "navigate"
        assert data["href"] == "/"

    def test_create_customer(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "new customer"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] == "navigate"
        assert data["href"] == "/customer/new"

    def test_create_invoice(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "create an invoice"}, headers=auth_headers)
        data = resp.json()
        assert data["href"] is not None
        assert "/new" in data["href"]

    def test_help(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "help"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] == "help"
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    def test_count_query(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "how many customers?"}, headers=auth_headers)
        data = resp.json()
        # Will be "count" or "error" (if no ERP DB locally)
        assert data["type"] in ("query", "error")

    def test_aggregate_revenue(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "total revenue this month"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] in ("query", "error")

    def test_action_submit(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "submit order SO-00012"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] in ("action", "help")
        if data["type"] == "action":
            assert data["action"]["action"] == "submit-sales-order"
            assert data["action"]["params"]["id"] == "SO-00012"

    def test_empty_message(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": ""}, headers=auth_headers)
        data = resp.json()
        assert data["type"] == "error"

    def test_requires_auth(self, client):
        resp = client.post("/api/chat", json={"message": "hello"})
        assert resp.status_code == 401

    def test_list_query(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "show overdue invoices"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] in ("query", "error")

    def test_entity_alias_orders(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "show me orders"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] in ("navigate", "query")

    def test_suggestions_in_help(self, client, auth_headers):
        resp = client.post("/api/chat", json={"message": "what can I do?"}, headers=auth_headers)
        data = resp.json()
        assert data["type"] == "help"
        assert any("customer" in s.lower() for s in data.get("suggestions", []))
