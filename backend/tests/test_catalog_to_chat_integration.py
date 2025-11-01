import os
import io
import tempfile
import uuid
import json
from typing import Generator, Dict, Any
from pathlib import Path
from fastapi.testclient import TestClient


def make_test_client() -> TestClient:
    import importlib
    import sys
    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "u") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def _tmp_db() -> str:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return db_path


def iter_sse_lines(resp) -> Generator[str, None, None]:
    buffer = b""
    for chunk in resp.iter_bytes():
        buffer += chunk
        while b"\n\n" in buffer:
            frame, buffer = buffer.split(b"\n\n", 1)
            yield frame.decode("utf-8", errors="ignore")


def test_catalog_upload_then_chat_lists_inventory(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    db_path = _tmp_db()
    monkeypatch.setenv("DATA_DB", db_path)

    from core.agents.user_interact import tools as tools_mod
    monkeypatch.setattr(tools_mod, "get_db_paths", lambda: {"app": Path(db_path), "market": Path(db_path)}, raising=True)

    client = make_test_client()

    email = unique_email("inv")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    csv_content = """sku,title,currency,current_price,cost,stock
LAPTOP001,Dell XPS 15,USD,1200,900,10
LAPTOP002,HP Pavilion,USD,800,600,15"""
    files = {"file": ("catalog.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rows_processed"] == 2

    r = client.get("/api/catalog/products", params={"token": token})
    assert r.status_code == 200
    assert r.json()["count"] == 2

    r = client.post("/api/threads", params={"token": token}, json={"title": "Inventory Check"})
    assert r.status_code == 200
    tid = r.json()["id"]

    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent as UIA

    def fake_stream_response(self, message):
        from core.agents.user_interact import tools as tm
        res = tm.list_inventory_items()
        if isinstance(res, dict) and res.get("items"):
            skus = [str(it.get("sku")) for it in res["items"] if it.get("sku")]
            yield "SKUs: " + ",".join(skus)
        else:
            yield (res.get("message") if isinstance(res, dict) else str(res))

    monkeypatch.setattr(UIA, "stream_response", fake_stream_response, raising=True)

    payload = {"user_name": "tester", "content": "what do we have?"}
    r = client.post(f"/api/threads/{tid}/messages", params={"token": token}, json=payload)
    assert r.status_code == 200, r.text
    msg = r.json()
    assert msg["role"] == "assistant"
    assert "LAPTOP001" in msg["content"]
    assert "LAPTOP002" in msg["content"]

    try:
        os.remove(db_path)
    except Exception:
        pass


def test_catalog_upload_then_stream_lists_inventory(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    db_path = _tmp_db()
    monkeypatch.setenv("DATA_DB", db_path)

    from core.agents.user_interact import tools as tools_mod
    monkeypatch.setattr(tools_mod, "get_db_paths", lambda: {"app": Path(db_path), "market": Path(db_path)}, raising=True)

    client = make_test_client()

    email = unique_email("inv")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    csv_content = """sku,title,currency,current_price,cost,stock
LAPTOP001,Dell XPS 15,USD,1200,900,10
LAPTOP002,HP Pavilion,USD,800,600,15"""
    files = {"file": ("catalog.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    r = client.post("/api/catalog/upload", params={"token": token}, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rows_processed"] == 2

    r = client.get("/api/catalog/products", params={"token": token})
    assert r.status_code == 200
    assert r.json()["count"] == 2

    r = client.post("/api/threads", params={"token": token}, json={"title": "Inventory Stream"})
    assert r.status_code == 200
    tid = r.json()["id"]

    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent as UIA

    def fake_stream_response_stream(self, message):
        from core.agents.user_interact import tools as tm
        res = tm.list_inventory_items()
        if isinstance(res, dict) and res.get("items"):
            skus = [str(it.get("sku")) for it in res["items"] if it.get("sku")]
            yield {"type": "delta", "text": "SKUs: " + ",".join(skus)}
        else:
            msg = res.get("message") if isinstance(res, dict) else str(res)
            yield {"type": "delta", "text": msg}

    monkeypatch.setattr(UIA, "stream_response", fake_stream_response_stream, raising=True)

    payload = {"user_name": "tester", "content": "show my items"}
    with client.stream("POST", f"/api/threads/{tid}/messages/stream", params={"token": token}, json=payload) as resp:
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/event-stream")

        final_payload: Dict[str, Any] | None = None
        got_done = False
        for raw in iter_sse_lines(resp):
            if not raw:
                continue
            lines = [ln for ln in raw.split("\n") if ln]
            ev = None
            data_line = None
            for ln in lines:
                if ln.startswith("event:"):
                    ev = ln.split(":", 1)[1].strip()
                if ln.startswith("data:"):
                    data_line = ln.split(":", 1)[1].strip()
            if ev == "message" and data_line:
                try:
                    obj = json.loads(data_line)
                    if isinstance(obj, dict) and obj.get("content") is not None:
                        final_payload = obj
                except Exception:
                    pass
            elif ev == "done":
                got_done = True
                break

        assert got_done
        assert isinstance(final_payload, dict)
        assert "LAPTOP001" in final_payload["content"]
        assert "LAPTOP002" in final_payload["content"]

    try:
        os.remove(db_path)
    except Exception:
        pass
