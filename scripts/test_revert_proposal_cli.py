from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid
import asyncio
import threading

from core.bus import bus as _bus
from core.protocol import Topic


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    app_db = (root / "app" / "data.db").as_posix()
    market_db = (root / "app" / "data.db").as_posix()

    # Ensure tables and find an ACCEPTED proposal
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
        "SELECT p.id, p.sku, p.current_price FROM price_proposals p\n"
        "JOIN (SELECT proposal_id, MAX(ts) AS ts FROM proposal_actions GROUP BY proposal_id) a\n"
        "ON a.proposal_id = p.id\n"
        "JOIN proposal_actions pa ON pa.proposal_id=p.id AND pa.ts=a.ts\n"
        "WHERE pa.action='ACCEPTED'\n"
        "ORDER BY p.ts ASC"
    )
    row = cur.fetchone()
    if not row:
        print("NO_ACCEPTED_PROPOSAL")
        return 2

    pid, sku, prev_price = row
    prev_price = float(prev_price) if prev_price is not None else None
    if prev_price is None:
        print("FAIL: accepted proposal missing current_price")
        return 1

    print(f"REVERT proposal_id={pid} sku={sku} to prev_price={prev_price}")

    # Insert REVERTED action
    cur.execute(
        "INSERT INTO proposal_actions (id, proposal_id, action, actor, ts) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), pid, "REVERTED", "cli", _utc_now_iso()),
    )
    conn.commit()

    # Upsert app/data.db to previous price
    mconn = sqlite3.connect(market_db)
    mcur = mconn.cursor()
    mcur.execute(
        "CREATE TABLE IF NOT EXISTS pricing_list (\n"
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "  product_name TEXT NOT NULL,\n"
        "  optimized_price REAL NOT NULL,\n"
        "  last_update TEXT DEFAULT CURRENT_TIMESTAMP,\n"
        "  reason TEXT,\n"
        "  owner_id INTEGER NOT NULL\n"
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
            (prev_price, "reverted_via_cli", sku),
        )
    else:
        mcur.execute(
            "INSERT INTO pricing_list (product_name, optimized_price, last_update, reason, owner_id) VALUES (?,?,CURRENT_TIMESTAMP,?,1)",
            (sku, prev_price, "reverted_via_cli"),
        )
    mconn.commit()

    # Publish PRICE_UPDATE(action=REVERT)
    payload = {
        "sku": sku,
        "new_price": prev_price,
        "actor": "cli",
        "proposal_id": pid,
        "action": "REVERT",
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

    # Verify REVERTED action exists
    cur.execute(
        "SELECT action FROM proposal_actions WHERE proposal_id=? AND action='REVERTED' ORDER BY ts DESC LIMIT 1",
        (pid,),
    )
    act = cur.fetchone()

    # Verify pricing_list equals previous price
    mcur.execute(
        "SELECT optimized_price FROM pricing_list WHERE product_name=?",
        (sku,),
    )
    row2 = mcur.fetchone()

    ok = act and act[0] == "REVERTED" and row2 and abs(float(row2[0]) - prev_price) < 1e-9

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





