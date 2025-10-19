import sqlite3
import random
from datetime import datetime, timedelta

DB = 'app/data.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT sku, title, current_price, owner_id FROM product_catalog")
products = cur.fetchall()

print(f"Found {len(products)} products in catalog")

for sku, title, current_price, owner_id in products:
    if current_price is None:
        print(f"Skipping {sku} - no current price")
        continue
    
    owner_id = owner_id or 1
    base_price = float(current_price)
    
    market_records = 0
    for i in range(15):
        competitor_price = round(base_price * random.uniform(0.85, 1.15), 2)
        timestamp = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        cur.execute(
            'INSERT INTO market_data (owner_id, product_name, price, update_time) VALUES (?,?,?,?)',
            (owner_id, title, competitor_price, timestamp)
        )
        market_records += 1
    
    optimized_price = round(base_price * random.uniform(0.92, 1.08), 2)
    cur.execute(
        'INSERT OR REPLACE INTO pricing_list (owner_id, product_name, optimized_price, last_update, reason) VALUES (?,?,?,?,?)',
        (owner_id, title, optimized_price, datetime.now().isoformat(), "Competitive pricing analysis")
    )
    
    print(f"Added {market_records} market records + pricing for {sku}: {title}")

conn.commit()
conn.close()

print("\nMarket data population complete!")
