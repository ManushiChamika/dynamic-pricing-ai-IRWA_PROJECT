import json
import uuid
import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def make_test_client():
    import importlib
    import sys

    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_complete_workflow_user_registration_to_pricing(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    client = make_test_client()

    email = unique_email("workflow")
    password = "correcthorse1"

    r = client.post("/api/register", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,name,category,current_price
LAPTOP001,Dell XPS 15,Laptops,1200.00
LAPTOP002,HP Pavilion,Laptops,800.00
LAPTOP003,Lenovo ThinkPad,Laptops,1000.00"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200
    upload_result = r.json()
    assert upload_result["total"] == 3

    r = client.get("/api/catalog", params={"token": token})
    assert r.status_code == 200
    products = r.json()
    assert len(products) == 3

    r = client.get("/api/catalog/LAPTOP001", params={"token": token})
    assert r.status_code == 200
    product = r.json()
    assert product["name"] == "Dell XPS 15"
    assert product["current_price"] == 1200.00

    with patch("core.agents.price_optimizer.api.propose_price") as mock_propose:
        mock_propose.return_value = {
            "proposed_price": 1150.00,
            "reason": "Competitive pricing adjustment",
            "margin": 0.15
        }

        r = client.post("/api/pricing/propose", params={"token": token}, json={"sku": "LAPTOP001"})
        assert r.status_code == 200
        proposal = r.json()
        assert "proposed_price" in proposal
        assert proposal["proposed_price"] == 1150.00

    with patch("core.agents.alert_service.api.list_incidents") as mock_incidents:
        mock_incidents.return_value = [
            {
                "id": "INC001",
                "severity": "high",
                "message": "Price drop detected for LAPTOP001",
                "status": "open",
                "created_at": "2025-01-01T12:00:00Z"
            }
        ]

        r = client.get("/api/alerts/incidents", params={"token": token})
        assert r.status_code == 200
        incidents = r.json()
        assert len(incidents) == 1
        assert incidents[0]["id"] == "INC001"


def test_workflow_catalog_to_price_streaming(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("streaming")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,name,category,current_price
PHONE001,iPhone 14,Phones,999.00
PHONE002,Samsung S23,Phones,899.00"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200

    with client.stream("GET", "/api/prices/stream", params={"token": token}) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        events_received = []
        for chunk in resp.iter_bytes():
            if chunk:
                decoded = chunk.decode("utf-8", errors="ignore")
                if decoded.strip() and not decoded.startswith(":"):
                    events_received.append(decoded)
                if len(events_received) >= 2:
                    break

        assert len(events_received) >= 1


def test_workflow_multi_user_catalog_isolation(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email1 = unique_email("user1")
    email2 = unique_email("user2")

    r = client.post("/api/register", json={"email": email1, "password": "correcthorse1"})
    assert r.status_code == 200
    token1 = r.json()["token"]

    r = client.post("/api/register", json={"email": email2, "password": "correcthorse2"})
    assert r.status_code == 200
    token2 = r.json()["token"]

    catalog1_csv = """sku,name,category,current_price
USER1_PROD1,Product A,Category1,100.00"""

    files = {"file": ("catalog1.csv", io.BytesIO(catalog1_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token1}, files=files)
    assert r.status_code == 200

    catalog2_csv = """sku,name,category,current_price
USER2_PROD1,Product B,Category2,200.00"""

    files = {"file": ("catalog2.csv", io.BytesIO(catalog2_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token2}, files=files)
    assert r.status_code == 200

    r = client.get("/api/catalog", params={"token": token1})
    assert r.status_code == 200
    user1_products = r.json()
    assert len(user1_products) == 1
    assert user1_products[0]["sku"] == "USER1_PROD1"

    r = client.get("/api/catalog", params={"token": token2})
    assert r.status_code == 200
    user2_products = r.json()
    assert len(user2_products) == 1
    assert user2_products[0]["sku"] == "USER2_PROD1"

    r = client.get("/api/catalog/USER2_PROD1", params={"token": token1})
    assert r.status_code == 404


def test_workflow_upload_optimize_delete(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("optimize")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,name,category,current_price
TABLET001,iPad Pro,Tablets,1099.00"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200

    r = client.get("/api/catalog/TABLET001", params={"token": token})
    assert r.status_code == 200
    product = r.json()
    assert product["current_price"] == 1099.00

    with patch("core.agents.price_optimizer.api.propose_price") as mock_propose:
        mock_propose.return_value = {
            "proposed_price": 1050.00,
            "reason": "Optimize for market competition",
            "margin": 0.12
        }

        r = client.post("/api/pricing/propose", params={"token": token}, json={"sku": "TABLET001"})
        assert r.status_code == 200
        proposal = r.json()
        assert proposal["proposed_price"] == 1050.00

    r = client.delete("/api/catalog/TABLET001", params={"token": token})
    assert r.status_code == 200

    r = client.get("/api/catalog/TABLET001", params={"token": token})
    assert r.status_code == 404


def test_workflow_chat_thread_with_context(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    client = make_test_client()

    email = unique_email("chat")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    r = client.post("/api/threads", params={"token": token}, json={"title": "Pricing Discussion"})
    assert r.status_code == 200
    tid = r.json()["id"]

    payload = {"user_name": "user", "content": "What should I price this laptop at?"}
    r = client.post(f"/api/threads/{tid}/messages", params={"token": token}, json=payload)
    assert r.status_code == 200
    response = r.json()
    assert response["role"] == "assistant"
    assert len(response["content"]) > 0

    r = client.get(f"/api/threads/{tid}/export", params={"token": token})
    assert r.status_code == 200
    exported = r.json()
    assert "messages" in exported
    assert len(exported["messages"]) >= 2


def test_workflow_json_catalog_upload(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("json")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_json = json.dumps([
        {"sku": "WATCH001", "name": "Apple Watch", "category": "Wearables", "current_price": 399.00},
        {"sku": "WATCH002", "name": "Samsung Watch", "category": "Wearables", "current_price": 299.00}
    ])

    files = {"file": ("catalog.json", io.BytesIO(catalog_json.encode()), "application/json")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200
    upload_result = r.json()
    assert upload_result["total"] == 2

    r = client.get("/api/catalog", params={"token": token})
    assert r.status_code == 200
    products = r.json()
    assert len(products) == 2


def test_workflow_bulk_delete_catalog(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("bulkdelete")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,name,category,current_price
BULK001,Product 1,Category,100.00
BULK002,Product 2,Category,200.00
BULK003,Product 3,Category,300.00"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200

    r = client.get("/api/catalog", params={"token": token})
    assert r.status_code == 200
    products_before = r.json()
    assert len(products_before) == 3

    r = client.delete("/api/catalog", params={"token": token})
    assert r.status_code == 200

    r = client.get("/api/catalog", params={"token": token})
    assert r.status_code == 200
    products_after = r.json()
    assert len(products_after) == 0


def test_workflow_alert_acknowledgement(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("alert")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    with patch("core.agents.alert_service.api.list_incidents") as mock_list, \
         patch("core.agents.alert_service.api.acknowledge_incident") as mock_ack:

        mock_list.return_value = [
            {
                "id": "INC123",
                "severity": "medium",
                "message": "Price variance detected",
                "status": "open",
                "created_at": "2025-01-01T12:00:00Z"
            }
        ]

        r = client.get("/api/alerts/incidents", params={"token": token})
        assert r.status_code == 200
        incidents = r.json()
        assert len(incidents) == 1

        mock_ack.return_value = {"status": "acknowledged", "id": "INC123"}

        r = client.post("/api/alerts/incidents/INC123/acknowledge", params={"token": token})
        assert r.status_code == 200
        result = r.json()
        assert result["status"] == "acknowledged"


def test_workflow_settings_persistence_across_sessions(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    monkeypatch.setenv("DEV_MODE", "1")

    client = make_test_client()

    r = client.get("/api/settings")
    assert r.status_code == 200
    settings = r.json()["settings"]
    assert settings["show_timestamps"] is True
    assert settings["show_metadata_panel"] is True

    monkeypatch.setenv("DEV_MODE", "0")

    client2 = make_test_client()
    r = client2.get("/api/settings")
    assert r.status_code == 200
    settings = r.json()["settings"]
    assert settings["show_timestamps"] is False
    assert settings["show_metadata_panel"] is False
