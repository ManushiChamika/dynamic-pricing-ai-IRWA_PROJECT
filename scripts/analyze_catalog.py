import sqlite3
from pathlib import Path
from typing import Dict, Any

def get_db_path():
    root = Path(__file__).resolve().parents[1]
    return root / "app" / "data.db"

def analyze_catalog():
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sku, title, currency, current_price, cost, stock, updated_at
        FROM product_catalog
        ORDER BY sku
    """)
    
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        print("No products found in catalog")
        return
    
    products_dict: Dict[str, Any] = {}
    for product in products:
        sku = product['sku']
        if sku not in products_dict:
            products_dict[sku] = {
                'sku': sku,
                'title': product['title'],
                'currency': product['currency'],
                'current_price': product['current_price'],
                'cost': product['cost'],
                'stock': product['stock'],
            }
    
    unique_products = list(products_dict.values())
    
    print(f"\n{'='*120}")
    print(f"CATALOG ANALYSIS - {len(unique_products)} Unique Products Found")
    print(f"{'='*120}\n")
    
    low_margin_products = []
    
    print(f"{'SKU':<30} | {'Title':<30} | {'Currency':<8} | {'Price':>10} | {'Cost':>10} | {'Profit':>10} | {'Margin':>8} | {'Stock':>8} | Status")
    print("-" * 140)
    
    for product in unique_products:
        sku = product['sku'][:30]
        title = product['title'][:30] if product['title'] else 'N/A'
        currency = product['currency'] or 'N/A'
        current_price = product['current_price'] or 0
        cost = product['cost'] or 0
        stock = product['stock'] or 0
        
        profit = current_price - cost
        
        if current_price > 0:
            margin_pct = (profit / current_price) * 100
        else:
            margin_pct = 0
        
        margin_status = "OK"
        if margin_pct < 10:
            margin_status = "LOW"
            low_margin_products.append({
                'sku': product['sku'],
                'title': product['title'],
                'current_price': current_price,
                'cost': cost,
                'margin_pct': margin_pct,
                'profit': profit
            })
        elif margin_pct < 20:
            margin_status = "CAUTION"
        
        print(f"{sku:<30} | {title:<30} | {currency:<8} | ${current_price:>9.2f} | ${cost:>9.2f} | ${profit:>9.2f} | {margin_pct:>7.1f}% | {stock:>8.0f} | {margin_status}")
    
    if low_margin_products:
        print(f"\n{'='*120}")
        print(f"⚠️  PRODUCTS WITH LOW PROFIT MARGINS (< 10%): {len(low_margin_products)}")
        print(f"{'='*120}\n")
        
        print(f"{'SKU':<30} | {'Title':<40} | {'Selling Price':>12} | {'Cost':>10} | {'Profit':>10} | {'Margin %':>10}")
        print("-" * 125)
        
        for p in low_margin_products:
            title_short = p['title'][:40] if p['title'] else 'N/A'
            print(f"{p['sku']:<30} | {title_short:<40} | ${p['current_price']:>11.2f} | ${p['cost']:>9.2f} | ${p['profit']:>9.2f} | {p['margin_pct']:>9.1f}%")
        
        print("\nRECOMMENDATIONS FOR LOW MARGIN PRODUCTS:")
        print("• Consider increasing prices on these products to improve margins")
        print("• Review competitor pricing to ensure competitiveness")
        print("• Negotiate with suppliers to reduce costs")
        print("• Evaluate demand elasticity before price increases")
    
    total_value = sum(p['current_price'] * p['stock'] for p in unique_products if p['current_price'] and p['stock'])
    total_cost_value = sum(p['cost'] * p['stock'] for p in unique_products if p['cost'] and p['stock'])
    total_potential_profit = total_value - total_cost_value
    
    margin_products = [p for p in unique_products if p['current_price'] and p['current_price'] > 0]
    avg_margin = sum((p['current_price'] - p['cost']) / p['current_price'] * 100 for p in margin_products) / len(margin_products) if margin_products else 0
    
    print(f"\n{'='*120}")
    print("CATALOG SUMMARY")
    print(f"{'='*120}")
    print(f"Total Unique Products: {len(unique_products)}")
    print(f"Total Inventory Value (at selling price): ${total_value:,.2f}")
    print(f"Total Inventory Cost: ${total_cost_value:,.2f}")
    print(f"Total Potential Profit (if all sold): ${total_potential_profit:,.2f}")
    print(f"Average Profit Margin: {avg_margin:.1f}%")
    print(f"{'='*120}\n")

if __name__ == "__main__":
    analyze_catalog()

if __name__ == "__main__":
    analyze_catalog()
