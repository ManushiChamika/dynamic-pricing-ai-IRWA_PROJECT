
import sqlite3, os
src = "market.db"
dst = os.path.join("app","data.db")
con = sqlite3.connect(dst)
cur = con.cursor()
cur.execute("ATTACH DATABASE ? AS srcdb", (src,))
# ensure destination has table
cur.executescript("""
CREATE TABLE IF NOT EXISTS market_ticks(
  id INTEGER PRIMARY KEY,
  sku TEXT NOT NULL,
  market TEXT NOT NULL,
  our_price REAL NOT NULL,
  competitor_price REAL,
  demand_index REAL,
  source TEXT NOT NULL,
  ts TEXT NOT NULL,
  ingested_at TEXT
);
""")
cur.execute("""
INSERT INTO market_ticks (sku, market, our_price, competitor_price, demand_index, source, ts, ingested_at)
SELECT sku, market, our_price, competitor_price, demand_index, source, ts, COALESCE(ingested_at, ts)
FROM srcdb.market_ticks
""")
print("Copied", cur.rowcount, "ticks into", dst)
con.commit()
con.close()


