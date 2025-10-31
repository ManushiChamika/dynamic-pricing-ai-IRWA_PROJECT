from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from core.tool_registry import get_tool_registry
import logging

logger = logging.getLogger(__name__)


async def collect_and_optimize_prelude(
    row: Dict[str, Any],
    timeout_s: int = 60,
    *,
    max_retries: int = 2,
    backoff: float = 0.5,
    poll_interval: float = 0.25,
) -> Dict[str, Any]:
    registry = get_tool_registry()
    sku = str(row.get("sku") or "").strip()
    market = str(row.get("market") or "DEFAULT")
    connector = str(row.get("connector") or "mock")
    depth = int(row.get("depth") or 3)
    if not sku:
        logger.warning("collect_and_optimize_prelude: missing sku")
        return {"ok": False, "error": "missing sku"}

    for attempt in range(max_retries + 1):
        try:
            await registry.execute_tool("upsert_product", product_data=row)
            break
        except Exception as e:
            logger.warning("upsert_product attempt %d failed: %s", attempt, e)
            if attempt >= max_retries:
                return {"ok": False, "error": f"upsert_product failed: {e}"}
            await asyncio.sleep(backoff * (attempt + 1))

    start_res = None
    for attempt in range(max_retries + 1):
        try:
            start_res = await registry.execute_tool(
                "start_data_collection",
                sku=sku,
                market=market,
                connector=connector,
                depth=depth,
            )
            if isinstance(start_res, dict) and start_res.get("ok"):
                break
            raise RuntimeError(f"start_data_collection returned: {start_res}")
        except Exception as e:
            logger.warning("start_data_collection attempt %d failed: %s", attempt, e)
            if attempt >= max_retries:
                return {"ok": False, "error": f"start_data_collection failed: {e}"}
            await asyncio.sleep(backoff * (attempt + 1))

    job_id = str(start_res.get("job_id"))
    t0 = time.time()
    status: str | None = None
    while time.time() - t0 < timeout_s:
        try:
            st = await registry.execute_tool("get_job_status", job_id=job_id)
            job = st.get("job") if st.get("ok") else None
            status = (job or {}).get("status")
            if status in {"DONE", "FAILED", "CANCELLED"}:
                break
        except Exception as e:
            logger.debug("get_job_status error: %s", e)
        await asyncio.sleep(poll_interval)

    logger.info("collect_and_optimize_prelude finished: sku=%s job_id=%s status=%s", sku, job_id, status)
    return {"ok": True, "sku": sku, "job_id": job_id, "job_status": status or "UNKNOWN"}
