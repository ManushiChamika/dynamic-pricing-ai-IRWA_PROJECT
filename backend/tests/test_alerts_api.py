import uuid
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


def make_test_client():
    import importlib
    import sys

    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "alerts") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_get_incidents_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    response = client.get("/api/alerts/incidents")
    
    assert response.status_code == 401
    assert "Authentication token required" in response.json()["detail"]


def test_get_incidents_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    response = client.get("/api/alerts/incidents?token=invalid_token")
    
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_incidents_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("incidents")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_incidents = [
        {
            "incident_id": "inc_001",
            "status": "active",
            "severity": "high",
            "message": "Price deviation detected"
        }
    ]
    
    with patch("core.agents.alert_service.api.list_incidents", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_incidents
        
        response = client.get(f"/api/alerts/incidents?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["incident_id"] == "inc_001"


@pytest.mark.asyncio
async def test_get_incidents_with_status_filter(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("filter")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_incidents = [
        {
            "incident_id": "inc_002",
            "status": "resolved",
            "severity": "medium",
            "message": "Issue resolved"
        }
    ]
    
    with patch("core.agents.alert_service.api.list_incidents", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_incidents
        
        response = client.get(f"/api/alerts/incidents?token={token}&status=resolved")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_acknowledge_incident_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("ack")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    incident_id = "inc_003"
    mock_result = {
        "success": True,
        "incident_id": incident_id,
        "status": "acknowledged"
    }
    
    with patch("core.agents.alert_service.api.ack_incident", new_callable=AsyncMock) as mock_ack:
        mock_ack.return_value = mock_result
        
        response = client.post(f"/api/alerts/incidents/{incident_id}/ack?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["incident_id"] == incident_id


def test_acknowledge_incident_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    response = client.post("/api/alerts/incidents/inc_001/ack")
    
    assert response.status_code == 401


def test_acknowledge_incident_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    response = client.post("/api/alerts/incidents/inc_001/ack?token=invalid_token")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_resolve_incident_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("resolve")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    incident_id = "inc_004"
    mock_result = {
        "success": True,
        "incident_id": incident_id,
        "status": "resolved"
    }
    
    with patch("core.agents.alert_service.api.resolve_incident", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = mock_result
        
        response = client.post(f"/api/alerts/incidents/{incident_id}/resolve?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "resolved"


def test_resolve_incident_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    response = client.post("/api/alerts/incidents/inc_001/resolve")
    
    assert response.status_code == 401


def test_resolve_incident_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    response = client.post("/api/alerts/incidents/inc_001/resolve?token=invalid_token")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_incidents_handles_service_error(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("error")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("core.agents.alert_service.api.list_incidents", new_callable=AsyncMock) as mock_list:
        mock_list.side_effect = Exception("Service unavailable")
        
        response = client.get(f"/api/alerts/incidents?token={token}")
        
        assert response.status_code == 500
        assert "Service unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_acknowledge_incident_handles_service_error(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("ackerr")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("core.agents.alert_service.api.ack_incident", new_callable=AsyncMock) as mock_ack:
        mock_ack.side_effect = Exception("Database error")
        
        response = client.post(f"/api/alerts/incidents/inc_001/ack?token={token}")
        
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_resolve_incident_handles_service_error(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("reserr")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("core.agents.alert_service.api.resolve_incident", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.side_effect = Exception("Update failed")
        
        response = client.post(f"/api/alerts/incidents/inc_001/resolve?token={token}")
        
        assert response.status_code == 500
        assert "Update failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_incidents_empty_list(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()
    
    email = unique_email("empty")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("core.agents.alert_service.api.list_incidents", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        
        response = client.get(f"/api/alerts/incidents?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
