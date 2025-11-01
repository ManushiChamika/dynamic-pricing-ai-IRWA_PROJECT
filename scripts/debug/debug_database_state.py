"""Debug script to check database state and schemas"""
import sqlite3
import os

os.chdir(r"C:\Users\sithu\OneDrive\Desktop\IRWA agentic AI\dynamic-pricing-ai-IRWA_PROJECT")

print("=" * 60)
print("DATABASE STATE INVESTIGATION")
print("=" * 60)

# Check market.db
print("\n1. MARKET DATABASE (data/market.db)")
print("-" * 60)
try:
    conn = sqlite3.connect('data/market.db')
    cursor = conn.cursor()
    
    # Get schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='market_data'")
    schema = cursor.fetchone()
    print(f"Schema:\n{schema[0] if schema else 'Table not found'}\n")
    
    # Count records
    cursor.execute('SELECT COUNT(*) FROM market_data')
    total = cursor.fetchone()[0]
    print(f"Total records: {total}")
    
    # Owner distribution
    cursor.execute('SELECT COUNT(DISTINCT owner_id) FROM market_data')
    distinct_owners = cursor.fetchone()[0]
    print(f"Distinct owners: {distinct_owners}")
    
    cursor.execute('SELECT owner_id, COUNT(*) FROM market_data GROUP BY owner_id LIMIT 10')
    print("\nOwner distribution:")
    for row in cursor.fetchall():
        print(f"  owner_id={row[0]}: {row[1]} records")
    
    # Search for ASUS ProArt
    cursor.execute("SELECT id, owner_id, product_name, price FROM market_data WHERE product_name LIKE '%ASUS%ProArt%' OR product_name LIKE '%4910S%' LIMIT 5")
    asus_records = cursor.fetchall()
    print(f"\nASUS ProArt records found: {len(asus_records)}")
    for r in asus_records:
        print(f"  id={r[0]}, owner={r[1]}, name={r[2][:50]}, price={r[3]}")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")

# Check auth.db
print("\n\n2. AUTH DATABASE (data/auth.db)")
print("-" * 60)
try:
    conn = sqlite3.connect('data/auth.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    # Get users table schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    schema = cursor.fetchone()
    print(f"\nUsers table schema:\n{schema[0] if schema else 'Table not found'}")
    
    # Find user 33
    cursor.execute("SELECT * FROM users WHERE id = 33")
    user = cursor.fetchone()
    if user:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\nUser 33 data:")
        for col, val in zip(columns, user):
            print(f"  {col}: {val}")
    else:
        print("\nUser 33 not found")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")

# Check chat.db
print("\n\n3. CHAT DATABASE (data/chat.db)")
print("-" * 60)
try:
    conn = sqlite3.connect('data/chat.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    # Try to find thread 88 (adapt to actual schema)
    if ('chat_threads',) in tables or ('threads',) in tables:
        table_name = 'chat_threads' if ('chat_threads',) in tables else 'threads'
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        schema = cursor.fetchone()
        print(f"\nThread table schema:\n{schema[0] if schema else 'Not found'}")
        
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = 88")
        thread = cursor.fetchone()
        if thread:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"\nThread 88 data:")
            for col, val in zip(columns, thread):
                print(f"  {col}: {val}")
        else:
            print(f"\nThread 88 not found in {table_name}")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("INVESTIGATION COMPLETE")
print("=" * 60)
