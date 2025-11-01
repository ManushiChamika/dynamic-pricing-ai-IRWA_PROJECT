import uuid
import io
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


def make_test_client():
    import importlib
    import sys

    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "catalog") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def create_csv_file(data: str) -> io.BytesIO:
    return io.BytesIO(data.encode('utf-8'))


def test_upload_catalog_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,1200,800,10"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post("/api/catalog/upload", files=files)
    
    assert response.status_code == 422


def test_upload_catalog_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,1200,800,10"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post("/api/catalog/upload?token=invalid_token", files=files)
    
    assert response.status_code == 401


def test_upload_catalog_csv_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("upload")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,1200,800,10"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.upsert_products.return_value = 1
        MockRepo.return_value = mock_instance
        
        response = client.post(f"/api/catalog/upload?token={token}", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["filename"] == "test.csv"
        assert data["rows_processed"] == 1


def test_upload_catalog_json_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("json")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    json_content = json.dumps([{
        "sku": "LAPTOP001",
        "title": "Test Laptop",
        "currency": "USD",
        "current_price": 1200,
        "cost": 800,
        "stock": 10
    }])
    files = {"file": ("test.json", io.BytesIO(json_content.encode('utf-8')), "application/json")}
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.upsert_products.return_value = 1
        MockRepo.return_value = mock_instance
        
        response = client.post(f"/api/catalog/upload?token={token}", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


def test_upload_catalog_invalid_file_type(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("invalid")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    files = {"file": ("test.txt", io.BytesIO(b"invalid content"), "text/plain")}
    
    response = client.post(f"/api/catalog/upload?token={token}", files=files)
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_upload_catalog_missing_columns(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("missing")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title\nLAPTOP001,Test Laptop"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post(f"/api/catalog/upload?token={token}", files=files)
    
    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_upload_catalog_negative_price(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("negative")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,-1200,800,10"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post(f"/api/catalog/upload?token={token}", files=files)
    
    assert response.status_code == 400
    assert "non-negative" in response.json()["detail"]


def test_upload_catalog_duplicate_sku(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("duplicate")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,1200,800,10\nLAPTOP001,Duplicate,USD,1500,900,5"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post(f"/api/catalog/upload?token={token}", files=files)
    
    assert response.status_code == 400
    assert "Duplicate SKU" in response.json()["detail"]


def test_get_products_requires_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    response = client.get("/api/catalog/products")
    
    assert response.status_code == 422


def test_get_products_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("getall")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_products = [
        {"sku": "LAPTOP001", "title": "Laptop 1", "current_price": 1200},
        {"sku": "LAPTOP002", "title": "Laptop 2", "current_price": 1500}
    ]
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_products_by_owner.return_value = mock_products
        MockRepo.return_value = mock_instance
        
        response = client.get(f"/api/catalog/products?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["products"]) == 2


def test_get_product_by_sku_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("getone")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    mock_product = {"sku": "LAPTOP001", "title": "Laptop 1", "current_price": 1200}
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_product_by_sku_and_owner.return_value = mock_product
        MockRepo.return_value = mock_instance
        
        response = client.get(f"/api/catalog/products/LAPTOP001?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["product"]["sku"] == "LAPTOP001"


def test_get_product_not_found(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("notfound")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_product_by_sku_and_owner.return_value = None
        MockRepo.return_value = mock_instance
        
        response = client.get(f"/api/catalog/products/NOTEXIST?token={token}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_delete_product_success(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("delone")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.delete_product_by_owner.return_value = 1
        MockRepo.return_value = mock_instance
        
        response = client.delete(f"/api/catalog/products/LAPTOP001?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rows_affected"] == 1


def test_delete_product_not_found(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("delnf")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.delete_product_by_owner.return_value = 0
        MockRepo.return_value = mock_instance
        
        response = client.delete(f"/api/catalog/products/NOTEXIST?token={token}")
        
        assert response.status_code == 404


def test_upload_catalog_invalid_data_types(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("badtype")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,notanumber,800,10"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post(f"/api/catalog/upload?token={token}", files=files)
    
    assert response.status_code == 400
    assert "Invalid data types" in response.json()["detail"] or "Failed to parse" in response.json()["detail"]


def test_upload_catalog_multiple_products(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("multi")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = """sku,title,currency,current_price,cost,stock
LAPTOP001,Laptop 1,USD,1200,800,10
LAPTOP002,Laptop 2,USD,1500,900,5
LAPTOP003,Laptop 3,USD,1800,1000,3"""
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.upsert_products.return_value = 3
        MockRepo.return_value = mock_instance
        
        response = client.post(f"/api/catalog/upload?token={token}", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rows_processed"] == 3


def test_get_products_empty_catalog(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("empty")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_products_by_owner.return_value = []
        MockRepo.return_value = mock_instance
        
        response = client.get(f"/api/catalog/products?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0


def test_upload_catalog_database_error(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("dberr")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,1200,800,10"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    with patch("backend.routers.catalog.DataRepo") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.upsert_products.side_effect = Exception("Database connection failed")
        MockRepo.return_value = mock_instance
        
        response = client.post(f"/api/catalog/upload?token={token}", files=files)
        
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


def test_upload_catalog_negative_stock(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    
    client = make_test_client()
    email = unique_email("negstock")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]
    
    csv_content = "sku,title,currency,current_price,cost,stock\nLAPTOP001,Test Laptop,USD,1200,800,-5"
    files = {"file": ("test.csv", create_csv_file(csv_content), "text/csv")}
    
    response = client.post(f"/api/catalog/upload?token={token}", files=files)
    
    assert response.status_code == 400
    assert "Stock must be non-negative" in response.json()["detail"]
