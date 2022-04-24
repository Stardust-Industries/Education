import sqlite3

connection = sqlite3.connect('users.db')
cursor = connection.cursor()

preferred_username = 'user8892766848@cms.k12.nc.us'

userName = preferred_username.replace('@', 'AT').replace('.', 'DOT')

i = 0

for x in cursor.execute('SELECT * FROM ' + userName):
  i += 1
  print(x[i])