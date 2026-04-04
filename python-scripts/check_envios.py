import psycopg2
from db_config import LOCAL_DB_CONFIG

conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()

# Check esocial_envios columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='esocial_envios'")
cols = [r[0] for r in cur.fetchall()]
print(f"Colunas esocial_envios: {cols}")

# Check for CPF data
if 'cpf' in cols:
    cur.execute("SELECT * FROM esocial_envios WHERE cpf = '08132588983' ORDER BY created_at DESC LIMIT 5")
elif 'xml_evento' in cols:
    cur.execute("SELECT * FROM esocial_envios WHERE xml_evento LIKE '%08132588983%' ORDER BY created_at DESC LIMIT 5")
else:
    cur.execute("SELECT * FROM esocial_envios LIMIT 3")

rows = cur.fetchall()
col_names = [d[0] for d in cur.description]
print(f"\nesocial_envios: {len(rows)} registros encontrados")
for r in rows:
    d = dict(zip(col_names, r))
    # Truncate long values
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 200:
            d[k] = v[:200] + "..."
    print(f"  {d}")

conn.close()
