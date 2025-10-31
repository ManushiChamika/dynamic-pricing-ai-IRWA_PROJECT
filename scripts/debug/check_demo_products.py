import sqlite3

conn = sqlite3.connect('app/data.db')
cursor = conn.cursor()

cursor.execute('SELECT sku, title, owner_id FROM product_catalog WHERE owner_id = 16 LIMIT 5')
products = cursor.fetchall()
print('Products:')
for p in products:
    print(f'  {p}')

cursor.execute('SELECT COUNT(*) FROM product_catalog WHERE owner_id = 16')
count = cursor.fetchone()
print(f'\nTotal products for demo user: {count[0]}')

conn.close()
