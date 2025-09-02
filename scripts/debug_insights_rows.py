# scripts/debug_insights_rows.py
import os
import asyncio
import sqlite3
from pprint import pprint

# import your analytics module
from core.agents.analytics import insights

def resolve_db_path() -> str:
    # Same fallback order your agent uses
    return (
        os.getenv("MARKET_DB_PATH")
        or os.getenv("DATA_DB")
        or os.path.join("app", "data.db")
    )

def quick_sql_join_check(db_path: str, sample_skus: list[str]) -> None:
    print("\n== Direct SQL join check (market_ticks ↔ products) ==")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    for sku in sample_skus:
        rows = cur.execute(
            """
            SELECT t.sku, t.market, COUNT(*) AS n, p.name
            FROM market_ticks t
            LEFT JOIN products p
              ON p.sku = t.sku
             AND (p.market = t.market OR p.market IS NULL OR t.market IS NULL)
            WHERE t.sku = ?
            GROUP BY t.sku, t.market
            ORDER BY n DESC
            """,
            (sku,),
        ).fetchall()
        print(f"-- {sku}")
        for r in rows:
            print(dict(r))
    con.close()

async def main():
    db_path = resolve_db_path()
    market = "DEFAULT"
    print("DB path used:", db_path)
    print("Env MARKET_DB_PATH =", os.getenv("MARKET_DB_PATH"))
    print("Env DATA_DB       =", os.getenv("DATA_DB"))

    print("\n== top_trending_by_volume ==")
    try:
        rows = await insights.top_trending_by_volume(db_path, days=7, market=market, limit=10)
        pprint(rows)
        print("\nPretty view:")
        for r in rows:
            sku   = r.get("sku")
            label = r.get("label") or r.get("name") or sku
            n     = int(r.get("n", 0))
            print(f"• {label} ({sku}): {n} updates")
    except Exception as e:
        print("ERROR (trending):", e)

    print("\n== top_price_movers ==")
    try:
        rows = await insights.top_price_movers(db_path, days=7, market=market, limit=10)
        pprint(rows)
        print("\nPretty view:")
        for r in rows:
            sku     = r.get("sku")
            label   = r.get("label") or r.get("name") or sku
            first_p = r.get("first_price")
            last_p  = r.get("last_price")
            pct     = float(r.get("pct_change") or 0.0) * 100.0
            arrow   = "↗️" if (first_p is not None and last_p is not None and last_p >= first_p) else "↘️"
            print(f"{arrow} {label} ({sku}): {first_p} → {last_p} (Δ {pct:+.1f}%)")
    except Exception as e:
        print("ERROR (movers):", e)

    print("\n== highest_competitor_pressure ==")
    try:
        rows = await insights.highest_competitor_pressure(db_path, days=7, market=market, limit=10)
        if rows:
            pprint(rows)
            print("\nPretty view:")
            for r in rows:
                sku      = r.get("sku")
                label    = r.get("label") or r.get("name") or sku
                avg_ours = float(r.get("avg_ours") or 0.0)
                avg_comp = float(r.get("avg_comp") or 0.0)
                delta    = avg_comp - avg_ours
                print(f"• {label} ({sku}): Δ={delta:.2f} (ours {avg_ours:.2f}, comp {avg_comp:.2f})")
        else:
            print("(no competitor_price data in ticks)")
    except Exception as e:
        print("ERROR (pressure):", e)

    # A small direct SQL sanity check for a few common SKUs
    quick_sql_join_check(db_path, sample_skus=["FS-1", "FS-10", "SKU-123"])

if __name__ == "__main__":
    asyncio.run(main())
