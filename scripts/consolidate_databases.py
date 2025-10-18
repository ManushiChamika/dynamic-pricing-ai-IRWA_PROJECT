#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def consolidate_databases():
    root = Path(__file__).resolve().parents[1]
    app_db = root / "app" / "data.db"
    market_db = root / "data" / "market.db"
    
    if not market_db.exists():
        print(f"No market.db found at {market_db}, skipping migration")
        return
    
    print(f"Consolidating {market_db} into {app_db}...")
    
    app_conn = sqlite3.connect(app_db)
    app_cur = app_conn.cursor()
    
    app_cur.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            features TEXT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    app_cur.execute('''
        CREATE TABLE IF NOT EXISTS pricing_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            optimized_price REAL NOT NULL,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    ''')
    
    app_cur.execute('''
        CREATE TABLE IF NOT EXISTS decision_log (
            proposal_id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            previous_price REAL NOT NULL,
            proposed_price REAL NOT NULL,
            final_price REAL,
            status TEXT NOT NULL CHECK (status IN (
                'RECEIVED', 'APPROVED', 'REJECTED', 'APPLIED_AUTO', 'APPLY_FAILED', 'STALE'
            )),
            actor TEXT NOT NULL,
            reason TEXT,
            received_at TEXT NOT NULL,
            processed_at TEXT
        )
    ''')
    
    app_conn.commit()
    
    market_conn = sqlite3.connect(market_db)
    market_cur = market_conn.cursor()
    
    market_cur.execute("SELECT COUNT(*) FROM market_data")
    market_data_count = market_cur.fetchone()[0]
    
    market_cur.execute("SELECT COUNT(*) FROM pricing_list")
    pricing_list_count = market_cur.fetchone()[0]
    
    market_cur.execute("SELECT COUNT(*) FROM decision_log")
    decision_log_count = market_cur.fetchone()[0]
    
    print(f"\nFound {market_data_count} market_data, {pricing_list_count} pricing_list, {decision_log_count} decision_log rows")
    
    if market_data_count > 0:
        market_cur.execute("SELECT product_name, price, features, update_time FROM market_data")
        rows = market_cur.fetchall()
        app_cur.executemany(
            "INSERT OR REPLACE INTO market_data (product_name, price, features, update_time) VALUES (?, ?, ?, ?)",
            rows
        )
        print(f"Migrated {len(rows)} market_data rows")
    
    if pricing_list_count > 0:
        market_cur.execute("SELECT product_name, optimized_price, last_update, reason FROM pricing_list")
        rows = market_cur.fetchall()
        app_cur.executemany(
            "INSERT OR REPLACE INTO pricing_list (product_name, optimized_price, last_update, reason) VALUES (?, ?, ?, ?)",
            rows
        )
        print(f"Migrated {len(rows)} pricing_list rows")
    
    if decision_log_count > 0:
        market_cur.execute("SELECT proposal_id, product_id, previous_price, proposed_price, final_price, status, actor, reason, received_at, processed_at FROM decision_log")
        rows = market_cur.fetchall()
        app_cur.executemany(
            "INSERT OR REPLACE INTO decision_log (proposal_id, product_id, previous_price, proposed_price, final_price, status, actor, reason, received_at, processed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows
        )
        print(f"Migrated {len(rows)} decision_log rows")
    
    app_conn.commit()
    
    market_conn.close()
    app_conn.close()
    
    backup_path = market_db.parent / f"market.db.backup"
    market_db.rename(backup_path)
    print(f"\nConsolidation complete!")
    print(f"Original market.db moved to {backup_path}")
    print(f"All data now in {app_db}")

if __name__ == "__main__":
    consolidate_databases()
