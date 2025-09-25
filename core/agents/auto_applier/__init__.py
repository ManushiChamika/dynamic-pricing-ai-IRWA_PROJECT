# core/agents/auto_applier/__init__.py
from __future__ import annotations

import asyncio
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Callable, List, Tuple

from core.bus import bus

# Try to import Topic from known places, fallback to simple strings
try:
    from core.protocol import Topic  # preferred in this repo
except Exception:
    try:
        from core.topics import Topic
    except Exception:
        class _T:
            PRICE_PROPOSAL = "PRICE_PROPOSAL"
            PRICE_UPDATE = "PRICE_UPDATE"
            PRICE_APPLIED = "PRICE_APPLIED"
        Topic = _T()  # type: ignore


# ---------- helpers ----------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _topic_value(t: Any, fallback: str) -> str:
    if hasattr(t, "value"):
        return getattr(t, "value")
    if isinstance(t, str):
        return t
    return fallback

def _project_roots() -> Tuple[Path, Path]:
    """
    ALWAYS use repo-root DBs:
      - <repo>/app/data.db
      - <repo>/market.db
    We are sitting at: <repo>/core/agents/auto_applier/__init__.py
    parents[3] is the repo root: [auto_applier]=0, [agents]=1, [core]=2, [repo]=3
    """
    here = Path(__file__).resolve()
    root = here.parents[3]  # <repo>
    app_db = root / "app" / "data.db"
    market_db = root / "market.db"

    # Ensure dirs exist (prevents sqlite 'unable to open database file')
    app_db.parent.mkdir(parents=True, exist_ok=True)
    market_db.parent.mkdir(parents=True, exist_ok=True)

    return app_db, market_db



def _ensure_actions(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS proposal_actions (
          id TEXT PRIMARY KEY,
          proposal_id TEXT,
          action TEXT,
          actor TEXT,
          ts TEXT
        )
    """)
    # Deduplicate concurrent inserts
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_proposal_action
        ON proposal_actions(proposal_id, action)
    """)

def _ensure_pricing(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pricing_list (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_name TEXT NOT NULL,
          optimized_price REAL NOT NULL,
          last_update TEXT DEFAULT CURRENT_TIMESTAMP,
          reason TEXT
        )
    """)

def _ensure_proposals(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_proposals (
          id TEXT PRIMARY KEY,
          sku TEXT,
          proposed_price REAL,
          current_price REAL,
          margin REAL,
          algorithm TEXT,
          ts TEXT
        )
    """)

def _find_proposal_id(conn: sqlite3.Connection, sku: str, proposed: float, current: Optional[float]) -> Optional[str]:
    """
    Match the proposal row created by the test. Use a tolerant match and
    fall back from (sku, proposed, current) -> (sku, proposed) if needed.
    """
    _ensure_proposals(conn)
    tol = 1e-6

    def _abs_diff(col: str, val: float) -> str:
        # SQLite lacks ABS(x - ?) < tol across floats precision issues sometimes;
        # This is still fine for our small values.
        return f"ABS({col} - ?) < {tol}"

    if current is not None:
        cur = conn.execute(
            f"""
            SELECT id FROM price_proposals
            WHERE sku=?
              AND {_abs_diff('proposed_price', proposed)}
              AND {_abs_diff('current_price', float(current))}
            ORDER BY ts DESC
            LIMIT 1
            """,
            (sku, proposed, float(current)),
        )
        row = cur.fetchone()
        if row:
            return row[0]

    # Fallback: match by (sku, proposed) only
    cur = conn.execute(
        f"""
        SELECT id FROM price_proposals
        WHERE sku=?
          AND {_abs_diff('proposed_price', proposed)}
        ORDER BY ts DESC
        LIMIT 1
        """,
        (sku, proposed),
    )
    row = cur.fetchone()
    return row[0] if row else None


# ---------- config and agent ----------

@dataclass
class AutoApplierConfig:
    auto_accept: bool = True

