from __future__ import annotations
import asyncio, random
from typing import Any, AsyncIterable, Dict, List, Optional
import httpx

API_BASE = "https://fakestoreapi.com"

async def _get_product(pid: int) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{API_BASE}/products/{pid}")
        r.raise_for_status()
        return r.json()

async def fakestore_ticks(
    sku: str,
    market: str = "DEFAULT",
    depth: int = 25,
    jitter_pct: float = 0.03,
) -> AsyncIterable[Dict[str, Any]]:
    """
    Turn Fake Store product price into a short price time-series (ticks).
    SKU format: FS-<id> (e.g., FS-1, FS-12)
    """
    try:
        pid = int(sku.replace("FS-", ""))
    except Exception:
        return

    prod = await _get_product(pid)
    base = float(prod.get("price", 0.0))
    if base <= 0:
        return

    price = base
    for _ in range(max(1, depth)):
        # random walk around base price
        step = random.uniform(-jitter_pct, jitter_pct) * base
        price = max(0.5, price + step)
        yield {
            "sku": sku,
            "our_price": round(price, 2),
            "source": "fakestore",
            "market": market,
            "competitor_price": None,
            "demand_index": None,
            "ts": None,  # repo will set default if needed
        }
        await asyncio.sleep(0)  # cooperate
