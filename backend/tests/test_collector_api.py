import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


def make_test_client():
    import importlib
    import sys

    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "collector") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_start_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    r = client.post("/api/collector/start", json={"sku": "SKU1"})
    assert r.status_code == 422


def test_start_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    r = client.post("/api/collector/start?token=bad", json={"sku": "SKU1"})
    assert r.status_code == 401


def test_start_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    email = unique_email("startok")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    with patch("backend.routers.collector.Tools") as MockTools:
        mock_tools = AsyncMock()
        mock_tools.start_collection_job.return_value = {"ok": True, "request_id": "abc"}
        MockTools.return_value = mock_tools

        r2 = client.post(f"/api/collector/start?token={token}", json={"sku": "SKU1"})
        assert r2.status_code == 200
        body = r2.json()
        assert body["ok"] is True
        assert body["request_id"] == "abc"


def test_start_error_from_tools(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    email = unique_email("starterr")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    with patch("backend.routers.collector.Tools") as MockTools:
        mock_tools = AsyncMock()
        mock_tools.start_collection_job.return_value = {"ok": False, "error": "boom"}
        MockTools.return_value = mock_tools

        r2 = client.post(f"/api/collector/start?token={token}", json={"sku": "S"})
        assert r2.status_code == 400
        assert "Failed" in r2.json()["detail"] or "boom" in r2.json()["detail"]
