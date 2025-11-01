"""Find which database has the actual product data"""
import sqlite3
import os

os.chdir(r"C:\Users\sithu\OneDrive\Desktop\IRWA agentic AI\dynamic-pricing-ai-IRWA_PROJECT")

print("SEARCHING FOR PRODUCT DATA ACROSS ALL DATABASES")
print("=" * 60)

db_files = [
    'data/data.db',
    'data/market.db',
    'data/catalog.db',
    'data/pricing_agent.db',
    'app/data.db'
]

for db_path in db_files:
    if not os.path.exists(db_path):
        print(f"\n{db_path}: [NOT FOUND]")
        continue
        
    print(f"\n{db_path}")
    print("-" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        print(f"Tables: {table_names}")
        
        # Check for product-related tables
        product_tables = ['products', 'product', 'catalog', 'inventory', 'market_data']
        for table in product_tables:
            if table in table_names:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
                
                # Show sample
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"    Columns: {columns[:5]}...")
                
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    print(f"    Sample: {dict(zip(columns[:5], sample[:5] if sample else []))}")
        
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
