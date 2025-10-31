import sqlite3
from datetime import datetime, timedelta, timezone

conn = sqlite3.connect('app/data.db')
cutoff = (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()

rows = conn.execute("""
    SELECT 
        pc.sku, 
        pc.title, 
        pc.source_url, 
        MAX(mt.ts) as last_update
    FROM product_catalog pc
    LEFT JOIN market_ticks mt ON pc.sku = mt.sku
    GROUP BY pc.sku, pc.title, pc.source_url
    HAVING last_update IS NULL OR last_update < ?
    ORDER BY 
        CASE WHEN pc.source_url IS NOT NULL THEN 0 ELSE 1 END,
        last_update ASC NULLS FIRST
    LIMIT 10
""", (cutoff,)).fetchall()

print('Stale products (no data or >60 min old):')
for r in rows:
    print(f'SKU: {r[0]}')
    print(f'Title: {r[1]}')
    print(f'URL: {r[2] if r[2] else "NO URL"}')
    print(f'Last: {r[3] if r[3] else "NEVER"}')
    print()

conn.close()
