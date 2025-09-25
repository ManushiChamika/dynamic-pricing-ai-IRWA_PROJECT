import sqlite3

conn = sqlite3.connect('market.db')

print('=== DATABASE VERIFICATION ===')
print('Total products:', conn.execute('SELECT COUNT(*) FROM market_data').fetchone()[0])
print('Budget laptops (<100k LKR):', conn.execute('SELECT COUNT(*) FROM market_data WHERE price < 100000').fetchone()[0])
print('Gaming laptops (>200k LKR):', conn.execute('SELECT COUNT(*) FROM market_data WHERE price > 200000').fetchone()[0])

print('\n=== CHEAPEST LAPTOPS ===')
for row in conn.execute('SELECT product_name, price FROM market_data ORDER BY price LIMIT 5').fetchall():
    print(f'  {row[0]} - LKR {row[1]:,}')

print('\n=== MOST EXPENSIVE LAPTOPS ===')
for row in conn.execute('SELECT product_name, price FROM market_data ORDER BY price DESC LIMIT 5').fetchall():
    print(f'  {row[0]} - LKR {row[1]:,}')

print('\n=== BRANDS DISTRIBUTION ===')
for row in conn.execute('''
    SELECT json_extract(features, '$.brand') as brand, COUNT(*) as count 
    FROM market_data 
    GROUP BY brand 
    ORDER BY count DESC
''').fetchall():
    print(f'  {row[0]}: {row[1]} laptops')

conn.close()
print('\n✅ Database ready for FluxPricer AI!')