"""Mark 44 CPFs with error [459] as OK - they were already retified by lote 28."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Mark as OK
cur.execute("""
    UPDATE pipeline_cpf_results
    SET status = 'ok', 
        erro_descricao = NULL,
        processed_at = NOW()
    WHERE run_id = 1 AND status = 'erro' AND erro_descricao LIKE '%%459%%'
    RETURNING cpf
""")
updated = cur.fetchall()
print(f"Marked {len(updated)} CPFs as OK")

# Update pipeline_runs counts
cur.execute("""
    UPDATE pipeline_runs SET
        cpfs_ok = (SELECT COUNT(*) FROM pipeline_cpf_results WHERE run_id = 1 AND status = 'ok'),
        cpfs_erro = (SELECT COUNT(*) FROM pipeline_cpf_results WHERE run_id = 1 AND status = 'erro')
    WHERE id = 1
    RETURNING cpfs_ok, cpfs_erro
""")
row = cur.fetchone()
conn.commit()
print(f"Dashboard: OK={row[0]}, Erro={row[1]}")
conn.close()
