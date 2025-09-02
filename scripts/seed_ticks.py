# scripts/seed_ticks.py
import os, sqlite3, random, datetime

DB = os.getenv("DATA_DB", os.path.join("app", "data.db"))
SKUS = ["SKU-123", "SKU-456", "SKU-789"]

os.makedirs(os.path.dirname(DB), exist_ok=True)

con = sqlite3.connect(DB)
cur = con.cursor()

# Schema compatible with DataRepo.market_ticks
cur.execute("""
CREATE TABLE IF NOT EXISTS market_ticks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT NOT NULL,
  market TEXT NOT NULL,
  our_price REAL NOT NULL,
  competitor_price REAL,
  demand_index REAL,
  source TEXT NOT NULL,
  ts TEXT NOT NULL,
  ingested_at TEXT
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_ticks_sku_ts ON market_ticks(sku, ts)")
con.commit()

now = datetime.datetime.utcnow()
for sku in SKUS:
    base = 100.0 if sku == "SKU-123" else (120.0 if sku == "SKU-456" else 80.0)
    for i in range(50):
        t = now - datetime.timedelta(minutes=30 * i)
        price = round(base + random.uniform(-5, 5), 2)
        comp = None  # set to a float if you want 'competitor pressure' queries to show results
        ts = t.isoformat() + "Z"
        cur.execute("""
          INSERT INTO market_ticks (sku, market, our_price, competitor_price, demand_index, source, ts, ingested_at)
          VALUES (?,?,?,?,?,?,?,?)
        """, (sku, "DEFAULT", price, comp, None, "seed", ts, ts))
con.commit()
con.close()
print(f"Seeded market_ticks with synthetic data in {DB}.")
