from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP

from .repo import DataRepo
from .collector import DataCollector
from .connectors.mock import mock_ticks

mcp = FastMCP("data-collector-service")
_repo = DataRepo()
_collector = DataCollector(_repo)


def _since_iso_from_window(window: str) -> str:
    """
    Parse very small subset like 'P7D', 'P1D'. Defaults to 7 days.
    """
    try:
        s = window.strip().upper()
        days = int(s.replace("P", "").replace("D", "") or "7")
    except Exception:
        days = 7
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


@mcp.tool()
async def fetch_market_features(
    sku: str, market: str = "DEFAULT", time_window: str = "P7D", freshness_sla_minutes: int = 60
) -> dict:
    await _repo.init()
    since_iso = _since_iso_from_window(time_window)
    return await _repo.features_for(sku, market, since_iso)


@mcp.tool()
async def ingest_tick(d: dict) -> dict:
    await _repo.init()
    await _collector.ingest_tick(d)
    return {"ok": True}


@mcp.tool()
async def import_product_catalog(rows: list) -> dict:
    """Import or update product rows into the product catalog.

    Returns a dict with count of processed rows.
    """
    await _repo.init()
    if not isinstance(rows, list):
        return {"ok": False, "error": "invalid_rows_type"}
    # Only accept dict items with a sku
    filtered: List[Dict[str, Any]] = [r for r in rows if isinstance(r, dict) and r.get("sku")]
    try:
        count = await _repo.upsert_products(filtered)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "count": count}


async def _run_job(job_id: str, sku: str, market: str, connector: str, depth: int) -> None:
    """Background job runner: marks RUNNING, ingests, then DONE/FAILED."""
    print(f"[mcp_job] start job id={job_id} sku={sku} connector={connector} depth={depth}")
    try:
        await _repo.mark_job_running(job_id)
        if connector == "mock":
            await _collector.ingest_stream(
                mock_ticks(sku=sku, market=market, n=max(1, int(depth))),
                delay_s=0.15,
            )
        else:
            raise ValueError(f"unsupported_connector: {connector}")
        await _repo.mark_job_done(job_id)
        print(f"[mcp_job] done job id={job_id}")
    except Exception as e:
        print(f"[mcp_job] failed job id={job_id}: {e}")
        try:
            await _repo.mark_job_failed(job_id, str(e))
        except Exception as ie:
            print(f"[mcp_job] mark failed error: {ie}")


@mcp.tool()
async def start_collection(
    sku: str,
    market: str = "DEFAULT",
    connector: str = "mock",
    depth: int = 1,
) -> dict:
    """Start a background collection job for a given sku/market."""
    await _repo.init()
    try:
        depth_int = max(1, int(depth))
    except Exception:
        depth_int = 1

    # Validate connector
    if connector != "mock":
        return {"ok": False, "error": "unsupported_connector"}

    job_id = await _repo.create_job(sku, market, connector, depth_int)
    # Fire-and-forget
    asyncio.create_task(_run_job(job_id, sku, market, connector, depth_int))
    return {"ok": True, "job_id": job_id}


@mcp.tool()
async def get_job_status(job_id: str) -> dict:
    """Return current job status or job_not_found."""
    await _repo.init()
    try:
        row = await _repo.get_job(job_id)
    except Exception as e:
        return {"ok": False, "error": str(e), "job_id": job_id}
    if row:
        return {"ok": True, "job": row}
    return {"ok": False, "error": "job_not_found", "job_id": job_id}


async def main():
    await _repo.init()
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())


