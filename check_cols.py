import sys
import psycopg2
import json
sys.path.append(r'C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend')
from app import tenant
cfg = tenant.get_db_config_for_empresa(2)
conn = psycopg2.connect(**{k: v for k, v in cfg.items() if k != 'search_path'})
cur = conn.cursor()
if 'search_path' in cfg: cur.execute(f"SET search_path TO {cfg['search_path']}")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'timeline_envio_item'")
print(json.dumps([r[0] for r in cur.fetchall()]))
