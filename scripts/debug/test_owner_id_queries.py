"""
Test that queries work with string owner_id against INTEGER column
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "app" / "data.db"

def main():
    print(f"[TEST] Testing owner_id queries in {DB_PATH}\n")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test 1: Query with string "33" against INTEGER column
    print("[TEST 1] Query product_catalog with string owner_id='33':")
    rows = cursor.execute("SELECT sku, title, owner_id FROM product_catalog WHERE owner_id = ?", ("33",)).fetchall()
    print(f"   Found {len(rows)} products")
    if rows:
        print(f"   First product: {rows[0]['sku']}, owner_id={rows[0]['owner_id']} (type: {type(rows[0]['owner_id'])})")
    
    # Test 2: Query with integer 33 against INTEGER column
    print("\n[TEST 2] Query product_catalog with integer owner_id=33:")
    rows = cursor.execute("SELECT sku, title, owner_id FROM product_catalog WHERE owner_id = ?", (33,)).fetchall()
    print(f"   Found {len(rows)} products")
    if rows:
        print(f"   First product: {rows[0]['sku']}, owner_id={rows[0]['owner_id']} (type: {type(rows[0]['owner_id'])})")
    
    # Test 3: JOIN query (like in list_price_proposals)
    print("\n[TEST 3] JOIN query (price_proposals + product_catalog) with string owner_id='33':")
    rows = cursor.execute("""
        SELECT pp.id, pp.sku, pp.proposed_price, pc.owner_id
        FROM price_proposals pp
        INNER JOIN product_catalog pc ON pp.sku = pc.sku
        WHERE pc.owner_id = ?
        LIMIT 5
    """, ("33",)).fetchall()
    print(f"   Found {len(rows)} proposals")
    for row in rows:
        print(f"   Proposal: SKU={row['sku']}, Price={row['proposed_price']}, Owner={row['owner_id']}")
    
    # Test 4: Check market_data table
    print("\n[TEST 4] Query market_data with integer owner_id=33:")
    rows = cursor.execute("SELECT id, product_name, price, owner_id FROM market_data WHERE owner_id = ? LIMIT 5", (33,)).fetchall()
    print(f"   Found {len(rows)} market data entries")
    for row in rows:
        print(f"   Product: {row['product_name']}, Price={row['price']}, Owner={row['owner_id']}")
    
    # Test 5: Check pricing_list table
    print("\n[TEST 5] Query pricing_list with integer owner_id=33:")
    rows = cursor.execute("SELECT id, product_name, optimized_price, owner_id FROM pricing_list WHERE owner_id = ? LIMIT 5", (33,)).fetchall()
    print(f"   Found {len(rows)} pricing list entries")
    for row in rows:
        print(f"   Product: {row['product_name']}, Price={row['optimized_price']}, Owner={row['owner_id']}")
    
    conn.close()
    print("\n[SUCCESS] All query tests completed!")

if __name__ == "__main__":
    main()
