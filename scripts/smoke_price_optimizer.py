# scripts/smoke_price_optimizer.py
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Ensure repo root on sys.path for module imports
from pathlib import Path as _Path0
import sys as _sys0
_root0 = _Path0(__file__).resolve().parents[1]
if str(_root0) not in _sys0.path:
    _sys0.path.insert(0, str(_root0))

from core.agents.pricing_optimizer import PricingOptimizerAgent
from core.agents.agent_sdk.bus_factory import get_bus
from core.agents.agent_sdk.protocol import Topic


SKU = "TEST-SKU"


def ensure_market_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path.as_posix(), check_same_thread=False)
    cur = conn.cursor()
    # Minimal schemas expected by the optimizer
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS market_data (
          product_name TEXT,
          price REAL,
          features TEXT,
          update_time TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pricing_list (
          product_name TEXT PRIMARY KEY,
          optimized_price REAL,
          last_update TEXT,
          reason TEXT
        )
        """
    )
    # Seed a few recent competitor prices for the target SKU
    cur.execute("DELETE FROM market_data WHERE product_name=?", (SKU,))
    now = datetime.utcnow()
    rows = [
        (SKU, 100.0, '{"brand":"Demo"}', (now - timedelta(minutes=5)).isoformat()),
        (SKU, 102.0, '{"brand":"Demo"}', (now - timedelta(minutes=4)).isoformat()),
        (SKU, 98.0,  '{"brand":"Demo"}', (now - timedelta(minutes=3)).isoformat()),
    ]
    cur.executemany(
        "INSERT INTO market_data (product_name, price, features, update_time) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


def run_smoke() -> int:
    root = Path(__file__).resolve().parents[1]
    market_db = root / "market.db"  # use root-level DB to avoid creating ./data

    ensure_market_db(market_db)

    # Subscribe to price.update events
    events: List[Dict[str, Any]] = []

    def _on_update(msg):
        # msg is a dict payload from the optimizer
        events.append(msg)
        print("BUS price.update:", msg)

    bus = get_bus()
    bus.subscribe(Topic.PRICE_UPDATE.value, _on_update)

    # Run optimizer end-to-end
    agent = PricingOptimizerAgent()
    res = agent.process_full_workflow("maximize profit", SKU, db_path=market_db.as_posix())
    print("optimizer_result:", res)

    if not isinstance(res, dict) or res.get("status") != "success":
        print("FAIL: optimizer returned error:", res)
        return 1

    # Verify pricing_list updated
    conn = sqlite3.connect(market_db.as_posix(), check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "SELECT optimized_price, last_update, reason FROM pricing_list WHERE product_name=?",
        (SKU,),
    )
    row = cur.fetchone()
    conn.close()
    if not row or row[0] is None:
        print("FAIL: pricing_list not updated for", SKU)
        return 1
    print("pricing_list:", {"optimized_price": row[0], "last_update": row[1], "reason": row[2]})

    # Verify decision_log entry in app/data.db
    app_db = root / "app" / "data.db"
    conn2 = sqlite3.connect(app_db.as_posix(), check_same_thread=False)
    cur2 = conn2.cursor()
    try:
        cur2.execute(
            "SELECT sku, decision, actor, new_price FROM decision_log WHERE sku=? ORDER BY ts DESC LIMIT 1",
            (SKU,),
        )
        drow = cur2.fetchone()
    except Exception as e:
        print("FAIL: querying decision_log:", e)
        conn2.close()
        return 1
    conn2.close()
    if not drow:
        print("FAIL: no decision_log entry for", SKU)
        return 1
    print("decision_log:", {"sku": drow[0], "decision": drow[1], "actor": drow[2], "new_price": drow[3]})

    # Verify at least one price.update event captured
    if not events:
        print("FAIL: no price.update event captured")
        return 1

    print("SMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_smoke())
