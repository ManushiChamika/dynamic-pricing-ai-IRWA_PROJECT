from __future__ import annotations
import json
import uuid
import time
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Simple JSON-backed chat threads per user
# Files live in app/chat_threads/

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "app" / "chat_threads"
INDEX = BASE / "index.json"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ensure_dirs() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        INDEX.write_text(json.dumps({}, indent=2), encoding="utf-8")


def _read_index() -> Dict[str, Any]:
    _ensure_dirs()
    try:
        data = INDEX.read_text(encoding="utf-8")
        return json.loads(data or "{}")
    except Exception:
        return {}


def _write_index(idx: Dict[str, Any]) -> None:
    tmp = INDEX.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(idx, indent=2), encoding="utf-8")
    tmp.replace(INDEX)


def _user_key(user: Dict[str, Any]) -> str:
    email = (user.get("email") or "").strip()
    return email or "anonymous"


def list_threads(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    idx = _read_index()
    u = _user_key(user)
    threads = idx.get(u, {}).get("threads", [])
    return sorted(threads, key=lambda t: t.get("updated_at", ""), reverse=True)


def get_thread(user: Dict[str, Any], tid: str) -> Optional[Dict[str, Any]]:
    idx = _read_index()
    u = _user_key(user)
    for t in idx.get(u, {}).get("threads", []):
        if t.get("id") == tid:
            return t
    return None


def thread_exists(user: Dict[str, Any], tid: str) -> bool:
    if not tid:
        return False
    return get_thread(user, tid) is not None


def first_thread_id(user: Dict[str, Any]) -> Optional[str]:
    threads = list_threads(user)
    return threads[0]["id"] if threads else None


def _default_meta(title: Optional[str] = None) -> Dict[str, Any]:
    ts = _now()
    return {
        "title": (title or "New chat"),
        "created_at": ts,
        "updated_at": ts,
        # naming flags
        "auto_named": False,   # heuristic from first user msg
        "llm_named": False,    # renamed by LLM summary
        "user_named": False,   # explicitly renamed by user
    }


def create_thread(user: Dict[str, Any], title: Optional[str] = None) -> str:
    idx = _read_index()
    u = _user_key(user)
    tid = str(uuid.uuid4())
    meta = _default_meta(title)
    tmeta = {"id": tid, **meta}
    idx.setdefault(u, {}).setdefault("threads", []).append(tmeta)
    _write_index(idx)
    (BASE / f"{tid}.json").write_text("[]", encoding="utf-8")
    return tid


def _messages_path(tid: str) -> Path:
    return BASE / f"{tid}.json"


def load_messages(user: Dict[str, Any], tid: str) -> List[Dict[str, Any]]:
    p = _messages_path(tid)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def _first_user_message(msgs: List[Dict[str, Any]]) -> Optional[str]:
    for m in msgs:
        if m.get("role") == "user":
            c = (m.get("content") or "").strip()
            if c:
                return c
    return None


_STOPWORDS = {
    "a","an","the","and","or","but","if","to","of","for","on","in","with","about","from",
    "is","are","was","were","be","can","could","would","should","please","help","how","what",
    "show","me","my","our","your","their","do","does","did","into","by","at","as","we","i",
    "you","they","it","this","that","these","those","need","want","let","lets","let's",
}


def _simple_topic_title(text: str, max_len: int = 60) -> str:
    s = text.strip()
    s = re.sub(r"https?://\S+", "", s)
    # Prefer first sentence or line
    s = s.split("\n", 1)[0]
    s = s.split("?", 1)[0]
    s = s.split(".", 1)[0]
    # Remove leading polite/request phrases
    s = re.sub(r"^(please|can you|could you|help me|i need|i want|how to|how do i|what is|what are|show me|give me)\b[\s,:-]*",
               "", s, flags=re.IGNORECASE)
    # Tokenize and remove stopwords/punct
    words = re.findall(r"[A-Za-z0-9%\-\+]+", s)
    filtered = [w for w in words if w.lower() not in _STOPWORDS]
    if filtered:
        candidate = " ".join(filtered[:8])
    else:
        candidate = s.strip() or "New chat"
    title = candidate[:max_len].strip()
    # Title case with minimal distortion (keep acronyms)
    title = " ".join([w if w.isupper() else w.capitalize() for w in title.split()])
    return title or "New chat"


def _count_user_messages(msgs: List[Dict[str, Any]]) -> int:
    return sum(1 for m in msgs if m.get("role") == "user" and (m.get("content") or "").strip())


def append_message(user: Dict[str, Any], tid: str, role: str, content: str) -> None:
    msgs = load_messages(user, tid)
    msgs.append({"role": role, "content": content, "ts": _now()})
    p = _messages_path(tid)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(msgs, indent=2), encoding="utf-8")
    tmp.replace(p)
    # Bump updated_at and auto-title on first user message
    idx = _read_index()
    u = _user_key(user)
    for t in idx.get(u, {}).get("threads", []):
        if t.get("id") == tid:
            t["updated_at"] = _now()
            if role == "user" and not t.get("user_named"):
                if not t.get("auto_named"):
                    # First user message heuristic
                    first = content.strip()
                    if not first:
                        first = _first_user_message(msgs) or ""
                    if first:
                        t["title"] = _simple_topic_title(first)
                        t["auto_named"] = True
            break
    _write_index(idx)


def rename_thread(user: Dict[str, Any], tid: str, title: str, by: str = "user") -> None:
    idx = _read_index()
    u = _user_key(user)
    for t in idx.get(u, {}).get("threads", []):
        if t.get("id") == tid:
            t["title"] = title.strip() or t.get("title") or "Untitled"
            t["updated_at"] = _now()
            if by == "user":
                t["user_named"] = True
            elif by == "llm":
                t["llm_named"] = True
            break
    _write_index(idx)


def delete_thread(user: Dict[str, Any], tid: str) -> None:
    idx = _read_index()
    u = _user_key(user)
    threads = idx.get(u, {}).get("threads", [])
    idx.setdefault(u, {})["threads"] = [t for t in threads if t.get("id") != tid]
    _write_index(idx)
    try:
        _messages_path(tid).unlink(missing_ok=True)
    except Exception:
        pass


def should_llm_rename(user: Dict[str, Any], tid: str) -> bool:
    meta = get_thread(user, tid) or {}
    if meta.get("user_named") or meta.get("llm_named"):
        return False
    msgs = load_messages(user, tid)
    return _count_user_messages(msgs) >= 4
