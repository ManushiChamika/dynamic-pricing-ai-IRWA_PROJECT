from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from core.tool_registry import get_tool_registry


async def collect_and_optimize_prelude(row: Dict[str, Any], timeout_s: int = 60) -> Dict[str, Any]:
    registry = get_tool_registry()
    sku = str(row.get("sku") or "").strip()
    market = str(row.get("market") or "DEFAULT")
    connector = str(row.get("connector") or "mock")
    depth = int(row.get("depth") or 3)
    if not sku:
        return {"ok": False, "error": "missing sku"}

    await registry.execute_tool("upsert_product", product_data=row)

    start_res = await registry.execute_tool(
        "start_data_collection",
        sku=sku,
        market=market,
        connector=connector,
        depth=depth,
    )
    if not isinstance(start_res, dict) or not start_res.get("ok"):
        return {"ok": False, "error": start_res}

    job_id = str(start_res.get("job_id"))
    t0 = time.time()
    status: str | None = None
    while time.time() - t0 < timeout_s:
        st = await registry.execute_tool("get_job_status", job_id=job_id)
        job = st.get("job") if st.get("ok") else None
        status = (job or {}).get("status")
        if status in {"DONE", "FAILED", "CANCELLED"}:
            break
        await asyncio.sleep(0.25)

    return {"ok": True, "sku": sku, "job_id": job_id, "job_status": status or "UNKNOWN"}
