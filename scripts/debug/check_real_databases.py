import sqlite3

auth_db = "data/auth.db"
data_db = "data/market.db"
alert_db = "data/alerts.db"

print("=== Users in data/auth.db ===")
conn_auth = sqlite3.connect(auth_db)
cursor_auth = conn_auth.cursor()

cursor_auth.execute("SELECT id, email, full_name FROM users")
users = cursor_auth.fetchall()
for user_id, email, full_name in users:
    print(f"  User ID: {user_id}, Email: {email}, Name: {full_name}")
conn_auth.close()

print("\n=== Products in data/market.db ===")
try:
    conn_market = sqlite3.connect(data_db)
    cursor_market = conn_market.cursor()
    
    cursor_market.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor_market.fetchall()]
    print(f"  Tables: {tables}")
    
    if 'product_catalog' in tables:
        cursor_market.execute("SELECT DISTINCT owner_id, COUNT(*) as count FROM product_catalog GROUP BY owner_id")
        products = cursor_market.fetchall()
        for owner_id, count in products:
            print(f"  Owner ID: {owner_id}, Product Count: {count}")
    
    conn_market.close()
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Incidents in data/alerts.db ===")
try:
    conn_alerts = sqlite3.connect(alert_db)
    cursor_alerts = conn_alerts.cursor()
    
    cursor_alerts.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor_alerts.fetchall()]
    print(f"  Tables: {tables}")
    
    if 'incidents' in tables:
        cursor_alerts.execute("PRAGMA table_info(incidents)")
        columns = [row[1] for row in cursor_alerts.fetchall()]
        print(f"  Columns: {columns}")
        
        cursor_alerts.execute("SELECT COUNT(*) FROM incidents")
        count = cursor_alerts.fetchone()[0]
        print(f"  Total incidents: {count}")
    
    conn_alerts.close()
except Exception as e:
    print(f"  Error: {e}")
