from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[2]
_JOURNAL_DIR = _ROOT / "data"
_JOURNAL_FILE = _JOURNAL_DIR / "events.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_event(topic: str, payload: Mapping[str, Any]) -> None:
    try:
        _JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": _utc_now_iso(),
            "topic": topic,
            "payload": dict(payload),
        }
        with _JOURNAL_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        # best effort
        pass
