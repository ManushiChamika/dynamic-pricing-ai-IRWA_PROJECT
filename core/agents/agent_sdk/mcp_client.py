from __future__ import annotations

import asyncio
import os
import time
import weakref
from typing import Any, Dict, Optional, Tuple, Union
from contextlib import asynccontextmanager


class _LocalDataCollectorTools:
    """Fallback that calls the in-process Python functions directly."""

    def __init__(self) -> None:
        # Lazy import to avoid import cost if using MCP
        from core.agents.data_collector import mcp_server as dc_mod  # type: ignore
        self._dc = dc_mod

    async def start_collection(self, sku: str, market: str = "DEFAULT", connector: str = "mock", depth: int = 1) -> Dict[str, Any]:
        return await self._dc.start_collection(sku=sku, market=market, connector=connector, depth=depth)

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        return await self._dc.get_job_status(job_id)

    async def fetch_market_features(self, sku: str, market: str = "DEFAULT", time_window: str = "P7D", freshness_sla_minutes: int = 60) -> Dict[str, Any]:
        return await self._dc.fetch_market_features(sku=sku, market=market, time_window=time_window, freshness_sla_minutes=freshness_sla_minutes)

    async def import_product_catalog(self, rows: list) -> Dict[str, Any]:
        return await self._dc.import_product_catalog(rows)


class _MCPConnectionPool:
    """Connection pool with lifecycle management for MCP stdio connections."""
    
    def __init__(self, max_connections: int = 3, connection_ttl: float = 300.0):
        self.max_connections = max_connections
        self.connection_ttl = connection_ttl
        self._pool: list[tuple[Any, Any, float]] = []  # (read, write, created_at)
        self._in_use: set[tuple[Any, Any]] = set()
        self._lock = asyncio.Lock()
        
    async def get_connection(self, command: str, args: list[str]) -> tuple[Any, Any]:
        """Get connection from pool or create new one."""
        async with self._lock:
            now = time.time()
            
            # Remove expired connections
            self._pool = [(r, w, t) for r, w, t in self._pool if now - t < self.connection_ttl]
            
            # Try to reuse existing connection
            if self._pool:
                read, write, created_at = self._pool.pop(0)
                self._in_use.add((read, write))
                return read, write
            
            # Create new connection if under limit
            if len(self._in_use) < self.max_connections:
                try:
                    from mcp.client.stdio import stdio_client, StdioServerParameters
                    server_params = StdioServerParameters(command=command, args=args)
                    
                    # Create connection with timeout
                    read, write = await asyncio.wait_for(
                        stdio_client(server_params).__aenter__(), timeout=10.0
                    )
                    self._in_use.add((read, write))
                    return read, write
                except Exception:
                    raise
            
            # If at limit, wait briefly and retry
            await asyncio.sleep(0.1)
            return await self.get_connection(command, args)
    
    async def return_connection(self, read: Any, write: Any, reusable: bool = True) -> None:
        """Return connection to pool or close it."""
        async with self._lock:
            conn_pair = (read, write)
            self._in_use.discard(conn_pair)
            
            if reusable and len(self._pool) < self.max_connections:
                self._pool.append((read, write, time.time()))
            else:
                # Close connection
                try:
                    await write.aclose()
                except Exception:
                    pass

    async def close_all(self) -> None:
        """Close all connections in pool."""
        async with self._lock:
            # Close pooled connections
            for read, write, _ in self._pool:
                try:
                    await write.aclose()
                except Exception:
                    pass
            
            # Close in-use connections (best effort)
            for read, write in self._in_use:
                try:
                    await write.aclose()
                except Exception:
                    pass
            
            self._pool.clear()
            self._in_use.clear()


