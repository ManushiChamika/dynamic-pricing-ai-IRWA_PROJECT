"""
Fix ownership issues and sync databases for user 33

This script:
1. Assigns ASUS ProArt 4910S (and other products) to user 33 in app/data.db
2. Syncs app/data.db product_catalog to data/market.db for user interaction tools
"""
import sqlite3
from pathlib import Path

# Change to project root
import os
os.chdir(r"C:\Users\sithu\OneDrive\Desktop\IRWA agentic AI\dynamic-pricing-ai-IRWA_PROJECT")

def assign_products_to_user33():
    """Assign all default_owner products to user 33"""
    print("=" * 60)
    print("STEP 1: Assigning products to user 33")
    print("=" * 60)
    
    conn = sqlite3.connect('app/data.db')
    cursor = conn.cursor()
    
    # Check current ownership
    cursor.execute('SELECT COUNT(*) FROM product_catalog WHERE owner_id = "default_owner"')
    default_count = cursor.fetchone()[0]
    print(f"Products owned by 'default_owner': {default_count}")
    
    cursor.execute('SELECT COUNT(*) FROM product_catalog WHERE owner_id = "33"')
    user33_count = cursor.fetchone()[0]
    print(f"Products owned by user 33: {user33_count}")
    
    # Update ownership
    cursor.execute('UPDATE product_catalog SET owner_id = "33" WHERE owner_id = "default_owner"')
    updated = cursor.rowcount
    conn.commit()
    
    print(f"\n[OK] Updated {updated} products to owner_id='33'")
    
    # Verify
    cursor.execute('SELECT sku, title, current_price FROM product_catalog WHERE owner_id = "33" LIMIT 5')
    print(f"\nSample of user 33's products:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1][:40]} - ${row[2]}")
    
    conn.close()

def sync_to_market_db():
    """Sync product_catalog to data/market.db"""
    print("\n" + "=" * 60)
    print("STEP 2: Syncing to data/market.db")
    print("=" * 60)
    
    # Read from app/data.db
    app_conn = sqlite3.connect('app/data.db')
    app_cursor = app_conn.cursor()
    
    app_cursor.execute('''
        SELECT sku, title, current_price, owner_id 
        FROM product_catalog 
        WHERE owner_id = "33"
    ''')
    products = app_cursor.fetchall()
    print(f"Found {len(products)} products for user 33 in app/data.db")
    
    # Write to data/market.db
    market_conn = sqlite3.connect('data/market.db')
    market_cursor = market_conn.cursor()
    
    # Clear existing data for user 33
    market_cursor.execute('DELETE FROM market_data WHERE owner_id = 33')
    deleted = market_cursor.rowcount
    print(f"Deleted {deleted} old market_data records for user 33")
    
    # Insert new data
    inserted = 0
    for sku, title, price, owner_id in products:
        market_cursor.execute('''
            INSERT INTO market_data (owner_id, product_name, price, features, update_time)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (33, title, price, f"SKU: {sku}"))
        inserted += 1
    
    market_conn.commit()
    print(f"[OK] Inserted {inserted} products into data/market.db")
    
    # Verify
    market_cursor.execute('SELECT COUNT(*) FROM market_data WHERE owner_id = 33')
    count = market_cursor.fetchone()[0]
    print(f"\nTotal market_data records for user 33: {count}")
    
    # Check ASUS ProArt specifically
    market_cursor.execute('''
        SELECT id, product_name, price 
        FROM market_data 
        WHERE owner_id = 33 AND product_name LIKE '%ASUS%ProArt%'
    ''')
    asus_products = market_cursor.fetchall()
    print(f"\nASUS ProArt products in market_data:")
    for row in asus_products:
        print(f"  id={row[0]}, name={row[1]}, price={row[2]}")
    
    app_conn.close()
    market_conn.close()

if __name__ == "__main__":
    print("\nFIXING DATABASE OWNERSHIP AND SYNC ISSUES\n")
    
    assign_products_to_user33()
    sync_to_market_db()
    
    print("\n" + "=" * 60)
    print("FIX COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart the backend server (if running)")
    print("2. Try the pricing optimization query again in Thread #88")
    print("3. The system should now find the ASUS ProArt 4910S product")
