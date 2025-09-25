# core/agents/data_collector/mcp_server.py
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except Exception:  # minimal fallback shim
    class FastMCP:  # type: ignore
        def __init__(self, name: str):
            self.name = name
            self._tools = {}
        def tool(self):
            def deco(fn):
                self._tools[fn.__name__] = fn
                return fn
            return deco
        async def run(self):
            # No-op in fallback
            print(f"[FastMCP fallback] {self.name} started with tools: {list(self._tools)}")

from .repo import DataRepo
from .collector import DataCollector
from .connectors import mock_ticks, build_connector  # ← import factory

mcp = FastMCP("data-collector-service")
_repo = DataRepo()
_collector = DataCollector(_repo)


def _since_iso_from_window(window: str) -> str:
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
    await _repo.init()
    if not isinstance(rows, list):
        return {"ok": False, "error": "invalid_rows_type"}
    filtered: List[Dict[str, Any]] = [r for r in rows if isinstance(r, dict) and r.get("sku")]
    try:
        result = await _repo.upsert_products(filtered)
        count = int(result.get("count", 0))
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "count": count}


async def _run_job(
    job_id: str,
    sku: str,
    market: str,
    connector: str,
    depth: int,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    print(f"[mcp_job] start job id={job_id} sku={sku} connector={connector} depth={depth}")
    try:
        await _repo.mark_job_running(job_id)

        if connector == "mock":
            # Existing mock generator
            await _collector.ingest_stream(
                mock_ticks(sku=sku, market=market, n=max(1, int(depth))),
                delay_s=0.15,
            )

        elif connector == "httpjson":
            # Build connector via factory
            extra = extra or {}
            httpc = build_connector(
                "httpjson",
                base_url=extra.get("base_url", ""),
                headers=extra.get("headers", {}),
                source_name=extra.get("source_name", "httpjson"),
                price_path=extra.get("price_path", []),
            )
            # Stream ticks from the HTTP connector
            await _collector.ingest_stream(
                httpc.ticks(sku=sku, market=market, depth=depth),
                delay_s=0.05,
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
    # Only used by httpjson:
    base_url: str = "",
    source_name: str = "httpjson",
    price_path: list = None,
    headers: dict = None,
) -> dict:
    await _repo.init()
    try:
        depth_int = max(1, int(depth))
    except Exception:
        depth_int = 1

    # Collect extra args for httpjson
    extra: Dict[str, Any] = {}
    if connector.lower() == "httpjson":
        if not base_url:
            return {"ok": False, "error": "httpjson_missing_base_url"}
        extra = {
            "base_url": (base_url or "").rstrip("/"),
            "headers": headers or {},
            "source_name": source_name,
            "price_path": price_path or [],
        }

    job_id = await _repo.create_job(sku, market, connector, depth_int)
    asyncio.create_task(_run_job(job_id, sku, market, connector, depth_int, extra))
    return {"ok": True, "job_id": job_id}


@mcp.tool()
async def get_job_status(job_id: str) -> dict:
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
