import sys
sys.path.insert(0, "/opt/easy-social/python-scripts")
from db_config import DB_CONFIG
import psycopg2

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()
cur.execute("DELETE FROM explorador_importacoes WHERE id = 41 RETURNING id")
r = cur.fetchone()
conn.commit()
print(f"Deleted import: {r}")
cur.execute("SELECT COUNT(*) FROM explorador_eventos")
print(f"Remaining events: {cur.fetchone()[0]}")
conn.close()
