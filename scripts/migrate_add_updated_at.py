import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = (BASE_DIR / "data" / "chat.db").resolve()

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT updated_at FROM threads LIMIT 1")
        print("Column 'updated_at' already exists.")
    except sqlite3.OperationalError:
        print("Adding 'updated_at' column to threads table...")
        cursor.execute("""
            ALTER TABLE threads 
            ADD COLUMN updated_at DATETIME
        """)
        cursor.execute("""
            UPDATE threads 
            SET updated_at = created_at
        """)
        conn.commit()
        print("Migration completed successfully!")
    
    conn.close()

if __name__ == "__main__":
    migrate()
