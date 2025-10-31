import sqlite3
from pathlib import Path

def migrate():
    db_path = Path(__file__).parent.parent / "app" / "data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(product_catalog)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "source_url" not in columns:
        print("Adding source_url column to product_catalog...")
        cursor.execute("ALTER TABLE product_catalog ADD COLUMN source_url TEXT")
        conn.commit()
        print("Migration completed")
    else:
        print("source_url column already exists")
    
    conn.close()

if __name__ == "__main__":
    migrate()
