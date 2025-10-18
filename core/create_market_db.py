import sqlite3

def create_tables(db_path='app/data.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create market_data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            features TEXT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create pricing_list table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            optimized_price REAL NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
