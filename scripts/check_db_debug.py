import sqlite3

db = "app/data.db"
con = sqlite3.connect(db)
cur = con.cursor()

print("products:", cur.execute("select count(*) from products").fetchone()[0])
print("ticks   :", cur.execute("select count(*) from market_ticks").fetchone()[0])
print("sample name for FS-1:", cur.execute("select name from products where sku='FS-1'").fetchone()[0])

con.close()
