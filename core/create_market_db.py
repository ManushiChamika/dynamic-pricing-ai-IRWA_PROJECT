import sqlite3

def create_tables(db_path='app/data.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            features TEXT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_owner ON market_data(owner_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            optimized_price REAL NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pricing_list_owner ON pricing_list(owner_id)')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
