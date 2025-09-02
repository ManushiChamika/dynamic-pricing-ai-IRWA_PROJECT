import sqlite3

# Path to your DB (already in project root)
DB_PATH = "market.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    name TEXT
)
""")

# Insert sample products
cur.executemany("""
INSERT OR REPLACE INTO products (sku, name) VALUES (?, ?)
""", [
    ("SKU-123", "Wireless Mouse X1"),
    ("SKU-456", "Mechanical Keyboard K2"),
    ("SKU-789", "USB-C Hub 7-in-1")
])

conn.commit()
conn.close()
print("✅ Products table created and populated!")
