from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple


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


class _MCPDataCollectorTools:
    """MCP-backed tools using stdio transport.

    Requires the `mcp` package. If missing or any error occurs, callers should fall back to _LocalDataCollectorTools.
    """

    def __init__(self, command: Optional[str] = None, args: Optional[list[str]] = None) -> None:
        self.command = command or os.getenv("MCP_DC_CMD") or "python"
        default_args = ["-u", "-m", "core.agents.data_collector.mcp_server"]
        self.args = args if args is not None else (os.getenv("MCP_DC_ARGS", "").split() if os.getenv("MCP_DC_ARGS") else default_args)

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        try:
            from mcp.client.session import ClientSession  # type: ignore
            from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
        except Exception as e:
            return False, {"ok": False, "error": f"mcp_client_import_error: {e}"}

        try:
            server_params = StdioServerParameters(command=self.command, args=self.args)
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    # Some versions require listing tools first; ignore result
                    try:
                        await session.list_tools()
                    except Exception:
                        pass
                    res = await session.call_tool(tool_name, arguments=arguments)
                    # res is expected to be a mcp.types.CallToolResult-like object; try to access .content or .to_dict
                    try:
                        # Fast path: if the server returned JSON as a single text block
                        items = getattr(res, "content", []) or []
                        if items and hasattr(items[0], "text"):
                            import json as _json
                            payload = items[0].text
                            # Try parse JSON, else wrap as message
                            try:
                                data = _json.loads(payload)
                            except Exception:
                                data = {"ok": True, "content": payload}
                            return True, data if isinstance(data, dict) else {"ok": True, "data": data}
                    except Exception:
                        pass

                    # Fallback: try dict() conversion
                    try:
                        data = res.to_dict()  # type: ignore[attr-defined]
                        return True, data if isinstance(data, dict) else {"ok": True, "data": data}
                    except Exception:
                        return True, {"ok": True, "result": str(res)}
        except Exception as e:
            return False, {"ok": False, "error": f"mcp_client_runtime_error: {e}"}

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