class _MCPDataCollectorTools:
    """MCP-backed tools using stdio transport with connection pooling.

    Requires the `mcp` package. If missing or any error occurs, callers should fall back to _LocalDataCollectorTools.
    """
    
    _pools: Dict[str, _MCPConnectionPool] = {}
    _pools_lock = asyncio.Lock()

    def __init__(self, command: Optional[str] = None, args: Optional[list[str]] = None) -> None:
        self.command = command or os.getenv("MCP_DC_CMD") or "python"
        default_args = ["-u", "-m", "core.agents.data_collector.mcp_server"]
        self.args = args if args is not None else (os.getenv("MCP_DC_ARGS", "").split() if os.getenv("MCP_DC_ARGS") else default_args)
        
        # Pool key based on command + args
        self._pool_key = f"{self.command}:{':'.join(self.args)}"

    async def _get_pool(self) -> _MCPConnectionPool:
        """Get or create connection pool for this service."""
        async with self._pools_lock:
            if self._pool_key not in self._pools:
                self._pools[self._pool_key] = _MCPConnectionPool()
            return self._pools[self._pool_key]

    @classmethod
    async def cleanup_all_pools(cls) -> None:
        """Cleanup all connection pools. Call during shutdown."""
        async with cls._pools_lock:
            for pool in cls._pools.values():
                await pool.close_all()
            cls._pools.clear()

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any], timeout: float = 30.0, retries: int = 3) -> Tuple[bool, Dict[str, Any]]:
        """Call MCP tool with connection pooling, timeout, retries, and exponential backoff."""
        import random
        
        try:
            from mcp.client.session import ClientSession  # type: ignore
        except Exception as e:
            return False, {"ok": False, "error": f"mcp_client_import_error: {e}", "error_code": "import_error"}

        last_error = None
        pool = await self._get_pool()
        
        for attempt in range(retries):
            read, write = None, None
            reusable = True
            
            try:
                # Get connection from pool
                read, write = await asyncio.wait_for(
                    pool.get_connection(self.command, self.args), timeout=15.0
                )
                
                # Wrap session operation in timeout
                async with asyncio.timeout(timeout):
                    async with ClientSession(read, write) as session:
                        # Initialize with shorter timeout
                        await asyncio.wait_for(session.initialize(), timeout=10.0)
                        
                        # List tools with timeout (optional operation for validation)
                        try:
                            await asyncio.wait_for(session.list_tools(), timeout=5.0)
                        except Exception:
                            pass  # Non-critical operation
                        
                        # Call tool with remaining timeout
                        res = await session.call_tool(tool_name, arguments=arguments)
                        
                        # Parse response
                        try:
                            # Fast path: JSON text response
                            items = getattr(res, "content", []) or []
                            if items and hasattr(items[0], "text"):
                                import json as _json
                                payload = items[0].text
                                try:
                                    data = _json.loads(payload)
                                    if isinstance(data, dict):
                                        # Add metadata
                                        data.setdefault("_mcp_meta", {
                                            "tool": tool_name, 
                                            "attempt": attempt + 1,
                                            "timestamp": time.time(),
                                            "pool_key": self._pool_key
                                        })
                                        return True, data
                                    else:
                                        return True, {"ok": True, "data": data, "_mcp_meta": {"tool": tool_name, "attempt": attempt + 1}}
                                except Exception:
                                    return True, {"ok": True, "content": payload, "_mcp_meta": {"tool": tool_name, "attempt": attempt + 1}}
                        except Exception:
                            pass

                        # Fallback: dict conversion
                        try:
                            data = res.to_dict()  # type: ignore[attr-defined]
                            if isinstance(data, dict):
                                data.setdefault("_mcp_meta", {
                                    "tool": tool_name, 
                                    "attempt": attempt + 1, 
                                    "timestamp": time.time(),
                                    "pool_key": self._pool_key
                                })
                                return True, data
                            else:
                                return True, {"ok": True, "data": data, "_mcp_meta": {"tool": tool_name, "attempt": attempt + 1}}
                        except Exception:
                            return True, {"ok": True, "result": str(res), "_mcp_meta": {"tool": tool_name, "attempt": attempt + 1}}
                                
            except asyncio.TimeoutError:
                last_error = f"timeout_after_{timeout}s"
                reusable = False  # Don't reuse timed-out connections
            except Exception as e:
                last_error = str(e)
                reusable = False  # Don't reuse failed connections
            finally:
                # Return connection to pool
                if read is not None and write is not None:
                    await pool.return_connection(read, write, reusable=reusable)
            
            # Exponential backoff with jitter (except on last attempt)
            if attempt < retries - 1:
                backoff = min(2 ** attempt + random.uniform(0, 1), 10.0)  # Max 10s
                await asyncio.sleep(backoff)
        
        return False, {
            "ok": False, 
            "error": f"mcp_client_runtime_error: {last_error}", 
            "error_code": "timeout" if "timeout" in str(last_error) else "runtime_error",
            "attempts": retries,
            "_mcp_meta": {"tool": tool_name, "final_attempt": True, "pool_key": self._pool_key}
        }

    async def start_collection(self, sku: str, market: str = "DEFAULT", connector: str = "mock", depth: int = 1) -> Dict[str, Any]:
        ok, res = await self._call_tool("start_collection", {
            "sku": sku,
            "market": market,
            "connector": connector,
            "depth": int(depth),
        })
        return res if ok else res

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        ok, res = await self._call_tool("get_job_status", {"job_id": job_id})
        return res if ok else res

    async def fetch_market_features(self, sku: str, market: str = "DEFAULT", time_window: str = "P7D", freshness_sla_minutes: int = 60) -> Dict[str, Any]:
        ok, res = await self._call_tool("fetch_market_features", {
            "sku": sku,
            "market": market,
            "time_window": time_window,
            "freshness_sla_minutes": int(freshness_sla_minutes),
        })
        return res if ok else res

    async def import_product_catalog(self, rows: list) -> Dict[str, Any]:
        ok, res = await self._call_tool("import_product_catalog", {"rows": rows})
        return res if ok else res


