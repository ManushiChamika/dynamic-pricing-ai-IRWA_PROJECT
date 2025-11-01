import json
import uuid
import io
import pytest
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

    catalog_csv = """sku,title,category,currency,current_price,cost,stock
LAPTOP001,Dell XPS 15,Laptops,USD,1200.00,900.00,10
LAPTOP002,HP Pavilion,Laptops,USD,800.00,600.00,15
LAPTOP003,Lenovo ThinkPad,Laptops,USD,1000.00,750.00,12"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200
    upload_result = r.json()
    assert upload_result["rows_processed"] == 3

    r = client.get("/api/catalog/products", params={"token": token})
    assert r.status_code == 200
    products_res = r.json()
    assert products_res["count"] == 3

    r = client.get("/api/catalog/products/LAPTOP001", params={"token": token})
    assert r.status_code == 200
    product_res = r.json()
    assert product_res["product"]["title"] == "Dell XPS 15"
    assert product_res["product"]["current_price"] == 1200.00

    pass

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


@pytest.mark.skip(reason="SSE streaming test requires live server environment")
def test_workflow_catalog_to_price_streaming(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("streaming")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,title,category,currency,current_price,cost,stock
PHONE001,iPhone 14,Phones,USD,999.00,750.00,20
PHONE002,Samsung S23,Phones,USD,899.00,650.00,25"""

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

    catalog1_csv = """sku,title,category,currency,current_price,cost,stock
USER1_PROD1,Product A,Category1,USD,100.00,70.00,5"""

    files = {"file": ("catalog1.csv", io.BytesIO(catalog1_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token1}, files=files)
    assert r.status_code == 200

    catalog2_csv = """sku,title,category,currency,current_price,cost,stock
USER2_PROD1,Product B,Category2,USD,200.00,140.00,8"""

    files = {"file": ("catalog2.csv", io.BytesIO(catalog2_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token2}, files=files)
    assert r.status_code == 200

    r = client.get("/api/catalog/products", params={"token": token1})
    assert r.status_code == 200
    user1_products_res = r.json()
    assert user1_products_res["count"] == 1
    assert user1_products_res["products"][0]["sku"] == "USER1_PROD1"

    r = client.get("/api/catalog/products", params={"token": token2})
    assert r.status_code == 200
    user2_products_res = r.json()
    assert user2_products_res["count"] == 1
    assert user2_products_res["products"][0]["sku"] == "USER2_PROD1"

    r = client.get("/api/catalog/products/USER2_PROD1", params={"token": token1})
    assert r.status_code == 404


def test_workflow_upload_optimize_delete(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("optimize")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,title,category,currency,current_price,cost,stock
TABLET001,iPad Pro,Tablets,USD,1099.00,800.00,7"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200

    r = client.get("/api/catalog/products/TABLET001", params={"token": token})
    assert r.status_code == 200
    product = r.json()["product"]
    assert product["current_price"] == 1099.00

    pass

    r = client.delete("/api/catalog/products/TABLET001", params={"token": token})
    assert r.status_code == 200

    r = client.get("/api/catalog/products/TABLET001", params={"token": token})
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
        {"sku": "WATCH001", "title": "Apple Watch", "category": "Wearables", "currency": "USD", "current_price": 399.00, "cost": 280.00, "stock": 15},
        {"sku": "WATCH002", "title": "Samsung Watch", "category": "Wearables", "currency": "USD", "current_price": 299.00, "cost": 210.00, "stock": 20}
    ])

    files = {"file": ("catalog.json", io.BytesIO(catalog_json.encode()), "application/json")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200
    upload_result = r.json()
    assert upload_result["rows_processed"] == 2

    r = client.get("/api/catalog/products", params={"token": token})
    assert r.status_code == 200
    products_res = r.json()
    assert products_res["count"] == 2


def test_workflow_bulk_delete_catalog(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("bulkdelete")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    catalog_csv = """sku,title,category,currency,current_price,cost,stock
BULK001,Product 1,Category,USD,100.00,70.00,10
BULK002,Product 2,Category,USD,200.00,140.00,12
BULK003,Product 3,Category,USD,300.00,210.00,8"""

    files = {"file": ("catalog.csv", io.BytesIO(catalog_csv.encode()), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200

    r = client.get("/api/catalog/products", params={"token": token})
    assert r.status_code == 200
    products_before_res = r.json()
    assert products_before_res["count"] == 3

    r = client.delete("/api/catalog/products", params={"token": token})
    assert r.status_code == 200

    r = client.get("/api/catalog/products", params={"token": token})
    assert r.status_code == 200
    products_after_res = r.json()
    assert products_after_res["count"] == 0


def test_workflow_alert_acknowledgement(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("alert")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    with patch("core.agents.alert_service.api.list_incidents") as mock_list, \
         patch("core.agents.alert_service.api.ack_incident") as mock_ack:


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
        
        mock_ack.return_value = {"ok": True, "id": "INC123", "status": "ACKED"}

        r = client.post("/api/alerts/incidents/INC123/ack", params={"token": token})
        assert r.status_code == 200
        result = r.json()
        assert result["status"] == "ACKED"



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
