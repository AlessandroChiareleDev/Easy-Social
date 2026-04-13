import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM pipeline_cpf_results WHERE status = 'erro' AND erro_descricao LIKE '%%1955%%'")
print(f"CPFs with 1955 error: {cur.fetchone()[0]}")
cur.execute("SELECT count(*) FROM pipeline_cpf_results WHERE status = 'erro' AND erro_descricao LIKE '%%REENVIO-1955%%'")
print(f"CPFs with REENVIO-1955: {cur.fetchone()[0]}")
conn.close()
