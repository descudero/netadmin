import sqlite3 as sql

conn = sql.connect('example.db')
c = conn.cursor()

# Save (commit) the changes
t = ('RHAT',)
c.execute('SELECT * FROM stocks WHERE symbol=?', t)
print(c.fetchone())
# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
