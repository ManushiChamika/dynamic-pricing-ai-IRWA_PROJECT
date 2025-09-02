# scripts/backfill_market_data.py
import sqlite3, datetime

db = "market.db"
con = sqlite3.connect(db)
cur = con.cursor()

# Ensure timestamp column exists
cur.execute("""
  PRAGMA table_info(market_data)
""")
cols = {r[1] for r in cur.fetchall()}
if "update_time" not in cols:
    cur.execute("ALTER TABLE market_data ADD COLUMN update_time TEXT")

# Fill any missing timestamps with now (UTC)
now = datetime.datetime.utcnow().isoformat()
cur.execute("""
  UPDATE market_data
     SET update_time = COALESCE(update_time, ?)
""", (now,))

con.commit()
con.close()
print("Backfilled update_time in market_data")
