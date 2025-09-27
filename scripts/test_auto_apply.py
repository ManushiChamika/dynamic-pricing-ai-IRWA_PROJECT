from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any

# Ensure repo root on sys.path for module imports
from pathlib import Path as _Path0
import sys as _Sys0
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _Sys0.path:
    _Sys0.path.insert(0, str(_root0))

from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.events_models import PriceProposal
from core.agents.auto_applier import AutoApplier


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paths():
    root = Path(__file__).resolve().parents[1]
    return (root / "app" / "data.db").as_posix(), (root / "market.db").as_posix()


def _ensure_settings_enabled():
    app_db, _ = _paths()
    conn = sqlite3.connect(app_db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    for k, v in [("auto_apply", "true"), ("min_margin", "0.12"), ("max_delta", "0.10")]:
        # SQLite upsert for defaults
        cur.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, v),
        )
    conn.commit()
    conn.close()


def _insert_proposal_row(sku: str, current_price: float, proposed_price: float, margin: float) -> str:
    app_db, _ = _paths()
    conn = sqlite3.connect(app_db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS price_proposals (
          id TEXT PRIMARY KEY,
          sku TEXT,
          proposed_price REAL,
          current_price REAL,
          margin REAL,
          algorithm TEXT,
          ts TEXT
        )
        """
    )
    pid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO price_proposals (id, sku, proposed_price, current_price, margin, algorithm, ts) VALUES (?,?,?,?,?,?,?)",
        (pid, sku, proposed_price, current_price, margin, "test", _utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return pid


async def main() -> int:
    app_db, market_db = _paths()
    _ensure_settings_enabled()
    # Insert a passing proposal row
    pid = _insert_proposal_row("SKU-123", current_price=100.0, proposed_price=101.0, margin=0.20)

    # Start AutoApplier
    aa = AutoApplier()
    await aa.start()

    # Capture price.update events
    events: List[Dict[str, Any]] = []

    def _on_update(msg):
        events.append(msg if isinstance(msg, dict) else {})

    bus = get_bus()
    bus.subscribe(Topic.PRICE_UPDATE.value, _on_update)

    # Publish the same PriceProposal concurrently multiple times
    pp = PriceProposal(
        sku="SKU-123",
        proposed_price=101.0,
        current_price=100.0,
        margin=0.20,
        algorithm="test",
    )
    await asyncio.gather(*[bus.publish(Topic.PRICE_PROPOSAL.value, pp) for _ in range(5)])

    # Wait for auto-apply to persist
    for _ in range(48):  # up to ~12s
        ok_decision = False
        ok_price = False
        ok_event = len(events) > 0

        # Check decision_log for AUTO_APPLIED by governance
        conn = sqlite3.connect(app_db)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_log (
              id TEXT PRIMARY KEY,
              proposal_id TEXT,
              sku TEXT NOT NULL,
              old_price REAL,
              new_price REAL NOT NULL,
              margin REAL,
              algorithm TEXT,
              decision TEXT NOT NULL,
              actor TEXT NOT NULL,
              ts TEXT NOT NULL
            )
            """
        )
        cur.execute(
            "SELECT COUNT(*) FROM decision_log WHERE sku=? AND decision='AUTO_APPLIED' AND actor='governance'",
            ("SKU-123",),
        )
        cnt = int(cur.fetchone()[0])
        ok_decision = cnt >= 1
        conn.close()

        # Check pricing_list updated
        conn2 = sqlite3.connect(market_db)
        cur2 = conn2.cursor()
        cur2.execute(
            "CREATE TABLE IF NOT EXISTS pricing_list (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, optimized_price REAL NOT NULL, last_update TEXT DEFAULT CURRENT_TIMESTAMP, reason TEXT)"
        )
        cur2.execute("SELECT optimized_price FROM pricing_list WHERE product_name=?", ("SKU-123",))
        r2 = cur2.fetchone()
        ok_price = bool(r2 and abs(float(r2[0]) - 101.0) < 1e-9)
        conn2.close()

        if ok_decision and ok_price and ok_event:
            print("PASS")
            await aa.stop()
            return 0
        await asyncio.sleep(0.25)

    print("FAIL")
    await aa.stop()
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
