import sqlite3, json, os, sys

# Open the market DB in the repository root (data/market.db)
db = os.path.join(os.path.dirname(__file__), 'data', 'market.db')
print('DB path:', db)
if not os.path.exists(db):
    print('MISSING DB file')
    sys.exit(0)

conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('TABLES:', tables)

candidates = ['pricing_list','market_data','product_catalog','products','catalog','items','pricing_list_view','pricing_list_1']
found = False
for t in candidates:
    if t in tables:
        found = True
        print('\n---', t, 'sample rows---')
        cur.execute(f"PRAGMA table_info({t})")
        cols = [c[1] for c in cur.fetchall()]
        print('COLUMNS:', cols)
        cur.execute(f"SELECT * FROM {t} LIMIT 20")
        rows = cur.fetchall()
        for r in rows:
            print(json.dumps(dict(zip(cols, r)), default=str, ensure_ascii=False))

if not found:
    print('No product-related tables found among candidates')

conn.close()
