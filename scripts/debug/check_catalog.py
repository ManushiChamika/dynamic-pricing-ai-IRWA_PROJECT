"""Check catalog database for product inventory"""
import sqlite3
import os

os.chdir(r"C:\Users\sithu\OneDrive\Desktop\IRWA agentic AI\dynamic-pricing-ai-IRWA_PROJECT")

print("CATALOG DATABASE CHECK")
print("=" * 60)

try:
    conn = sqlite3.connect('data/catalog.db')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}\n")
    
    # Get product count
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    print(f"Total products in catalog: {count}\n")
    
    # Get sample products
    cursor.execute('SELECT id, name, current_price, owner_id FROM products LIMIT 10')
    print("Sample products:")
    for r in cursor.fetchall():
        print(f"  id={r[0]}, name={r[1][:50]}, price={r[2]}, owner_id={r[3]}")
    
    # Search for ASUS ProArt
    cursor.execute("SELECT id, name, current_price, owner_id FROM products WHERE name LIKE '%ASUS%' OR name LIKE '%ProArt%' OR name LIKE '%4910S%'")
    asus = cursor.fetchall()
    print(f"\n\nASUS products found: {len(asus)}")
    for r in asus:
        print(f"  id={r[0]}, name={r[1]}, price={r[2]}, owner_id={r[3]}")
    
    # Check for user 33's products
    cursor.execute('SELECT COUNT(*) FROM products WHERE owner_id = 33')
    user33_count = cursor.fetchone()[0]
    print(f"\n\nProducts owned by user 33: {user33_count}")
    
    if user33_count > 0:
        cursor.execute('SELECT id, name, current_price FROM products WHERE owner_id = 33 LIMIT 5')
        print("User 33's products:")
        for r in cursor.fetchall():
            print(f"  id={r[0]}, name={r[1]}, price={r[2]}")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
