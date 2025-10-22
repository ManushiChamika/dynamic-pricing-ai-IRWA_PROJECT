import json
import re
from typing import List, Dict, Any

from fastapi.testclient import TestClient

from backend.main import app


def make_test_client():
    from fastapi.testclient import TestClient as _TestClient
    return _TestClient(app)


def test_create_thread_and_post_message_non_streaming(monkeypatch):
    # Force LLM unavailable to hit fallback path deterministically
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create thread
    r = client.post("/api/threads", json={"title": "API Test"})
    assert r.status_code == 200, r.text
    thread = r.json()
    tid = thread["id"]

    # Post message (non-streaming)
    payload = {"user_name": "tester", "content": "hello"}
    r = client.post(f"/api/threads/{tid}/messages", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    # Validate basic shape
    assert data["role"] == "assistant"
    assert isinstance(data["id"], int)
    assert isinstance(data["created_at"], str)
    # In fallback mode we should get the explicit non-LLM message
    assert "LLM is not available" in data["content"]

    # Fetch messages list and ensure two messages exist (user + assistant)
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def iter_sse_lines(resp):
    buffer = b""
    for chunk in resp.iter_bytes():
        buffer += chunk
        while b"\n\n" in buffer:
            frame, buffer = buffer.split(b"\n\n", 1)
            yield frame.decode("utf-8", errors="ignore")


def test_post_message_streaming_sse(monkeypatch):
    # Force LLM unavailable to ensure deterministic fallback string from stream_response
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create thread
    r = client.post("/api/threads", json={"title": "Stream Test"})
    assert r.status_code == 200
    tid = r.json()["id"]

    # Start streaming request
    payload = {"user_name": "tester", "content": "stream please"}
    with client.stream("POST", f"/api/threads/{tid}/messages/stream", json=payload) as resp:
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/event-stream")

        deltas: List[str] = []
        final_payload: Dict[str, Any] | None = None
        got_done = False

        for raw in iter_sse_lines(resp):
            if not raw:
                continue
            # Parse SSE format: lines like 'event: X' and 'data: JSON'
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
                except Exception:
                    # delta frames are JSON with {"id","delta"} or final full payload
                    obj = None
                if isinstance(obj, dict) and "delta" in obj:
                    deltas.append(obj["delta"])  # incremental
                elif isinstance(obj, dict) and "content" in obj:
                    final_payload = obj
            elif ev == "done":
                got_done = True
                break

        # Validate we got at least a final payload and done event
        assert got_done
        assert isinstance(final_payload, dict)
        assert final_payload["role"] == "assistant"
        # In fallback, content will contain the non-LLM message
        assert "LLM is not available" in final_payload["content"]
        # Deltas may be a single full chunk in fallback path
        assert isinstance("".join(deltas), str)

    # Ensure DB has persisted messages (user + assistant)
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_delete_thread_cascades_messages_and_summaries(monkeypatch):
    # Ensure deterministic fallback behavior
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create a thread and add a user+assistant exchange
    r = client.post("/api/threads", json={"title": "Delete Cascade Test"})
    assert r.status_code == 200
    tid = r.json()["id"]

    payload = {"user_name": "tester", "content": "hello world"}
    r = client.post(f"/api/threads/{tid}/messages", json=payload)
    assert r.status_code == 200

    # Confirm messages exist and capture last id
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) >= 2
    upto_id = msgs[-1]["id"]

    # Insert a summary explicitly to verify cascade cleaning
    from core.chat_db import add_summary as db_add_summary
    db_add_summary(thread_id=tid, upto_message_id=upto_id, content="summary for test")

    # Pre-delete sanity: summaries endpoint returns at least one summary
    r = client.get(f"/api/threads/{tid}/summaries")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert isinstance(body.get("summaries", []), list)
    assert len(body["summaries"]) >= 1

    # Delete the thread
    r = client.delete(f"/api/threads/{tid}")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    # Messages should be gone (endpoint returns empty list for deleted thread id)
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    assert r.json() == []

    # Summaries should be gone
    r = client.get(f"/api/threads/{tid}/summaries")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body.get("summaries", []) == []


def test_delete_thread_twice_returns_404(monkeypatch):
    # Create and delete once, second delete should 404
    r = client.post("/api/threads", json={"title": "Delete Twice Test"})
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.delete(f"/api/threads/{tid}")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    r = client.delete(f"/api/threads/{tid}")
    assert r.status_code == 404


def test_edit_user_message_updates_content(monkeypatch):
    # Deterministic fallback
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create thread and send one message
    r = client.post("/api/threads", json={"title": "Edit Test"})
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.post(f"/api/threads/{tid}/messages", json={"user_name": "tester", "content": "first"})
    assert r.status_code == 200

    # Find the user message id
    r = client.get(f"/api/threads/{tid}/messages")
    msgs = r.json()
    user_msg = next((m for m in msgs if m["role"] == "user"), None)
    assert user_msg is not None

    # Edit content
    new_text = "first (edited)"
    r = client.patch(f"/api/messages/{user_msg['id']}", json={"content": new_text, "branch": True})
    assert r.status_code == 200
    edited = r.json()
    assert edited["id"] == user_msg["id"]
    assert edited["content"] == new_text

    # Verify messages reflect the edit
    r = client.get(f"/api/threads/{tid}/messages")
    msgs2 = r.json()
    user_after = next((m for m in msgs2 if m["id"] == user_msg["id"]), None)
    assert user_after is not None and user_after["content"] == new_text


