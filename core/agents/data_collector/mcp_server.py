import asyncio
import inspect
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import json
from pydantic import BaseModel, ValidationError, Field

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
from .connectors.mock import mock_ticks
from ..agent_sdk.health_tools import ping, version, health
from ..agent_sdk.auth import verify_capability, AuthError, get_auth_metrics

# Input validation schemas using Pydantic
class StartCollectionRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    market: str = Field("DEFAULT", min_length=1)
    connector: str = Field("mock", pattern=r"^(mock|web_scraper|api)$")
    depth: int = Field(1, ge=1, le=100)

class FetchMarketFeaturesRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    market: str = Field("DEFAULT", min_length=1) 
    time_window: str = Field("P7D", pattern=r"^P\d+D$")
    freshness_sla_minutes: int = Field(60, ge=1, le=1440)

class ImportProductCatalogRequest(BaseModel):
    rows: List[Dict[str, Any]] = Field(..., min_items=1)
    owner_id: str = Field(..., min_length=1)

class JobStatusRequest(BaseModel):
    job_id: str = Field(..., min_length=1)

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
    sku: str, market: str = "DEFAULT", time_window: str = "P7D", freshness_sla_minutes: int = 60, capability_token: str = ""
) -> dict:
    """Fetch market features for a SKU with validation."""
    try:
        # Validate auth
        verify_capability(capability_token, "read")
        
        # Validate input
        request = FetchMarketFeaturesRequest(
            sku=sku, 
            market=market, 
            time_window=time_window, 
            freshness_sla_minutes=freshness_sla_minutes
        )
        
        await _repo.init()
        since_iso = _since_iso_from_window(request.time_window)
        result = await _repo.features_for(request.sku, request.market, since_iso)
        
        # Ensure result has proper structure
        if not isinstance(result, dict):
            result = {"ok": True, "features": result}
        # Ensure standard fields
        result.setdefault("ok", True)
        result.setdefault("sku", request.sku)
        result.setdefault("market", request.market)
        result.setdefault("time_window", request.time_window)
        
        return result
        
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}


@mcp.tool()
async def ingest_tick(d: dict, capability_token: str = "") -> dict:
    try:
        verify_capability(capability_token, "write")
        await _repo.init()
        await _collector.ingest_tick(d)
        return {"ok": True}
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}


@mcp.tool()
async def import_product_catalog(rows: list, owner_id: str, capability_token: str = "") -> dict:
    """Import or update product rows into the product catalog with validation."""
    try:
        # Validate auth
        verify_capability(capability_token, "import")
        
        # Validate input
        request = ImportProductCatalogRequest(rows=rows, owner_id=owner_id)
        
        await _repo.init()
        
        # Only accept dict items with a sku
        filtered: List[Dict[str, Any]] = [r for r in request.rows if isinstance(r, dict) and r.get("sku")]
        
        if not filtered:
            return {"ok": False, "error": "no_valid_products", "message": "No products with valid SKUs found"}
        
        count = await _repo.upsert_products(filtered, request.owner_id)
        return {
            "ok": True, 
            "count": count,
            "processed": len(filtered),
            "total_input": len(request.rows)
        }
        
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}


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
    capability_token: str = ""
) -> dict:
    """Start a background collection job for a given sku/market with validation."""
    try:
        # Validate auth
        verify_capability(capability_token, "collect")
        
        # Validate input
        request = StartCollectionRequest(
            sku=sku,
            market=market,
            connector=connector,
            depth=depth
        )
        
        await _repo.init()

        # Validate connector support
        if request.connector not in ["mock"]:  # Extend as more connectors are added
            return {
                "ok": False, 
                "error": "unsupported_connector", 
                "supported_connectors": ["mock"]
            }

        job_id = await _repo.create_job(request.sku, request.market, request.connector, request.depth)
        
        # Fire-and-forget background job
        asyncio.create_task(_run_job(job_id, request.sku, request.market, request.connector, request.depth))
        
        return {
            "ok": True, 
            "job_id": job_id,
            "sku": request.sku,
            "market": request.market,
            "connector": request.connector,
            "depth": request.depth
        }
        
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}


@mcp.tool()  
async def get_job_status(job_id: str, capability_token: str = "") -> dict:
    """Return current job status with validation."""
    try:
        # Validate auth
        verify_capability(capability_token, "read")
        
        # Validate input
        request = JobStatusRequest(job_id=job_id)
        
        await _repo.init()
        row = await _repo.get_job(request.job_id)
        
        if row:
            return {"ok": True, "job": row, "job_id": request.job_id}
        else:
            return {"ok": False, "error": "job_not_found", "job_id": request.job_id}
            
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e), "job_id": job_id}


@mcp.tool()  
async def list_sources(capability_token: str = "") -> dict:
    """List available data sources with their current status."""
    try:
        # Validate auth
        verify_capability(capability_token, "read")
        # In production, this would check actual connector health
        sources = [
            {
                "name": "mock",
                "type": "mock", 
                "status": "active",
                "description": "Mock data generator for testing",
                "last_check": datetime.now(timezone.utc).isoformat()
            },
            {
                "name": "web_scraper", 
                "type": "web_scraper",
                "status": "inactive",
                "description": "Web scraping data connector",
                "last_check": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        return {
            "ok": True,
            "sources": sources,
            "count": len(sources)
        }
        
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}


# Health tools
@mcp.tool()
async def ping_health() -> dict:
    """Basic connectivity test."""
    return await ping()


@mcp.tool() 
async def version_info() -> dict:
    """Server version information."""
    return await version()


@mcp.tool()
async def health_check() -> dict:
    """Detailed health status."""
    return await health("data-collector", check_dependencies=True)


@mcp.tool()
async def auth_metrics(capability_token: str = "") -> Dict[str, Any]:
    """Get authentication metrics for this service."""
    try:
        # Validate auth - requires admin scope to view metrics
        verify_capability(capability_token, "admin")
        
        metrics = get_auth_metrics()
        return {
            "ok": True,
            "result": {
                "service": "data-collector",
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}


def _call_mcp_run() -> None:
    run_fn = getattr(mcp, "run", None)
    if run_fn is None:
        raise RuntimeError("FastMCP.run not available")
    if inspect.iscoroutinefunction(run_fn):
        asyncio.run(run_fn())
    else:
        run_fn()


def serve() -> None:
    asyncio.run(_repo.init())
    _call_mcp_run()


# Keep async main for backward compatibility if imported elsewhere, but avoid nested loops
async def main():
    # Initialize repository, then run the server in a separate thread to avoid nested event loops
    await _repo.init()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _call_mcp_run)


if __name__ == "__main__":
    serve()
