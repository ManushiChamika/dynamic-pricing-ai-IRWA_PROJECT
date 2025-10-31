from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union

from core.agents.data_collector.repo import DataRepo
from core.agents.agent_sdk.mcp_client import get_data_collector_client


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        schema: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.schema = schema or self._infer_schema()

    def _infer_schema(self) -> Dict[str, Any]:
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"

            properties[name] = {"type": param_type}
            if param.default == inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    async def execute(self, **kwargs: Any) -> Any:
        if inspect.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            return self.func(**kwargs)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.register(
            "start_data_collection",
            "Start collecting data for a specific SKU and market",
            self._start_data_collection,
        )
        self.register(
            "get_job_status",
            "Get the status of a data collection job",
            self._get_job_status,
        )
        self.register(
            "optimize_price",
            "Run price optimization for a specific SKU",
            self._optimize_price,
        )
        self.register(
            "upsert_product",
            "Insert or update a product in the catalog",
            self._upsert_product,
        )

    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        tool = Tool(name, description, func, schema)
        self._tools[name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.schema,
            }
            for tool in self._tools.values()
        ]

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return await tool.execute(**kwargs)

    async def _start_data_collection(
        self, sku: str, market: str = "DEFAULT", connector: str = "mock", depth: int = 3
    ) -> Dict[str, Any]:
        client = get_data_collector_client()
        return await client.start_collection(sku, market=market, connector=connector, depth=depth)

    async def _get_job_status(self, job_id: str) -> Dict[str, Any]:
        client = get_data_collector_client()
        return await client.get_job_status(job_id)

    async def _optimize_price(self, sku: str, objective: str = "maximize profit") -> Dict[str, Any]:
        from core.agents.price_optimizer.agent import PricingOptimizerAgent
        optimizer = PricingOptimizerAgent()
        return await optimizer.process_full_workflow(objective, sku)

    async def _upsert_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        repo = DataRepo()
        await repo.init()
        await repo.upsert_products([product_data])
        return {"status": "ok", "sku": product_data.get("sku")}


_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry