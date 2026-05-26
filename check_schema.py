import psycopg2
from psycopg2 import extras
conn_str_remote = "postgresql://postgres:EsoV2_CoxRHWQ1z6iucG7ZyvdqFIbN@db.kjbgiwnlvqnrfdozjvhq.supabase.co:5432/postgres?sslmode=require"
conn = psycopg2.connect(conn_str_remote)
cur = conn.cursor(cursor_factory=extras.RealDictCursor)
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name LIKE 'timeline%' OR table_name LIKE 'explorador%'")
for r in cur.fetchall():
    print(r)
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'timeline_envio' AND table_schema = 'solucoes'")
for r in cur.fetchall():
    print(f"timeline_envio col: {r['column_name']}")
conn.close()
