# scripts/test_apply_proposal_cli.py
from __future__ import annotations

import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid
import asyncio
import threading

from core.bus import bus as _bus
from core.protocol import Topic


def _utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    app_db = (root / "app" / "data.db").as_posix()
    market_db = (root / "market.db").as_posix()

    # Find oldest pending proposal (no action row)
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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS proposal_actions (
          id TEXT PRIMARY KEY,
          proposal_id TEXT,
          action TEXT,
          actor TEXT,
          ts TEXT
        )
        """
    )
    conn.commit()

    cur.execute(
        "SELECT id, sku, proposed_price FROM price_proposals ORDER BY ts ASC"
    )
    proposals = cur.fetchall()
    pending = None
    for pid, sku, pprice in proposals:
        cur.execute(
            "SELECT 1 FROM proposal_actions WHERE proposal_id=? LIMIT 1",
            (pid,),
        )
        if not cur.fetchone():
            pending = (pid, sku, pprice)
            break

    if not pending:
        print("NO_PENDING_PROPOSAL")
        return 2

    pid, sku, proposed_price = pending
    print(f"ACCEPT proposal_id={pid} sku={sku} proposed_price={proposed_price}")

    # Insert action row
    cur.execute(
        "INSERT INTO proposal_actions (id, proposal_id, action, actor, ts) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), pid, "ACCEPTED", "cli", _utc_now_iso()),
    )
    conn.commit()

    # Upsert into market.db.pricing_list
    mconn = sqlite3.connect(market_db)
    mcur = mconn.cursor()
    mcur.execute(
        "CREATE TABLE IF NOT EXISTS pricing_list (\n"
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "  product_name TEXT NOT NULL,\n"
        "  optimized_price REAL NOT NULL,\n"
        "  last_update TEXT DEFAULT CURRENT_TIMESTAMP,\n"
        "  reason TEXT\n"
        ")"
    )
    mcur.execute(
        "SELECT product_name FROM pricing_list WHERE product_name=?",
        (sku,),
    )
    exists = mcur.fetchone() is not None
    if exists:
        mcur.execute(
            "UPDATE pricing_list SET optimized_price=?, last_update=CURRENT_TIMESTAMP, reason=? WHERE product_name=?",
            (float(proposed_price), "accepted_via_cli", sku),
        )
    else:
        mcur.execute(
            "INSERT INTO pricing_list (product_name, optimized_price, last_update, reason) VALUES (?,?,CURRENT_TIMESTAMP,?)",
            (sku, float(proposed_price), "accepted_via_cli"),
        )
    mconn.commit()

    # Publish PRICE_UPDATE event
    payload = {
        "sku": sku,
        "new_price": float(proposed_price),
        "actor": "cli",
        "proposal_id": pid,
    }

    async def _pub():
        try:
            await _bus.publish(Topic.PRICE_UPDATE.value, payload)
        except Exception as e:
            print(f"WARN: publish failed: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_pub())
    except RuntimeError:
        threading.Thread(target=lambda: asyncio.run(_pub()), daemon=True).start()

    # Verify action inserted
    cur.execute(
        "SELECT action FROM proposal_actions WHERE proposal_id=? ORDER BY ts DESC LIMIT 1",
        (pid,),
    )
    act = cur.fetchone()

    # Verify market pricing_list updated
    mcur.execute(
        "SELECT optimized_price FROM pricing_list WHERE product_name=?",
        (sku,),
    )
    row = mcur.fetchone()

    ok = act and act[0] == "ACCEPTED" and row and abs(float(row[0]) - float(proposed_price)) < 1e-9

    try:
        conn.close()
    except Exception:
        pass
    try:
        mconn.close()
    except Exception:
        pass

    if ok:
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


