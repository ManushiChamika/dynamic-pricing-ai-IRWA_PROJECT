import sqlite3

conn = sqlite3.connect('data/chat.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title FROM threads WHERE id = 429')
result = cursor.fetchone()
if result:
    print(f'Thread 429 - ID: {result[0]}, Title: {result[1]}')
else:
    print('Thread 429 not found')
    cursor.execute('SELECT id, title FROM threads ORDER BY id DESC LIMIT 5')
    print('\nRecent threads:')
    for row in cursor.fetchall():
        print(f'  Thread {row[0]} - Title: {row[1]}')
conn.close()
