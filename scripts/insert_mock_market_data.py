import sqlite3
import random
from datetime import datetime
import sys

DB = 'app/data.db'
PRODUCT = 'iphone15'
COUNT = 85
OWNER_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, product_name TEXT NOT NULL, price REAL NOT NULL, update_time TEXT DEFAULT CURRENT_TIMESTAMP)")
cur.execute("CREATE TABLE IF NOT EXISTS pricing_list (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL, product_name TEXT NOT NULL, optimized_price REAL NOT NULL, last_update TEXT DEFAULT CURRENT_TIMESTAMP, reason TEXT)")
cur.execute('DELETE FROM market_data WHERE product_name=? AND owner_id=?', (PRODUCT, OWNER_ID))
for _ in range(COUNT):
    price = round(1100 + random.uniform(-50, 200), 2)
    cur.execute('INSERT INTO market_data (owner_id, product_name, price, update_time) VALUES (?,?,?,?)', (OWNER_ID, PRODUCT, price, datetime.now().isoformat()))
conn.commit()
print(f'inserted {COUNT} records for {PRODUCT} (owner_id={OWNER_ID}) into {DB}')
conn.close()