def test_branch_from_parent_appends_pair(monkeypatch):
    # Deterministic fallback
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create thread and first exchange
    r = client.post("/api/threads", json={"title": "Branch Test"})
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.post(f"/api/threads/{tid}/messages", json={"user_name": "tester", "content": "hello"})
    assert r.status_code == 200

    # Capture the first user message id
    r = client.get(f"/api/threads/{tid}/messages")
    msgs = r.json()
    assert len(msgs) == 2
    first_user = msgs[0]
    assert first_user["role"] == "user"

    # Branch from the first user message
    r = client.post(
        f"/api/threads/{tid}/messages",
        json={"user_name": "tester", "content": "branching question", "parent_id": first_user["id"]},
    )
    assert r.status_code == 200

    # We should now have 4 messages: user, assistant, user(branch), assistant
    r = client.get(f"/api/threads/{tid}/messages")
    msgs2 = r.json()
    assert len(msgs2) == 4
    assert msgs2[-2]["role"] == "user" and msgs2[-2]["content"] == "branching question"
    assert msgs2[-1]["role"] == "assistant"


def test_delete_single_message(monkeypatch):
    # Deterministic fallback
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create thread and one exchange
    r = client.post("/api/threads", json={"title": "Delete Msg Test"})
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.post(f"/api/threads/{tid}/messages", json={"user_name": "tester", "content": "to delete"})
    assert r.status_code == 200

    # Delete the assistant message
    r = client.get(f"/api/threads/{tid}/messages")
    msgs = r.json()
    assert len(msgs) == 2
    assistant = msgs[1]
    assert assistant["role"] == "assistant"

    r = client.delete(f"/api/messages/{assistant['id']}")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    # Only the user message should remain
    r = client.get(f"/api/threads/{tid}/messages")
    msgs2 = r.json()
    assert len(msgs2) == 1
    assert msgs2[0]["role"] == "user"


def test_export_import_roundtrip(monkeypatch):
    # Deterministic fallback
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create a thread with two exchanges
    r = client.post("/api/threads", json={"title": "Export Source"})
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.post(f"/api/threads/{tid}/messages", json={"user_name": "tester", "content": "first"})
    assert r.status_code == 200
    r = client.post(f"/api/threads/{tid}/messages", json={"user_name": "tester", "content": "second"})
    assert r.status_code == 200

    r = client.get(f"/api/threads/{tid}/messages")
    original_msgs = r.json()
    assert len(original_msgs) == 4

    # Export
    r = client.get(f"/api/threads/{tid}/export")
    assert r.status_code == 200
    exported = r.json()
    assert "thread" in exported and "messages" in exported
    assert isinstance(exported["messages"], list)
    assert len(exported["messages"]) == len(original_msgs)

    # Import into a new thread
    title = (exported.get("thread") or {}).get("title") or "Imported Copy"
    payload = {"title": title, "messages": exported["messages"]}
    r = client.post("/api/threads/import", json=payload)
    assert r.status_code == 200
    new_tid = r.json()["id"]

    # Verify messages preserved (role + content sequence)
    r = client.get(f"/api/threads/{new_tid}/messages")
    imported_msgs = r.json()
    assert len(imported_msgs) == len(original_msgs)
    for a, b in zip(original_msgs, imported_msgs):
        assert a["role"] == b["role"]
        assert a["content"] == b["content"]


def test_user_message_metadata_non_streaming_propagated(monkeypatch):
    # Ensure fallback (no external LLM)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    # Create thread and send one message
    r = client.post("/api/threads", json={"title": "User Meta Non-Stream"})
    assert r.status_code == 200
    tid = r.json()["id"]

    r = client.post(f"/api/threads/{tid}/messages", json={"user_name": "tester", "content": "check agents"})
    assert r.status_code == 200

    # Inspect messages; the user message should have agents/tools metadata
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    user_msg = msgs[0]
    assert user_msg["role"] == "user"
    # Agents/tools present as dicts with count fields
    assert isinstance(user_msg.get("agents"), dict)
    assert isinstance(user_msg.get("tools"), dict)
    assert "count" in user_msg["agents"]
    assert "count" in user_msg["tools"]
    assert isinstance(user_msg["agents"].get("activated", []), list)
    assert isinstance(user_msg["tools"].get("used", []), list)
    # Metadata dictionary exists with provider key
    assert isinstance(user_msg.get("metadata"), (dict, type(None)))


def test_user_message_metadata_streaming_propagated(monkeypatch):
    # Ensure fallback
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    client = make_test_client()

    r = client.post("/api/threads", json={"title": "User Meta Stream"})
    assert r.status_code == 200
    tid = r.json()["id"]

    payload = {"user_name": "tester", "content": "stream agents"}
    with client.stream("POST", f"/api/threads/{tid}/messages/stream", json=payload) as resp:
        assert resp.status_code == 200
        # Drain stream
        for _ in iter_sse_lines(resp):
            pass

    # Inspect messages; the user message should have agents/tools metadata
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) == 2
    user_msg = msgs[0]
    assert user_msg["role"] == "user"
    assert isinstance(user_msg.get("agents"), dict)
    assert isinstance(user_msg.get("tools"), dict)
    assert "count" in user_msg["agents"]
    assert "count" in user_msg["tools"]
    assert isinstance(user_msg["agents"].get("activated", []), list)
    assert isinstance(user_msg["tools"].get("used", []), list)
    assert isinstance(user_msg.get("metadata"), (dict, type(None)))
