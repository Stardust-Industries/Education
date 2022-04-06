import sqlite3

connection = sqlite3.connect('classes.db')
cursor = connection.cursor()

cursor.execute('SELECT * FROM BLWRcWgxEr')
print(str(cursor.fetchall()))