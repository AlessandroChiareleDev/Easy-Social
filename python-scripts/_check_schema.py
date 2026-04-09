"""Temp script to check local DB schema on VPS."""
import psycopg2
from db_config import LOCAL_DB_CONFIG
print('LOCAL_DB_CONFIG:', {k:v for k,v in LOCAL_DB_CONFIG.items() if k != 'password'})
conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
for t in tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", (t,))
    cols = [r[0] for r in cur.fetchall()]
    print(f'  {t}: {cols}')
conn.close()
