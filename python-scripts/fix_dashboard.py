"""Fix pipeline_runs dashboard counts to match actual pipeline_cpf_results."""
import psycopg2

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor()

cur.execute("""
    UPDATE pipeline_runs SET
        cpfs_ok = (SELECT COUNT(*) FROM pipeline_cpf_results WHERE run_id = 1 AND status = 'ok'),
        cpfs_erro = (SELECT COUNT(*) FROM pipeline_cpf_results WHERE run_id = 1 AND status = 'erro')
    WHERE id = 1
    RETURNING cpfs_ok, cpfs_erro
""")
row = cur.fetchone()
conn.commit()
print(f'Atualizado pipeline_runs: ok={row[0]}, erro={row[1]}, total={row[0]+row[1]}')
conn.close()
