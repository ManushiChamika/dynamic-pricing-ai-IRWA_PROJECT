#!/usr/bin/env python3
"""
Sri Lankan Laptop Store - Sample Data Generator
Creates 100 realistic laptop products with Sri Lankan market pricing
"""

import sqlite3
import random
import json
from datetime import datetime, timedelta

def create_realistic_laptop_data():
    """Generate 20 realistic laptop products for Sri Lankan market"""
    
    # Sri Lankan laptop brands commonly available
    brands = {
        'ASUS': {'market_share': 25, 'price_modifier': 1.0},
        'HP': {'market_share': 20, 'price_modifier': 1.1},
        'Dell': {'market_share': 15, 'price_modifier': 1.15},
        'Lenovo': {'market_share': 15, 'price_modifier': 0.95},
        'Acer': {'market_share': 10, 'price_modifier': 0.85},
        'MSI': {'market_share': 5, 'price_modifier': 1.3},
        'Apple': {'market_share': 5, 'price_modifier': 2.0},
        'Razer': {'market_share': 3, 'price_modifier': 1.8},
        'Samsung': {'market_share': 2, 'price_modifier': 1.2}
    }
    
    # Laptop categories with typical Sri Lankan pricing (in LKR)
    categories = {
        'Budget Office': {
            'base_price_range': (45000, 85000),
            'specs': {
                'processors': ['Intel Celeron N4000', 'Intel Pentium Silver N5000', 'AMD A4-9120', 'Intel Core i3-10110U'],
                'ram': ['4GB DDR4', '8GB DDR4'],
                'storage': ['128GB SSD', '256GB SSD', '500GB HDD', '1TB HDD'],
                'screen': ['14" HD', '15.6" HD', '14" FHD'],
                'graphics': ['Intel UHD Graphics', 'AMD Radeon Graphics']
            }
        },
        'Business Professional': {
            'base_price_range': (85000, 180000),
            'specs': {
                'processors': ['Intel Core i5-1135G7', 'Intel Core i5-11320H', 'AMD Ryzen 5 5500U', 'Intel Core i7-1165G7'],
                'ram': ['8GB DDR4', '16GB DDR4'],
                'storage': ['256GB SSD', '512GB SSD', '256GB SSD + 1TB HDD'],
                'screen': ['14" FHD IPS', '15.6" FHD IPS', '13.3" FHD IPS'],
                'graphics': ['Intel Iris Xe Graphics', 'AMD Radeon Graphics', 'NVIDIA MX450 2GB']
            }
        },
        'Gaming Entry': {
            'base_price_range': (180000, 300000),
            'specs': {
                'processors': ['Intel Core i5-11400H', 'AMD Ryzen 5 5600H', 'Intel Core i7-11800H', 'AMD Ryzen 7 5800H'],
                'ram': ['8GB DDR4', '16GB DDR4'],
                'storage': ['512GB SSD', '1TB SSD', '512GB SSD + 1TB HDD'],
                'screen': ['15.6" FHD 120Hz', '15.6" FHD 144Hz', '17.3" FHD 120Hz'],
                'graphics': ['NVIDIA GTX 1650 4GB', 'NVIDIA RTX 3050 4GB', 'NVIDIA GTX 1660Ti 6GB']
            }
        },
        'Gaming High-End': {
            'base_price_range': (300000, 500000),
            'specs': {
                'processors': ['Intel Core i7-12700H', 'AMD Ryzen 7 5800H', 'Intel Core i9-11900H', 'AMD Ryzen 9 5900HX'],
                'ram': ['16GB DDR4', '32GB DDR4', '16GB DDR5'],
                'storage': ['1TB SSD', '2TB SSD', '1TB SSD + 2TB HDD'],
                'screen': ['15.6" FHD 165Hz', '17.3" FHD 144Hz', '15.6" QHD 165Hz'],
                'graphics': ['NVIDIA RTX 3060 6GB', 'NVIDIA RTX 3070 8GB', 'NVIDIA RTX 4050 6GB']
            }
        },
        'Premium Ultrabook': {
            'base_price_range': (200000, 450000),
            'specs': {
                'processors': ['Intel Core i5-1240P', 'Intel Core i7-1260P', 'AMD Ryzen 7 5800U', 'Apple M1', 'Apple M2'],
                'ram': ['8GB DDR4', '16GB DDR4', '16GB DDR5', '8GB Unified', '16GB Unified'],
                'storage': ['512GB SSD', '1TB SSD', '2TB SSD'],
                'screen': ['13.3" FHD IPS', '14" FHD IPS', '15.6" 4K OLED', '13.3" Retina', '14.2" Liquid Retina XDR'],
                'graphics': ['Intel Iris Xe Graphics', 'AMD Radeon Graphics', 'Apple GPU']
            }
        },
        'Workstation': {
            'base_price_range': (350000, 800000),
            'specs': {
                'processors': ['Intel Core i7-12800H', 'Intel Core i9-12900H', 'AMD Ryzen 9 5950H', 'Intel Xeon W-11955M'],
                'ram': ['32GB DDR4', '64GB DDR4', '32GB DDR5'],
                'storage': ['1TB SSD', '2TB SSD', '4TB SSD'],
                'screen': ['15.6" 4K IPS', '17.3" 4K IPS', '16" 4K IPS'],
                'graphics': ['NVIDIA RTX A2000 4GB', 'NVIDIA RTX 3080 8GB', 'NVIDIA RTX A3000 6GB']
            }
        }
    }
    
    model_series = {
        'ASUS': ['VivoBook', 'ZenBook', 'TUF Gaming', 'ROG Strix', 'ROG Zephyrus', 'ProArt'],
        'HP': ['Pavilion', 'Envy', 'Spectre', 'Omen', 'EliteBook', 'ZBook'],
        'Dell': ['Inspiron', 'XPS', 'Latitude', 'Precision', 'G Series', 'Alienware'],
        'Lenovo': ['IdeaPad', 'ThinkPad', 'Legion', 'Yoga', 'ThinkBook'],
        'Acer': ['Aspire', 'Swift', 'Nitro', 'Predator', 'ConceptD'],
        'MSI': ['Modern', 'Prestige', 'GF', 'GP', 'GE', 'GT'],
        'Apple': ['MacBook Air', 'MacBook Pro'],
        'Razer': ['Blade', 'Book'],
        'Samsung': ['Galaxy Book', 'Notebook']
    }
    
    laptops = []
    
    # Generate 20 laptops
    for i in range(20):
        # Select brand based on market share
        brand_weights = [(brand, data['market_share']) for brand, data in brands.items()]
        brand = random.choices([b[0] for b in brand_weights], [b[1] for b in brand_weights])[0]
        
        # Select category (more budget and business laptops in Sri Lankan market)
        category_weights = [
            ('Budget Office', 30),
            ('Business Professional', 25), 
            ('Gaming Entry', 20),
            ('Premium Ultrabook', 10),
            ('Gaming High-End', 10),
            ('Workstation', 5)
        ]
        category = random.choices([c[0] for c in category_weights], [c[1] for c in category_weights])[0]
        
        # Generate specifications
        specs = categories[category]['specs']
        processor = random.choice(specs['processors'])
        ram = random.choice(specs['ram'])
        storage = random.choice(specs['storage'])
        screen = random.choice(specs['screen'])
        graphics = random.choice(specs['graphics'])
        
        # Generate model name
        series = random.choice(model_series[brand])
        model_number = random.randint(1000, 9999) if brand != 'Apple' else random.choice(['M1', 'M2'])
        model_suffix = random.choice(['', 'Pro', 'Plus', 'X', 'S', 'Ultra']) if brand != 'Apple' else ''
        
        product_name = f"{brand} {series} {model_number}{model_suffix}"
        if brand == 'Apple':
            product_name = f"{brand} {series} {model_number}"
        
        # Calculate realistic price in LKR
        base_price_min, base_price_max = categories[category]['base_price_range']
        base_price = random.randint(base_price_min, base_price_max)
        brand_modifier = brands[brand]['price_modifier']
        
        # Add some market variation (-10% to +15%)
        market_variation = random.uniform(0.9, 1.15)
        final_price = int(base_price * brand_modifier * market_variation)
        
        # Create features JSON
        features = {
            'category': category,
            'processor': processor,
            'ram': ram,
            'storage': storage,
            'display': screen,
            'graphics': graphics,
            'brand': brand,
            'series': series,
            'color': random.choice(['Black', 'Silver', 'White', 'Blue', 'Red', 'Gold']),
            'weight': f"{random.uniform(1.2, 3.5):.1f}kg",
            'battery': f"{random.randint(4, 12)} hours",
            'warranty': random.choice(['1 Year', '2 Years', '3 Years']),
            'origin': random.choice(['USA', 'China', 'Taiwan', 'South Korea']),
            'availability': random.choice(['In Stock', 'Limited Stock', 'Pre-Order'])
        }
        
        # Add time variation (products added over last 6 months)
        days_ago = random.randint(0, 180)
        update_time = datetime.now() - timedelta(days=days_ago)
        
        laptop = {
            'product_name': product_name,
            'price': final_price,
            'features': json.dumps(features),
            'update_time': update_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        laptops.append(laptop)
    
    return laptops

def populate_database(db_path='app/data.db'):
    """Populate the database with laptop data"""
    
    # Generate laptop data
    print("Generating 20 realistic Sri Lankan laptop products...")
    laptops = create_realistic_laptop_data()
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM market_data')
    cursor.execute('DELETE FROM pricing_list')
    
    print("Inserting products into market_data table...")
    
    # Insert market data
    for laptop in laptops:
        cursor.execute('''
            INSERT INTO market_data (product_name, price, features, update_time)
            VALUES (?, ?, ?, ?)
        ''', (laptop['product_name'], laptop['price'], laptop['features'], laptop['update_time']))
    
    print("Creating optimized pricing entries...")
    
    # Create corresponding pricing_list entries with optimization suggestions
    optimization_reasons = [
        "Market analysis suggests 5% price reduction",
        "Competitor pricing adjustment needed",
        "Inventory clearance optimization",
        "Seasonal demand adjustment",
        "Premium positioning strategy",
        "Bundle pricing opportunity",
        "Stock level optimization",
        "Market penetration pricing",
        "Value-based pricing adjustment",
        "Dynamic demand-based pricing"
    ]
    
    for laptop in laptops:
        # Generate optimized price (typically -10% to +5% of market price)
        optimization_factor = random.uniform(0.9, 1.05)
        optimized_price = int(laptop['price'] * optimization_factor)
        reason = random.choice(optimization_reasons)
        
        cursor.execute('''
            INSERT INTO pricing_list (product_name, optimized_price, reason)
            VALUES (?, ?, ?)
        ''', (laptop['product_name'], optimized_price, reason))
    
    # Commit changes
    conn.commit()
    
    # Print summary
    cursor.execute('SELECT COUNT(*) FROM market_data')
    market_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM pricing_list')
    pricing_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(price), MAX(price), AVG(price) FROM market_data')
    price_stats = cursor.fetchone()
    
    print(f"\nDATABASE POPULATED SUCCESSFULLY!")
    print(f"Market Data: {market_count} products")
    print(f"Pricing List: {pricing_count} entries")
    print(f"Price Range: LKR {price_stats[0]:,.0f} - LKR {price_stats[1]:,.0f}")
    print(f"Average Price: LKR {price_stats[2]:,.0f}")
    
    # Show sample products by category
    print(f"\nSample Products by Category:")
    cursor.execute('''
        SELECT product_name, price, json_extract(features, '$.category') as category
        FROM market_data 
        ORDER BY category, price 
        LIMIT 10
    ''')
    
    for product_name, price, category in cursor.fetchall():
        print(f"  * {category}: {product_name} - LKR {price:,.0f}")
    
    conn.close()
    print(f"\nReady to test with FluxPricer AI!")
    print(f"Try asking: 'What laptops do we have under LKR 100,000?'")

if __name__ == "__main__":
    populate_database()