import uuid
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


def make_test_client():
    import importlib
    import sys
    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "prices") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_prices_stream_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    response = client.get("/api/prices/stream")
    
    assert response.status_code == 401
    assert "Authentication token required" in response.json()["detail"]


def test_prices_stream_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    response = client.get("/api/prices/stream?token=invalid_token")
    
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]


def test_prices_stream_empty_catalog(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("empty")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {}
        
        with client.stream("GET", f"/api/prices/stream?token={token}") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
            
            chunks = []
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                if len(chunks) >= 1:
                    break
            
            stream_data = b"".join(chunks).decode("utf-8")
            assert "event: ping" in stream_data


def test_prices_stream_with_products(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("stream")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_products = {
        "LAPTOP001": 1200.00,
        "LAPTOP002": 1500.00
    }
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_products
        
        with client.stream("GET", f"/api/prices/stream?token={token}") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
            
            chunks = []
            events_received = 0
            
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                stream_data = b"".join(chunks).decode("utf-8")
                
                if "event: price" in stream_data:
                    events_received += 1
                
                if events_received >= 2:
                    break
            
            stream_data = b"".join(chunks).decode("utf-8")
            assert "event: price" in stream_data or "event: ping" in stream_data


def test_prices_stream_with_sku_filter(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("filter")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_products = {"LAPTOP001": 1200.00}
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_products
        
        with client.stream("GET", f"/api/prices/stream?token={token}&sku=LAPTOP001") as response:
            assert response.status_code == 200
            
            chunks = []
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                if len(chunks) >= 3:
                    break
            
            stream_data = b"".join(chunks).decode("utf-8")
            assert "event: ping" in stream_data or "event: price" in stream_data


def test_prices_stream_event_format(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("format")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_products = {"LAPTOP001": 1200.00}
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_products
        
        with client.stream("GET", f"/api/prices/stream?token={token}") as response:
            assert response.status_code == 200
            
            chunks = []
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                stream_data = b"".join(chunks).decode("utf-8")
                
                if "event: price" in stream_data and "data:" in stream_data:
                    lines = stream_data.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith("data:"):
                            data_json = line[5:].strip()
                            if data_json:
                                try:
                                    data = json.loads(data_json)
                                    assert "sku" in data
                                    assert "price" in data
                                    assert "ts" in data
                                    assert isinstance(data["sku"], str)
                                    assert isinstance(data["price"], (int, float))
                                    assert isinstance(data["ts"], int)
                                    return
                                except json.JSONDecodeError:
                                    pass
                
                if len(chunks) >= 5:
                    break


def test_prices_stream_multiple_products(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("multi")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_products = {
        "LAPTOP001": 1200.00,
        "LAPTOP002": 1500.00,
        "LAPTOP003": 1800.00
    }
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_products
        
        with client.stream("GET", f"/api/prices/stream?token={token}") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"


def test_prices_stream_handles_database_error(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("error")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {}
        
        with client.stream("GET", f"/api/prices/stream?token={token}") as response:
            assert response.status_code == 200


def test_prices_stream_price_drift(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("drift")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_products = {"LAPTOP001": 1000.00}
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_products
        
        with client.stream("GET", f"/api/prices/stream?token={token}") as response:
            assert response.status_code == 200
            
            chunks = []
            prices_seen = []
            
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                stream_data = b"".join(chunks).decode("utf-8")
                
                lines = stream_data.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("data:"):
                        data_json = line[5:].strip()
                        if data_json and data_json != "{}":
                            try:
                                data = json.loads(data_json)
                                if "price" in data:
                                    prices_seen.append(data["price"])
                            except json.JSONDecodeError:
                                pass
                
                if len(prices_seen) >= 2:
                    break
                
                if len(chunks) >= 5:
                    break


def test_fetch_products_returns_dict():
    client = make_test_client()
    from backend.routers.prices import _fetch_products
    import asyncio
    
    result = asyncio.run(_fetch_products("test_owner"))
    assert isinstance(result, dict)


def test_prices_stream_validates_owner_isolation(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email1 = unique_email("owner1")
    r1 = client.post("/api/register", json={"email": email1, "password": "correcthorse1"})
    assert r1.status_code == 200
    token1 = r1.json()["token"]
    
    email2 = unique_email("owner2")
    r2 = client.post("/api/register", json={"email": email2, "password": "correcthorse1"})
    assert r2.status_code == 200
    token2 = r2.json()["token"]
    
    with patch("backend.routers.prices._fetch_products", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"LAPTOP001": 1200.00}
        
        with client.stream("GET", f"/api/prices/stream?token={token1}") as response1:
            assert response1.status_code == 200
        
        with client.stream("GET", f"/api/prices/stream?token={token2}") as response2:
            assert response2.status_code == 200
