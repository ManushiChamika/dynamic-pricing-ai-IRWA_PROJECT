"""Check app/data.db for ASUS ProArt product"""
import sqlite3
import os

os.chdir(r"C:\Users\sithu\OneDrive\Desktop\IRWA agentic AI\dynamic-pricing-ai-IRWA_PROJECT")

print("CHECKING app/data.db FOR ASUS PROART")
print("=" * 60)

try:
    conn = sqlite3.connect('app/data.db')
    cursor = conn.cursor()
    
    # Check all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}\n")
    
    # Check product_catalog
    cursor.execute("SELECT COUNT(*) FROM product_catalog")
    catalog_count = cursor.fetchone()[0]
    print(f"product_catalog: {catalog_count} products")
    
    cursor.execute("SELECT id, sku, name, current_price, owner_id FROM product_catalog WHERE name LIKE '%ASUS%' OR name LIKE '%ProArt%' OR name LIKE '%4910S%' LIMIT 10")
    asus_products = cursor.fetchall()
    print(f"\nASUS products in catalog: {len(asus_products)}")
    for p in asus_products:
        print(f"  id={p[0]}, sku={p[1]}, name={p[2]}, price={p[3]}, owner={p[4]}")
    
    # Check market_data
    cursor.execute("SELECT COUNT(*) FROM market_data")
    market_count = cursor.fetchone()[0]
    print(f"\n\nmarket_data: {market_count} records")
    
    cursor.execute("SELECT id, owner_id, product_name, price FROM market_data")
    market_records = cursor.fetchall()
    for m in market_records:
        print(f"  id={m[0]}, owner={m[1]}, product={m[2]}, price={m[3]}")
    
    # Check pricing_list
    cursor.execute("SELECT COUNT(*) FROM pricing_list")
    pricing_count = cursor.fetchone()[0]
    print(f"\n\npricing_list: {pricing_count} entries")
    
    # Check price_proposals
    cursor.execute("SELECT COUNT(*) FROM price_proposals")
    proposal_count = cursor.fetchone()[0]
    print(f"price_proposals: {proposal_count} proposals")
    
    # Check for user 33's products
    cursor.execute("SELECT id, sku, name, current_price FROM product_catalog WHERE owner_id = 33 LIMIT 10")
    user33_products = cursor.fetchall()
    print(f"\n\nUser 33's products: {len(user33_products)}")
    for p in user33_products:
        print(f"  id={p[0]}, sku={p[1]}, name={p[2]}, price={p[3]}")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
