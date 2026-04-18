import sqlite3
conn = sqlite3.connect('data/transmissoes.db')
c = conn.cursor()
c.execute('SELECT evento, tipo_transmissao FROM transmissoes WHERE evento LIKE "%Corneto%"')
for row in c.fetchall():
    print(f"Evento: {row[0]} | Tipo: {row[1]}")
conn.close()
