import sqlite3

db_path = "app/alert.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(incidents)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Current columns: {columns}")

if "owner_id" not in columns:
    print("Adding owner_id column...")
    cursor.execute("ALTER TABLE incidents ADD COLUMN owner_id INTEGER")
    conn.commit()
    print("owner_id column added")
else:
    print("owner_id column already exists")

cursor.execute("PRAGMA table_info(incidents)")
print("\nUpdated schema:")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

conn.close()
print("\nDone!")
