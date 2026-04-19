import sqlite3

conn = sqlite3.connect('trading.db')

print("=== ORDERS ===")
cursor = conn.execute('SELECT * FROM orders')
for row in cursor:
    print(row)

print("\n=== TRADES ===")
cursor = conn.execute('SELECT * FROM trades')
for row in cursor:
    print(row)

conn.close()