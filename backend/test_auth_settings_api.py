import json
import uuid
from typing import Dict, Any, List

from fastapi.testclient import TestClient

from backend.main import app


def make_test_client():
    import importlib
    import sys

    if "backend.main" in sys.modules:
        del sys.modules["backend.main"]
    mod = importlib.import_module("backend.main")
    return TestClient(mod.app)


def unique_email(prefix: str = "user") -> str:
    # Use example.com which is reserved but valid for testing
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_auth_gating_requires_token_on_chat_routes(monkeypatch):
    # Enable login requirement
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")

    client = make_test_client()

    # Unprotected endpoints work
    r = client.get("/api/settings")
    assert r.status_code == 200
    r = client.post("/api/register", json={"email": unique_email("needtoken"), "password": "correcthorse1"})
    # Register may return 200 or 400 for duplicate; but should not be gated by 401
    assert r.status_code in (200, 400)

    # Protected chat routes should 401 without token
    r = client.get("/api/threads")
    assert r.status_code == 401

    r = client.post("/api/threads", json={"title": "Gated"})
    assert r.status_code == 401

    r = client.post("/api/threads/1/messages", json={"user_name": "t", "content": "hi"})
    assert r.status_code == 401

    r = client.get("/api/threads/1/export")
    assert r.status_code == 401

    # /api/me is allowed by middleware but handler enforces token
    r = client.get("/api/me", params={"token": "invalid"})
    assert r.status_code == 401


def iter_sse_frames(resp):
    buf = b""
    for chunk in resp.iter_bytes():
        buf += chunk
        while b"\n\n" in buf:
            frame, buf = buf.split(b"\n\n", 1)
            yield frame.decode("utf-8", errors="ignore")


