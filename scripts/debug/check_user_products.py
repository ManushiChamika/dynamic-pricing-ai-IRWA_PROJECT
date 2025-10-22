import sqlite3

data_db = "app/data.db"
auth_db = "app/auth.db"

print("=== Users in auth.db ===")
conn_auth = sqlite3.connect(auth_db)
cursor_auth = conn_auth.cursor()

cursor_auth.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor_auth.fetchall()
print(f"  Available tables: {[t[0] for t in tables]}")

try:
    cursor_auth.execute("SELECT id, email FROM users")
    users = cursor_auth.fetchall()
    for user_id, email in users:
        print(f"  User ID: {user_id}, Email: {email}")
except sqlite3.OperationalError as e:
    print(f"  Error: {e}")
    
conn_auth.close()

print("\n=== Products in data.db ===")
conn_data = sqlite3.connect(data_db)
cursor_data = conn_data.cursor()
cursor_data.execute("SELECT DISTINCT owner_id, COUNT(*) as count FROM product_catalog GROUP BY owner_id")
products = cursor_data.fetchall()
for owner_id, count in products:
    print(f"  Owner ID: {owner_id}, Product Count: {count}")

print("\n=== Sample products ===")
cursor_data.execute("PRAGMA table_info(product_catalog)")
columns = [row[1] for row in cursor_data.fetchall()]
print(f"  Columns: {columns}")

cursor_data.execute(f"SELECT sku, {columns[1]}, owner_id FROM product_catalog LIMIT 5")
for sku, second_col, owner_id in cursor_data.fetchall():
    print(f"  SKU: {sku}, Col2: {second_col}, Owner: {owner_id}")

conn_data.close()
