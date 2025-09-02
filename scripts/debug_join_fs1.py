
import sqlite3
con = sqlite3.connect("app/data.db")
con.row_factory = sqlite3.Row
cur = con.cursor()

print("-- direct check FS-1")
for r in cur.execute("""
SELECT t.sku, t.market, COUNT(*) as n, p.name
FROM market_ticks t
LEFT JOIN products p ON p.sku = t.sku AND p.market = t.market
WHERE t.sku = 'FS-1'
GROUP BY t.sku, t.market
"""):
    print(dict(r))
con.close()

