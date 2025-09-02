
import sqlite3, os
src = os.path.join("app","data.db")
dst = "market.db"
con = sqlite3.connect(dst)
cur = con.cursor()
cur.execute("ATTACH DATABASE ? AS srcdb", (src,))
cur.executescript("""
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
);
""")
cur.execute("""
INSERT INTO products (sku, market, name, cost, base_price, currency, updated_at)
SELECT sku, market, name, cost, base_price, currency, updated_at
FROM srcdb.products
ON CONFLICT(sku, market) DO UPDATE SET
  name=excluded.name,
  cost=excluded.cost,
  base_price=excluded.base_price,
  currency=excluded.currency,
  updated_at=excluded.updated_at
""")
print("Upserted", cur.rowcount, "products into", dst)
con.commit()
con.close()