class DataCollectorTools:
    """Facade over data-collector functions, MCP-enabled via USE_MCP toggle."""

    def __init__(self, use_mcp: bool | None = None) -> None:
        if use_mcp is None:
            use_mcp = str(os.getenv("USE_MCP", "")).strip() in {"1", "true", "yes", "on"}
        self._use_mcp = bool(use_mcp)
        self._mcp_impl: Optional[_MCPDataCollectorTools] = _MCPDataCollectorTools() if self._use_mcp else None
        self._local_impl = _LocalDataCollectorTools()

    def using_mcp(self) -> bool:
        return self._use_mcp and (self._mcp_impl is not None)

    async def start_collection(self, *args, **kwargs) -> Dict[str, Any]:
        if self.using_mcp():
            res = await self._mcp_impl.start_collection(*args, **kwargs)  # type: ignore[arg-type]
            if res and res.get("ok"):
                return res
        return await self._local_impl.start_collection(*args, **kwargs)

    async def get_job_status(self, *args, **kwargs) -> Dict[str, Any]:
        if self.using_mcp():
            res = await self._mcp_impl.get_job_status(*args, **kwargs)  # type: ignore[arg-type]
            if res and res.get("ok") is not False:
                return res
        return await self._local_impl.get_job_status(*args, **kwargs)

    async def fetch_market_features(self, *args, **kwargs) -> Dict[str, Any]:
        if self.using_mcp():
            res = await self._mcp_impl.fetch_market_features(*args, **kwargs)  # type: ignore[arg-type]
            if res and res.get("ok") is not False:
                return res
        return await self._local_impl.fetch_market_features(*args, **kwargs)

    async def import_product_catalog(self, *args, **kwargs) -> Dict[str, Any]:
        if self.using_mcp():
            res = await self._mcp_impl.import_product_catalog(*args, **kwargs)  # type: ignore[arg-type]
            if res and res.get("ok") is not False:
                return res
        return await self._local_impl.import_product_catalog(*args, **kwargs)


def get_data_collector_client(use_mcp: bool | None = None) -> DataCollectorTools:
    return DataCollectorTools(use_mcp=use_mcp)


async def shutdown_mcp_clients() -> None:
    """Cleanup all MCP connection pools. Call during application shutdown."""
    await _MCPDataCollectorTools.cleanup_all_pools()


# Auto-cleanup on module finalization
_cleanup_scheduled = False

def _schedule_cleanup():
    """Schedule cleanup on interpreter shutdown."""
    global _cleanup_scheduled
    if not _cleanup_scheduled:
        import atexit
        import threading
        
        def cleanup_sync():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule cleanup
                    asyncio.create_task(shutdown_mcp_clients())
                else:
                    # If loop is not running, run cleanup synchronously
                    loop.run_until_complete(shutdown_mcp_clients())
            except Exception:
                pass  # Best effort cleanup
        
        atexit.register(cleanup_sync)
        _cleanup_scheduled = True

# Schedule cleanup when module is first imported
_schedule_cleanup()
