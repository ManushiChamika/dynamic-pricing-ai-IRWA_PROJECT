"""
Fix product_catalog.owner_id column type from TEXT to INTEGER
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "app" / "data.db"

def main():
    print(f"[FIX] Fixing product_catalog.owner_id type in {DB_PATH}\n")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Step 1: Check current schema
    print("[SCHEMA] Current product_catalog schema:")
    schema = cursor.execute("PRAGMA table_info(product_catalog)").fetchall()
    for col in schema:
        print(f"   {col}")
    
    # Step 2: Create new table with INTEGER owner_id
    print("\n[CREATE] Creating new table with INTEGER owner_id...")
    cursor.execute("""
        CREATE TABLE product_catalog_new (
            sku TEXT PRIMARY KEY,
            title TEXT,
            currency TEXT,
            current_price REAL,
            cost REAL,
            stock INTEGER,
            category TEXT,
            updated_at TEXT,
            owner_id INTEGER NOT NULL DEFAULT 33,
            source_url TEXT
        )
    """)
    
    # Step 3: Copy data, converting owner_id to INTEGER
    print("[COPY] Copying data with type conversion...")
    cursor.execute("""
        INSERT INTO product_catalog_new 
        SELECT 
            sku, 
            title, 
            currency, 
            current_price, 
            cost, 
            stock, 
            category, 
            updated_at, 
            CAST(owner_id AS INTEGER) as owner_id,
            source_url
        FROM product_catalog
    """)
    
    rows_copied = cursor.rowcount
    print(f"   [OK] Copied {rows_copied} rows")
    
    # Step 4: Drop old table and rename new table
    print("[REPLACE] Replacing old table...")
    cursor.execute("DROP TABLE product_catalog")
    cursor.execute("ALTER TABLE product_catalog_new RENAME TO product_catalog")
    
    # Step 5: Verify new schema
    print("\n[VERIFY] New product_catalog schema:")
    schema = cursor.execute("PRAGMA table_info(product_catalog)").fetchall()
    for col in schema:
        print(f"   {col}")
    
    # Step 6: Verify data
    print("\n[DATA] Sample data (first 5 rows):")
    rows = cursor.execute("""
        SELECT sku, title, current_price, owner_id, typeof(owner_id) as owner_id_type
        FROM product_catalog
        LIMIT 5
    """).fetchall()
    for row in rows:
        print(f"   SKU: {row[0]}, Title: {row[1][:30]}..., Price: {row[2]}, Owner: {row[3]} (type: {row[4]})")
    
    # Step 7: Count by owner_id
    print("\n[STATS] Products by owner_id:")
    counts = cursor.execute("""
        SELECT owner_id, COUNT(*) as count
        FROM product_catalog
        GROUP BY owner_id
    """).fetchall()
    for owner_id, count in counts:
        print(f"   Owner {owner_id}: {count} products")
    
    conn.commit()
    conn.close()
    
    print("\n[SUCCESS] Done! product_catalog.owner_id is now INTEGER type")

if __name__ == "__main__":
    main()
