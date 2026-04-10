import psycopg2, psycopg2.extras, json, sys
sys.path.insert(0, "/opt/easy-social/python-scripts")
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    cur.execute("SELECT id, pasta, periodo, total_arquivos, importado_em FROM explorador_importacoes ORDER BY id DESC LIMIT 10")
    for r in cur.fetchall():
        print(json.dumps(dict(r), default=str))
conn.close()
