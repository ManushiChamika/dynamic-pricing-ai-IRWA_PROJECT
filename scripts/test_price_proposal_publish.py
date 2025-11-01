from __future__ import annotations

import asyncio
from typing import List

from core.agents.data_collector.repo import DataRepo
from core.agents.alert_service.repo import Repo as AlertRepo
from core.agents.alert_service.engine import AlertEngine
from core.agents.data_collector import mcp_server as svc
import asyncio
from core.agents.price_optimizer.agent import PricingOptimizerAgent
import sqlite3
from datetime import datetime


async def main() -> int:
    # Ensure data repo and tables exist
    r = DataRepo()
    await r.init()

    # Import product so product_catalog has SKU-123
    imp = await svc.import_product_catalog([
        {
            "sku": "SKU-123",
            "title": "Demo",
            "currency": "USD",
            "current_price": 100.0,
            "cost": 90.0,
            "stock": 10,
        }
    ])
    print("import_product_catalog:", imp)

    # Seed app/data.db with fresh competitor records for SKU-123 so optimizer can run
    try:
        conn = sqlite3.connect("app/data.db")
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, price REAL NOT NULL, update_time TEXT DEFAULT CURRENT_TIMESTAMP, owner_id INTEGER NOT NULL)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS pricing_list (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, optimized_price REAL NOT NULL, last_update TEXT DEFAULT CURRENT_TIMESTAMP, reason TEXT, owner_id INTEGER NOT NULL)"
        )
        now = datetime.now().isoformat()
        cur.execute("DELETE FROM market_data WHERE product_name=?", ("SKU-123",))
        for p in (98.0, 100.0, 102.0, 101.0, 99.0):
            cur.execute(
                "INSERT INTO market_data (product_name, price, update_time, owner_id) VALUES (?,?,?,1)",
                ("SKU-123", float(p), now),
            )
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Optionally ingest some ticks to ensure features are present
    start = await svc.start_collection("SKU-123", market="DEFAULT", connector="mock", depth=3)
    if start.get("ok"):
        job_id = start["job_id"]
        for _ in range(20):
            st = await svc.get_job_status(job_id)
            if st.get("ok") and st.get("job", {}).get("status") in {"DONE", "FAILED"}:
                break
            await asyncio.sleep(0.2)

    # Start alert engine to capture PRICE_PROPOSAL alerts
    alerts: List[str] = []

    async def ui_sink(a):
        line = f"[{a.ts:%H:%M:%S}] {a.kind} {a.sku} — {a.message} [{a.severity}]"
        print("ALERT:", line)
        alerts.append(line)

    alert_repo = AlertRepo()
    engine = AlertEngine(alert_repo)
    await engine.start()

    # Run pricing optimizer workflow (now async)
    agent = PricingOptimizerAgent()
    res = await agent.process_full_workflow("maximize profit", "SKU-123")
    print("optimizer_result:", res)

    # Allow background publish/persist time to complete
    await asyncio.sleep(1.0)

    # Fetch features to show DB connectivity is fine
    feats = await svc.fetch_market_features("SKU-123", "DEFAULT", "P7D")
    print("features:", feats)

    # Decide pass/fail
    ok_res = isinstance(res, dict) and res.get("status") == "ok"
    ok_alerts = len(alerts) >= 1  # preferably MARGIN_BREACH; accept any alert present
    ok_feats = int(feats.get("count") or 0) >= 1
    if ok_res and ok_alerts and ok_feats:
        print("PRICE_PROPOSAL SMOKE PASS")
        return 0
    print("PRICE_PROPOSAL SMOKE FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))


