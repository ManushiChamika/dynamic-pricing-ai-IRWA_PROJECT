# scripts/init_products.py
import sqlite3

DB = "market.db"

rows = [
    ("SKU-123", "Wireless Mouse X1"),
    ("SKU-456", "Mechanical Keyboard K2"),
    ("SKU-789", "USB-C Hub 7-in-1"),
]

con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS products (sku TEXT PRIMARY KEY, name TEXT)")
cur.executemany("INSERT OR REPLACE INTO products(sku, name) VALUES (?,?)", rows)
con.commit()
con.close()
print("Seeded 'products' table with", len(rows), "rows in", DB)
