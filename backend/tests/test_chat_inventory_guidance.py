import os
import sqlite3
import tempfile
import uuid
import json
from pathlib import Path
from typing import Generator, List, Dict, Any

from fastapi.testclient import TestClient
import pytest


def make_test_client() -> TestClient:
    import importlib
    import sys
    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def iter_sse_lines(resp) -> Generator[str, None, None]:
    buffer = b""
    for chunk in resp.iter_bytes():
        buffer += chunk
        while b"\n\n" in buffer:
            frame, buffer = buffer.split(b"\n\n", 1)
            yield frame.decode("utf-8", errors="ignore")


def _make_empty_catalog_db() -> str:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS product_catalog (
                sku TEXT,
                title TEXT,
                currency TEXT,
                current_price REAL,
                cost REAL,
                stock INTEGER,
                updated_at TEXT,
                owner_id TEXT
            )
            """
        )
        conn.commit()
    return db_path


def test_post_message_nonstream_guidance_no_owner(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "0")

    client = make_test_client()

    r = client.post("/api/threads", json={"title": "Inv Guidance"})
    assert r.status_code == 200
    tid = r.json()["id"]

    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent as UIA

    def fake_stream_response(self, message):
        from core.agents.user_interact import tools as tools_mod
        res = tools_mod.list_inventory_items()
        msg = res.get("message") if isinstance(res, dict) else str(res)
        yield msg

    monkeypatch.setattr(UIA, "stream_response", fake_stream_response, raising=True)

    payload = {"user_name": "tester", "content": "what do we have?"}
    r = client.post(f"/api/threads/{tid}/messages", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "assistant"
    assert "No inventory found for your account" in body["content"]


def test_post_message_stream_guidance_empty_owner_catalog(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")

    client = make_test_client()

    email = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    db_path = _make_empty_catalog_db()

    from core.agents.user_interact import tools as tools_mod
    monkeypatch.setattr(tools_mod, "get_db_paths", lambda: {"app": Path(db_path), "market": Path(db_path)}, raising=True)

    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent as UIA

    def fake_stream_response_stream(self, message):
        from core.agents.user_interact import tools as tools_mod
        res = tools_mod.list_inventory_items()
        msg = res.get("message") if isinstance(res, dict) else str(res)
        yield {"type": "delta", "text": msg}

    monkeypatch.setattr(UIA, "stream_response", fake_stream_response_stream, raising=True)

    r = client.post("/api/threads", params={"token": token}, json={"title": "Inv Stream"})
    assert r.status_code == 200
    tid = r.json()["id"]

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
        assert "Your inventory is currently empty" in final_payload["content"]

    try:
        os.remove(db_path)
    except Exception:
        pass
