
import sqlite3, os
db = os.path.join("app","data.db")
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS products(
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL,
  market TEXT NOT NULL,
  name TEXT,
  cost REAL,
  base_price REAL,
  currency TEXT,
  updated_at TEXT NOT NULL,
  UNIQUE(sku, market)
)
""")
rows = [
  ("SKU-123","DEFAULT","Wireless Mouse X1","USD"),
  ("SKU-456","DEFAULT","Mechanical Keyboard K2","USD"),
  ("SKU-789","DEFAULT","USB-C Hub 7-in-1","USD"),
]
for sku,market,name,currency in rows:
    cur.execute("""
      INSERT INTO products (sku, market, name, currency, updated_at)
      VALUES (?,?,?,?, datetime('now'))
      ON CONFLICT(sku, market) DO UPDATE SET
        name=excluded.name, currency=excluded.currency, updated_at=excluded.updated_at
    """, (sku, market, name, currency))
con.commit()
print("Inserted/updated 3 demo product names in", db)
print("Sample:", list(cur.execute("SELECT sku, market, name FROM products WHERE sku IN ('SKU-123','SKU-456','SKU-789')")))
con.close()