def test_auth_gating_allows_with_token(monkeypatch):
    # Enable gating and force deterministic LLM fallback path
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    client = make_test_client()

    # Register and obtain token
    email = unique_email("allow")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]

    # Create thread (token via query)
    r = client.post("/api/threads", params={"token": token}, json={"title": "Auth OK"})
    assert r.status_code == 200, r.text
    tid = r.json()["id"]

    # List threads
    r = client.get("/api/threads", params={"token": token})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Post message (non-streaming)
    payload = {"user_name": "tester", "content": "hello"}
    r = client.post(f"/api/threads/{tid}/messages", params={"token": token}, json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "assistant"

    # Streaming path also works with token
    payload = {"user_name": "tester", "content": "stream please"}
    with client.stream("POST", f"/api/threads/{tid}/messages/stream", params={"token": token}, json=payload) as resp:
        assert resp.status_code == 200
        got_done = False
        for frame in iter_sse_frames(resp):
            if "event: done" in frame:
                got_done = True
                break
        assert got_done

    # Export thread
    r = client.get(f"/api/threads/{tid}/export", params={"token": token})
    assert r.status_code == 200
    exported = r.json()
    assert "messages" in exported and isinstance(exported["messages"], list)

    # Import export into a new thread
    title = (exported.get("thread") or {}).get("title") or "Copy"
    r = client.post("/api/threads/import", params={"token": token}, json={"title": title, "messages": exported["messages"]})
    assert r.status_code == 200
    new_tid = r.json()["id"]
    assert isinstance(new_tid, int)

    # Update and delete operations
    r = client.patch(f"/api/threads/{new_tid}", params={"token": token}, json={"title": "Renamed"})
    assert r.status_code == 200
    r = client.delete(f"/api/threads/{new_tid}", params={"token": token})
    assert r.status_code == 200


def test_settings_dev_mode_defaults_toggle(monkeypatch):
    # DEV_MODE = 1 enables timestamps/metadata/thinking
    monkeypatch.setenv("DEV_MODE", "1")
    client = make_test_client()
    r = client.get("/api/settings")
    assert r.status_code == 200
    s = r.json()["settings"]
    assert s["show_model_tag"] is True
    assert s["show_timestamps"] is True
    assert s["show_metadata_panel"] is True
    assert s["show_thinking"] is True

    # DEV_MODE = 0 disables those flags (model tag remains True)
    monkeypatch.setenv("DEV_MODE", "0")
    r = client.get("/api/settings")
    assert r.status_code == 200
    s = r.json()["settings"]
    assert s["show_model_tag"] is True
    assert s["show_timestamps"] is False
    assert s["show_metadata_panel"] is False
    assert s["show_thinking"] is False


def test_register_with_weak_password(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("weak")
    r = client.post("/api/register", json={"email": email, "password": "123"})
    assert r.status_code == 400
    assert "password" in r.text.lower()


def test_register_with_invalid_email(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.post("/api/register", json={"email": "notanemail", "password": "correcthorse1"})
    assert r.status_code == 400
    assert "email" in r.text.lower()


def test_register_duplicate_email(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("duplicate")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200

    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 400
    assert "exists" in r.text.lower() or "already" in r.text.lower()


def test_login_with_wrong_password(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("wrongpw")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200

    r = client.post("/api/login", json={"email": email, "password": "wrongpassword"})
    assert r.status_code == 401
    assert "token" not in r.json()


def test_login_with_nonexistent_user(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.post("/api/login", json={"email": unique_email("ghost"), "password": "anypassword"})
    assert r.status_code == 401


def test_login_success_returns_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("login")
    password = "correcthorse1"
    r = client.post("/api/register", json={"email": email, "password": password})
    assert r.status_code == 200
    token1 = r.json()["token"]

    r = client.post("/api/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token2 = r.json()["token"]

    assert token1 != token2
    assert len(token1) > 20
    assert len(token2) > 20


def test_token_validation_with_invalid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.get("/api/threads", params={"token": "invalid_token_12345"})
    assert r.status_code == 401


def test_token_validation_with_empty_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.get("/api/threads", params={"token": ""})
    assert r.status_code == 401


def test_me_endpoint_without_login(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.get("/api/me", params={"token": "invalid"})
    assert r.status_code == 401


def test_me_endpoint_with_valid_token(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    email = unique_email("me")
    r = client.post("/api/register", json={"email": email, "password": "correcthorse1"})
    assert r.status_code == 200
    token = r.json()["token"]

    r = client.get("/api/me", params={"token": token})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["user"]["email"] == email


def test_register_missing_email_field(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.post("/api/register", json={"password": "correcthorse1"})
    assert r.status_code == 422


def test_register_missing_password_field(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.post("/api/register", json={"email": unique_email("nopw")})
    assert r.status_code == 422


def test_login_missing_fields(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "1")
    client = make_test_client()

    r = client.post("/api/login", json={"email": unique_email("login")})
    assert r.status_code == 422

    r = client.post("/api/login", json={"password": "correcthorse1"})
    assert r.status_code == 422


def test_auth_isolation_between_users(monkeypatch):
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

    r = client.post("/api/threads", params={"token": token1}, json={"title": "User1 Thread"})
    assert r.status_code == 200
    tid1 = r.json()["id"]

    r = client.post(f"/api/threads/{tid1}/messages", params={"token": token1}, json={"user_name": "user1", "content": "test message"})
    assert r.status_code == 200

    r = client.get("/api/threads", params={"token": token1})
    assert r.status_code == 200
    user1_threads = r.json()
    assert any(t["id"] == tid1 for t in user1_threads)

    r = client.get("/api/threads", params={"token": token2})
    assert r.status_code == 200
    user2_threads = r.json()
    assert not any(t["id"] == tid1 for t in user2_threads)


def test_settings_without_auth_returns_defaults(monkeypatch):
    monkeypatch.setenv("UI_REQUIRE_LOGIN", "0")
    client = make_test_client()

    r = client.get("/api/settings")
    assert r.status_code == 200
    data = r.json()
    assert "settings" in data
    assert isinstance(data["settings"], dict)
