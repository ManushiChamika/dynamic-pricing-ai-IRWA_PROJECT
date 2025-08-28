from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict

from mcp.server.fastmcp import FastMCP

from .repo import DataRepo
from .collector import DataCollector

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
) -> Dict:
    await _repo.init()
    since_iso = _since_iso_from_window(time_window)
    return await _repo.features_for(sku, market, since_iso)


@mcp.tool()
async def ingest_tick(d: dict) -> Dict:
    await _repo.init()
    await _collector.ingest_tick(d)
    return {"ok": True}


async def main():
    await _repo.init()
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())


