from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from backend.deps import get_current_user, get_repo
from core.agents.data_collector.repo import DataRepo
import asyncio
import json
import random
import time
import logging

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = logging.getLogger(__name__)


async def _fetch_products(repo: DataRepo, owner_id: str, sku_filter: Optional[str] = None) -> Dict[str, float]:
    try:
        products: Dict[str, float] = {}
        if sku_filter:
            row = await repo.get_product_by_sku_and_owner(sku_filter, owner_id)
            rows = [row] if row else []
        else:
            rows = await repo.get_products_by_owner(owner_id)
            rows = rows[:50]
        if not rows:
            logger.info(f"No products found for owner_id={owner_id}, sku_filter={sku_filter}")
            return {}
        for row in rows:
            try:
                sku = str(row.get("sku"))
                price_val = row.get("current_price")
                price = float(price_val) if price_val is not None else 100.0
                products[sku] = price
            except Exception as e:
                logger.warning(f"Invalid price for SKU {row.get('sku')}: {e}")
                products[str(row.get("sku"))] = 100.0
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return {}


@router.get("/stream")
async def api_prices_stream(
    sku: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    owner_id = str(current_user["user_id"]) 
    bases = await _fetch_products(repo, owner_id, sku)
    if not bases:
        logger.info(f"No catalog products found for owner_id={owner_id}")
        async def _empty_iter():
            yield "event: ping\n" + "data: {}\n\n"
            while True:
                await asyncio.sleep(10.0)
        return StreamingResponse(_empty_iter(), media_type="text/event-stream")
    logger.info(f"Streaming {len(bases)} products for owner_id={owner_id}")
    symbols = list(bases.keys())

    async def _aiter():
        try:
            yield "event: ping\n" + "data: {}\n\n"
            while True:
                try:
                    sym = random.choice(symbols)
                    drift = random.uniform(-1.2, 1.2)
                    current_base = bases.get(sym, 100.0)
                    price = max(1.0, current_base + drift)
                    bases[sym] = price
                    payload = {
                        "sku": sym,
                        "price": round(price, 2),
                        "ts": int(time.time() * 1000),
                    }
                    yield "event: price\n" + "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
                    await asyncio.sleep(1.0)
                except asyncio.CancelledError:
                    logger.info(f"Price stream cancelled for owner_id={owner_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in price stream: {e}")
                    err = {"error": "Internal streaming error"}
                    yield "event: error\n" + "data: " + json.dumps(err, ensure_ascii=False) + "\n\n"
                    await asyncio.sleep(1.0)
        except Exception as e:
            logger.error(f"Fatal error in price stream: {e}")

    return StreamingResponse(_aiter(), media_type="text/event-stream")