class AutoApplier:
    name = "auto_applier"

    def __init__(self, config: Optional[AutoApplierConfig] = None) -> None:
        self.config = config or AutoApplierConfig()
        self._handlers: List[Tuple[str, Callable[[Any], Any]]] = []
        self._stopped = False
        
        # Log database paths on initialization
        app_db, market_db = _project_roots()
        print(f"[AutoApplier] app_db={app_db}  market_db={market_db}", flush=True)

    async def _on_proposal(self, pp: Any) -> None:
        if self._stopped or not self.config.auto_accept:
            return

        # Extract fields (accept both objects and dicts)
        if hasattr(pp, "sku"):
            sku = getattr(pp, "sku")
            proposed = getattr(pp, "proposed_price", None)
            current = getattr(pp, "current_price", None)
            ts = getattr(pp, "ts", None) or _now_iso()
        elif isinstance(pp, dict):
            sku = pp.get("sku")
            proposed = pp.get("proposed_price")
            current = pp.get("current_price")
            ts = pp.get("ts") or _now_iso()
        else:
            return

        if sku is None or proposed is None:
            return
        try:
            new_price = float(proposed)
        except Exception:
            return

        # Update DBs (repo-root DBs; matches test script)
        app_db, market_db = _project_roots()

        # 1) Find the matching proposal row created by the test
        with sqlite3.connect(app_db.as_posix()) as conn:
            proposal_id = _find_proposal_id(conn, sku, new_price, current)

        # 2) Record AUTO_APPLIED exactly once (handles concurrent publishes)
        if proposal_id:
            with sqlite3.connect(app_db.as_posix()) as conn:
                _ensure_actions(conn)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO proposal_actions
                    (id, proposal_id, action, actor, ts)
                    VALUES (?,?,?,?,?)
                    """,
                    (str(uuid.uuid4()), proposal_id, "AUTO_APPLIED", "auto_applier", _now_iso()),
                )
                conn.commit()

        # 3) Upsert pricing_list in market.db
        with sqlite3.connect(market_db.as_posix()) as conn:
            _ensure_pricing(conn)
            cur = conn.execute("SELECT id FROM pricing_list WHERE product_name=?", (sku,))
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE pricing_list SET optimized_price=?, last_update=?, reason=? WHERE id=?",
                    (new_price, _now_iso(), "AUTO_APPLIED", row[0]),
                )
            else:
                conn.execute(
                    "INSERT INTO pricing_list (product_name, optimized_price, last_update, reason) VALUES (?,?,?,?)",
                    (sku, new_price, _now_iso(), "AUTO_APPLIED"),
                )
            conn.commit()

        # 4) Publish events (support enum.value or raw strings)
        update_topic = _topic_value(getattr(Topic, "PRICE_UPDATE", "PRICE_UPDATE"), "PRICE_UPDATE")
        applied_topic = _topic_value(getattr(Topic, "PRICE_APPLIED", "PRICE_APPLIED"), "PRICE_APPLIED")
        try:
            await bus.publish(update_topic, {"sku": sku, "price": new_price, "ts": ts})
        except Exception:
            pass
        try:
            await bus.publish(applied_topic, {"sku": sku, "new_price": new_price, "ts": ts})
        except Exception:
            pass

    async def start(self) -> None:
        self._stopped = False
        proposal_topic = _topic_value(getattr(Topic, "PRICE_PROPOSAL", "PRICE_PROPOSAL"), "PRICE_PROPOSAL")
        for t in {proposal_topic, "PRICE_PROPOSAL"}:
            bus.subscribe(t, self._on_proposal)
            self._handlers.append((t, self._on_proposal))

    async def run(self) -> bool:
        await self.start()
        await asyncio.sleep(0)
        return True

    async def stop(self) -> None:
        self._stopped = True
        if hasattr(bus, "unsubscribe"):
            for t, h in self._handlers:
                try:
                    bus.unsubscribe(t, h)
                except Exception:
                    pass
        self._handlers.clear()
