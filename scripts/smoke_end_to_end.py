# scripts/smoke_end_to_end.py
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

# ---- minimal local mcp client calls (directly call your tools) ----
# We import the MCP server module and call its tool functions directly.
from core.agents.data_collector.mcp_server import (
    import_product_catalog,
    start_collection,
    get_job_status,
    fetch_market_features,
)

SKU = "SKU-123"
MARKET = "DEFAULT"


async def smoke() -> int:
    # 1) Seed a tiny product catalog
    print("import_product_catalog:", end=" ")
    res = await import_product_catalog([{"sku": SKU, "market": MARKET, "name": "Demo"}])
    print(res)
    if not res.get("ok"):
        print("FAIL: import_product_catalog returned error")
        return 1

    # 2) Start a background data collection job
    job = await start_collection(SKU, MARKET, connector="mock", depth=5)
    if not job.get("ok"):
        print("FAIL: start_collection returned error:", job)
        return 1
    job_id = job["job_id"]
    print("job_id:", job_id)

    # 3) Poll job until FINISHED or FAILED (max ~15s)
    final_status = None
    for _ in range(60):
        js = await get_job_status(job_id)
        print("job_status:", js)
        if not js.get("ok"):
            await asyncio.sleep(0.25)
            continue
        st = js["job"]["status"]
        if st in ("FINISHED", "FAILED"):
            final_status = st
            break
        await asyncio.sleep(0.25)

    # 4) Fetch features
    #    Ask for last 7 days (P7D) which covers our new ticks.
    features = await fetch_market_features(SKU, MARKET, time_window="P7D")
    print("features:", features)

    # 5) Summarize
    print("summary:")
    print(f"  final_status: {final_status}")
    alerts_collected = 0  # if you wire alerts, update this
    print(f"  alerts_collected: {alerts_collected}")

    last_price = features.get("features", {}).get("last_price")
    count = features.get("count", 0)

    if final_status == "FINISHED" and last_price is not None and count > 0:
        print("E2E SMOKE SUCCESS")
        return 0

    print("E2E SMOKE FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(smoke()))
