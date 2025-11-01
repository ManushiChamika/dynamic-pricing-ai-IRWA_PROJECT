from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from core.auth_service import validate_session_token

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/stream")
async def api_prices_stream(sku: Optional[str] = None, token: Optional[str] = None):
    import asyncio
    import json
    import random
    import time
    import sqlite3

    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    owner_id = int(sess["user_id"])

    if sku:
        symbols = [sku]
    else:
        conn = sqlite3.connect('app/data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT product_name FROM market_data WHERE owner_id = ? LIMIT 50', (owner_id,))
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        if not symbols:
            symbols = ["SKU-1", "SKU-2", "SKU-3"]
    
    bases = {s: 100.0 + random.random() * 10.0 for s in symbols}

    async def _aiter():
        yield "event: ping\n" + "data: {}\n\n"
        while True:
            try:
                sym = random.choice(symbols)
                drift = random.uniform(-1.2, 1.2)
                price = max(1.0, bases[sym] + drift)
                bases[sym] = price
                payload = {
                    "sku": sym,
                    "price": round(price, 2),
                    "ts": int(time.time() * 1000),
                }
                yield "event: price\n" + "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                err = {"error": str(e)}
                yield "event: error\n" + "data: " + json.dumps(err, ensure_ascii=False) + "\n\n"
                await asyncio.sleep(1.0)

    return StreamingResponse(_aiter(), media_type="text/event-stream")
