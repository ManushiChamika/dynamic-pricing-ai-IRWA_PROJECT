import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "chat.db"

def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(threads)")
    columns = cursor.fetchall()
    print("Current schema:")
    for col in columns:
        print(f"  {col}")
    
    print("\nMigrating threads table...")
    cursor.execute("BEGIN TRANSACTION")
    
    cursor.execute("""
        CREATE TABLE threads_new (
            id INTEGER PRIMARY KEY,
            title VARCHAR(255) NOT NULL DEFAULT 'New Thread',
            owner_id INTEGER,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        INSERT INTO threads_new (id, title, owner_id, created_at, updated_at)
        SELECT id, title, owner_id, created_at, COALESCE(updated_at, created_at)
        FROM threads
    """)
    
    cursor.execute("DROP TABLE threads")
    cursor.execute("ALTER TABLE threads_new RENAME TO threads")
    cursor.execute("CREATE INDEX ix_threads_owner_id ON threads (owner_id)")
    
    cursor.execute("COMMIT")
    
    cursor.execute("PRAGMA table_info(threads)")
    columns = cursor.fetchall()
    print("\nNew schema:")
    for col in columns:
        print(f"  {col}")
    
    conn.close()
    print(f"\n✓ Migration complete: {DB_PATH}")

if __name__ == "__main__":
    migrate()
