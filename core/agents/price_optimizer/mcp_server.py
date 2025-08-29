from __future__ import annotations

import asyncio
from typing import Dict, Any

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:
    # Allow file to exist even if MCP isn't installed; runtime will report
    FastMCP = None  # type: ignore

from .optimizer import Features, optimize


async def main():
    if FastMCP is None:
        raise RuntimeError("MCP not available: install the MCP package to run this server.")

    mcp = FastMCP("price-optimizer-service")

    @mcp.tool()
    async def optimize_price(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: {
          "sku": "...",
          "our_price": 100.0,
          "competitor_price": 98.0,
          "demand_index": 0.5,
          "cost": 90.0,
          "min_price": 80.0,
          "max_price": 130.0,
          "min_margin": 0.12
        }
        """
        f = Features(
            sku=str(payload["sku"]),
            our_price=float(payload["our_price"]),
            competitor_price=payload.get("competitor_price"),
            demand_index=payload.get("demand_index"),
            cost=payload.get("cost"),
        )
        res = optimize(
            f=f,
            min_price=float(payload.get("min_price", 0.0)),
            max_price=float(payload.get("max_price", 1e9)),
            min_margin=float(payload.get("min_margin", 0.12)),
        )
        return res

    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())


