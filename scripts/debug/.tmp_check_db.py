import sqlite3

conn = sqlite3.connect(r'C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\app\data.db')
cursor = conn.execute('SELECT COUNT(*) FROM product_catalog')
print(f'Product catalog rows: {cursor.fetchone()[0]}')

cursor = conn.execute('SELECT sku, owner_id, current_price FROM product_catalog LIMIT 5')
print('Sample products:')
for row in cursor.fetchall():
    print(f'  {row}')

cursor = conn.execute('SELECT DISTINCT owner_id FROM product_catalog')
print('\nDistinct owner_ids:')
for row in cursor.fetchall():
    print(f'  {row[0]}')

conn.close()

print('\n--- Alert DB ---')
conn2 = sqlite3.connect(r'C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\app\alert.db')
cursor2 = conn2.execute('SELECT COUNT(*) FROM incidents')
print(f'Incident count: {cursor2.fetchone()[0]}')

cursor2 = conn2.execute('SELECT id, rule_id, sku, status, severity, owner_id FROM incidents LIMIT 5')
print('Sample incidents:')
for row in cursor2.fetchall():
    print(f'  {row}')

conn2.close()
