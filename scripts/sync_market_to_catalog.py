#!/usr/bin/env python3
"""
Sync Market Data to Product Catalog
Transfers laptop products from data/market.db to app/data.db product_catalog
so the LLM tools can access the same inventory data.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def sync_databases():
    """Sync products from market.db to app/data.db product_catalog"""
    
    # Database paths
    market_db_path = Path("data/market.db")
    app_db_path = Path("app/data.db")
    
    if not market_db_path.exists():
        print(f"Error: {market_db_path} not found")
        return False
        
    if not app_db_path.exists():
        print(f"Error: {app_db_path} not found")
        return False
    
    print("Syncing market data to product catalog...")
    
    # Read from market.db
    market_products = []
    with sqlite3.connect(market_db_path) as market_conn:
        market_conn.row_factory = sqlite3.Row
        cursor = market_conn.execute("""
            SELECT md.product_name, md.price, md.features, pl.optimized_price 
            FROM market_data md
            LEFT JOIN pricing_list pl ON md.product_name = pl.product_name
            ORDER BY md.product_name
        """)
        
        for row in cursor.fetchall():
            # Parse features JSON to extract useful info
            features = {}
            if row['features']:
                try:
                    features = json.loads(row['features'])
                except:
                    features = {}
            
            # Generate SKU from product name (simplified)
            sku = row['product_name'].replace(' ', '-').replace('/', '-')[:20]
            
            # Use optimized price if available, otherwise market price
            current_price = row['optimized_price'] if row['optimized_price'] else row['price']
            
            # Estimate cost (assuming ~20% margin for realistic costing)
            cost = round(current_price * 0.8, 2)
            
            # Random stock between 5-50 units
            import random
            stock = random.randint(5, 50)
            
            product = {
                'sku': sku,
                'title': row['product_name'],
                'currency': 'LKR',  # Sri Lankan Rupees
                'current_price': current_price,
                'cost': cost,
                'stock': stock,
                'category': features.get('category', 'Laptop'),
                'brand': features.get('brand', 'Unknown'),
                'processor': features.get('processor', ''),
                'ram': features.get('ram', ''),
                'storage': features.get('storage', ''),
                'display': features.get('display', ''),
                'graphics': features.get('graphics', ''),
                'updated_at': datetime.now().isoformat()
            }
            market_products.append(product)
    
    print(f"Found {len(market_products)} products in market database")
    
    # Write to app/data.db
    with sqlite3.connect(app_db_path) as app_conn:
        # Work with existing product_catalog schema (sku, title, currency, current_price, cost, stock, updated_at)
        
        # Clear existing laptop products from catalog (keep demo items)
        print("Clearing existing laptop products from catalog...")
        app_conn.execute("DELETE FROM product_catalog WHERE title LIKE '%ASUS%' OR title LIKE '%HP%' OR title LIKE '%Dell%' OR title LIKE '%Lenovo%' OR title LIKE '%Acer%' OR title LIKE '%MSI%' OR title LIKE '%Apple%' OR title LIKE '%Samsung%' OR title LIKE '%Razer%'")
        
        # Insert market products using existing schema
        print("Inserting products into product_catalog...")
        for product in market_products:
            try:
                app_conn.execute("""
                    INSERT OR REPLACE INTO product_catalog 
                    (sku, title, currency, current_price, cost, stock, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    product['sku'], product['title'], product['currency'], 
                    product['current_price'], product['cost'], product['stock'],
                    product['updated_at']
                ))
            except Exception as e:
                print(f"Error inserting {product['sku']}: {e}")
        
        app_conn.commit()
    
    # Verify sync
    with sqlite3.connect(app_db_path) as app_conn:
        app_conn.row_factory = sqlite3.Row
        count = app_conn.execute("SELECT COUNT(*) FROM product_catalog").fetchone()[0]
        print(f"\nSync completed! Product catalog now has {count} total items")
        
        # Show sample
        print("\nSample products in catalog:")
        rows = app_conn.execute("""
            SELECT sku, title, current_price, currency, stock 
            FROM product_catalog 
            ORDER BY current_price 
            LIMIT 5
        """).fetchall()
        
        for row in rows:
            print(f"  {row[0]}: {row[1]} - {row[3]} {row[2]:.2f} (Stock: {row[4]})")
    
    print(f"\nReady to test! Try asking the AI: 'What laptops do we have in stock?'")
    return True

if __name__ == "__main__":
    success = sync_databases()
    if not success:
        exit(1)