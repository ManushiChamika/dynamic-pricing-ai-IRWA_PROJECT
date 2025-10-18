import sqlite3
import random
from datetime import datetime

DB = 'app/data.db'
PRODUCT = 'iphone15'
COUNT = 85

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS market_data (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, price REAL NOT NULL, update_time TEXT DEFAULT CURRENT_TIMESTAMP)")
cur.execute("CREATE TABLE IF NOT EXISTS pricing_list (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT NOT NULL, optimized_price REAL NOT NULL, last_update TEXT DEFAULT CURRENT_TIMESTAMP, reason TEXT)")
cur.execute('DELETE FROM market_data WHERE product_name=?', (PRODUCT,))
for _ in range(COUNT):
    price = round(1100 + random.uniform(-50, 200), 2)
    cur.execute('INSERT INTO market_data (product_name, price, update_time) VALUES (?,?,?)', (PRODUCT, price, datetime.now().isoformat()))
conn.commit()
print(f'inserted {COUNT} records for {PRODUCT} into {DB}')
conn.close()
