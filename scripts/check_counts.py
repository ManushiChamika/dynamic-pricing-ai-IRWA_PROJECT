import sqlite3

db = "market.db"
con = sqlite3.connect(db); con.row_factory = sqlite3.Row
cur = con.cursor()

def exists(tbl):
    return cur.execute(
        "select name from sqlite_master where type='table' and name=?",
        (tbl,)
    ).fetchone() is not None

def count(tbl):
    if not exists(tbl): return "n/a"
    return cur.execute(f"select count(*) c from {tbl}").fetchone()["c"]

print("products      rows:", count("products"))
print("market_ticks rows:", count("market_ticks"))
print("market_data  rows:", count("market_data"))

con.close()
