from typing import Optional, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from core.auth_service import validate_session_token
import asyncio
import json
import random
import time
import aiosqlite
import logging

router = APIRouter(prefix="/api/prices", tags=["prices"])
logger = logging.getLogger(__name__)


async def _fetch_products(owner_id: str, sku_filter: Optional[str] = None) -> Dict[str, float]:
    try:
        async with aiosqlite.connect('app/data.db') as conn:
            if sku_filter:
                cursor = await conn.execute(
                    'SELECT sku, current_price FROM product_catalog WHERE owner_id = ? AND sku = ?',
                    (owner_id, sku_filter)
                )
            else:
                cursor = await conn.execute(
                    'SELECT sku, current_price FROM product_catalog WHERE owner_id = ? LIMIT 50',
                    (owner_id,)
                )
            rows = await cursor.fetchall()
            
            if not rows:
                logger.info(f"No products found for owner_id={owner_id}, sku_filter={sku_filter}")
                return {}
            
            products = {}
            for row in rows:
                try:
                    sku = row[0]
                    price = float(row[1]) if row[1] is not None else 100.0
                    products[sku] = price
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid price for SKU {row[0]}: {e}")
                    products[row[0]] = 100.0
            
            return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return {}


@router.get("/stream")
async def api_prices_stream(sku: Optional[str] = None, token: Optional[str] = None):
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    owner_id = str(sess["user_id"])
    
    bases = await _fetch_products(owner_id, sku)
    
    if not bases:
        logger.info(f"No catalog products found for owner_id={owner_id}, using demo data")
        bases = {
            "SKU-1": 100.0 + random.random() * 10.0,
            "SKU-2": 100.0 + random.random() * 10.0,
            "SKU-3": 100.0 + random.random() * 10.0
        }
    else:
        logger.info(f"Streaming {len(bases)} products for owner_id={owner_id}")
    
    symbols = list(bases.keys())

    async def _aiter():
        try:
            yield "event: ping\n" + "data: {}\n\n"
            
            while True:
                try:
                    if not symbols:
                        await asyncio.sleep(1.0)
                        continue
                    
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
