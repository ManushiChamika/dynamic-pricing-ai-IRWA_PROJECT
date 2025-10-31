import uuid
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def unique_email(prefix: str = "catalog") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_delete_all_products_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    email = unique_email("delete")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    response = client.delete(f"/api/catalog/products?token={token}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "rows_affected" in data
    assert isinstance(data["rows_affected"], int)


def test_delete_all_products_no_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    response = client.delete("/api/catalog/products")
    
    assert response.status_code == 422


def test_delete_all_products_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    response = client.delete("/api/catalog/products?token=invalid_token")
    
    assert response.status_code == 401


def test_delete_all_products_idempotent(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    email = unique_email("idempotent")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    response1 = client.delete(f"/api/catalog/products?token={token}")
    assert response1.status_code == 200
    
    response2 = client.delete(f"/api/catalog/products?token={token}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["rows_affected"] == 0


def test_delete_all_products_isolation(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    email1 = unique_email("user1")
    r1 = client.post("/api/register", json={"email": email1, "password": "correcthorse1"})
    assert r1.status_code == 200
    token1 = r1.json()["token"]
    
    email2 = unique_email("user2")
    r2 = client.post("/api/register", json={"email": email2, "password": "correcthorse1"})
    assert r2.status_code == 200
    token2 = r2.json()["token"]
    
    response1 = client.delete(f"/api/catalog/products?token={token1}")
    assert response1.status_code == 200
    
    response2 = client.get(f"/api/catalog/products?token={token2}")
    assert response2.status_code == 200
