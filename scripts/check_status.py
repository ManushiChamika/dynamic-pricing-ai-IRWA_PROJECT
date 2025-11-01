import sqlite3

print("=== CATALOG DATABASE (app/data.db) ===")
conn_catalog = sqlite3.connect('app/data.db')
cursor_catalog = conn_catalog.cursor()

cursor_catalog.execute('SELECT COUNT(*) FROM product_catalog')
total = cursor_catalog.fetchone()[0]
print(f"Total products: {total}")

cursor_catalog.execute('SELECT COUNT(*) FROM product_catalog WHERE source_url IS NOT NULL AND source_url != ""')
with_urls = cursor_catalog.fetchone()[0]
print(f"Products with URLs: {with_urls}")

cursor_catalog.execute('SELECT sku, title, source_url FROM product_catalog WHERE title LIKE "%MacBook%" LIMIT 5')
macbooks = cursor_catalog.fetchall()
print("\nMacBook products:")
for sku, title, url in macbooks:
    print(f"  SKU: {sku}")
    print(f"  Title: {title}")
    print(f"  URL: {url if url else 'NO URL'}")
    print()

conn_catalog.close()

print("\n=== MARKET DATABASE (data/market.db) ===")
conn_market = sqlite3.connect('data/market.db')
cursor_market = conn_market.cursor()

cursor_market.execute('SELECT COUNT(*) FROM ingestion_jobs')
jobs_count = cursor_market.fetchone()[0]
print(f"Total ingestion jobs: {jobs_count}")

if jobs_count > 0:
    cursor_market.execute('SELECT id, sku, connector, status, started_at FROM ingestion_jobs ORDER BY id DESC LIMIT 5')
    jobs = cursor_market.fetchall()
    print("\nRecent ingestion jobs:")
    for job in jobs:
        print(f"  Job {job[0]}: SKU={job[1]}, Connector={job[2]}, Status={job[3]}, Started={job[4]}")

cursor_market.execute('SELECT COUNT(*) FROM market_ticks')
ticks_count = cursor_market.fetchone()[0]
print(f"\nTotal market ticks: {ticks_count}")

if ticks_count > 0:
    cursor_market.execute('SELECT sku, market, competitor_price, ts FROM market_ticks ORDER BY id DESC LIMIT 5')
    ticks = cursor_market.fetchall()
    print("\nRecent market ticks:")
    for tick in ticks:
        print(f"  SKU={tick[0]}, Market={tick[1]}, Price=${tick[2]}, Time={tick[3]}")

conn_market.close()
