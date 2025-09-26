# scripts/test_data_collector_tools.py
from __future__ import annotations

import asyncio
from typing import Any, Dict

# Run directly against the MCP server module-level tools
from core.agents.data_collector import mcp_server as srv


async def main() -> None:
    # 1) Import product catalog (upsert)
    rows = [
        {
            "sku": "SKU-123",
            "title": "Demo",
            "currency": "USD",
            "current_price": 100.0,
            "cost": 80.0,
            "stock": 10,
        }
    ]
    res = await srv.import_product_catalog(rows)
    print("import_product_catalog:", res)

    # 2) Start collection job
    start = await srv.start_collection("SKU-123", market="DEFAULT", connector="mock", depth=3)
    if not start.get("ok"):
        print("start_collection error:", start)
        return
    job_id = start["job_id"]
    print("job_id:", job_id)

    # 3) Poll job status
    for _ in range(40):  # up to ~10s at 0.25s interval
        status = await srv.get_job_status(job_id)
        print("job_status:", status)
        if status.get("ok") and status.get("job", {}).get("status") in {"DONE", "FAILED"}:
            break
        await asyncio.sleep(0.25)

    # 4) Fetch features
    feats = await srv.fetch_market_features("SKU-123", "DEFAULT", "P7D")
    print("features:", feats)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

