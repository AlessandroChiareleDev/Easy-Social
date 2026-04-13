import psycopg2, psycopg2.extras

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) pipeline_runs
cur.execute("SELECT id, per_apur, status, total_cpfs, cpfs_ok, cpfs_erro, cpfs_ignorados, lote_atual, total_lotes FROM pipeline_runs ORDER BY id DESC LIMIT 5")
print('=== PIPELINE_RUNS ===')
for r in cur.fetchall():
    print(f'  run#{r["id"]} per={r["per_apur"]} status={r["status"]} total={r["total_cpfs"]} ok={r["cpfs_ok"]} erro={r["cpfs_erro"]} ign={r["cpfs_ignorados"]} lote={r["lote_atual"]}/{r["total_lotes"]}')

# 2) pipeline_cpf_results - contagem por status
cur.execute("SELECT run_id, status, COUNT(*) as cnt FROM pipeline_cpf_results GROUP BY run_id, status ORDER BY run_id DESC, status")
print('\n=== PIPELINE_CPF_RESULTS por run/status ===')
for r in cur.fetchall():
    print(f'  run#{r["run_id"]} {r["status"]}: {r["cnt"]}')

# 3) CPFs com erro - agrupar por erro_descricao
cur.execute("""
    SELECT run_id, 
           SUBSTRING(erro_descricao FROM 1 FOR 80) as erro_trunc, 
           COUNT(*) as cnt
    FROM pipeline_cpf_results 
    WHERE status = 'erro'
    GROUP BY run_id, erro_trunc
    ORDER BY run_id DESC, cnt DESC
""")
print('\n=== ERROS AGRUPADOS ===')
for r in cur.fetchall():
    print(f'  run#{r["run_id"]} [{r["cnt"]}x]: {r["erro_trunc"]}')

# 4) Checar se os 50 CPFs corrigidos do erro 8 mudaram de status
cur.execute("""
    SELECT status, COUNT(*) as cnt
    FROM pipeline_cpf_results 
    WHERE erro_descricao LIKE '%459%' OR erro_descricao LIKE '%recibo%retifica%'
    GROUP BY status
""")
print('\n=== CPFs com erro 459 (status atual) ===')
for r in cur.fetchall():
    print(f'  {r["status"]}: {r["cnt"]}')

# 5) Checar CPFs com penAlim/erro 8
cur.execute("""
    SELECT status, COUNT(*) as cnt
    FROM pipeline_cpf_results 
    WHERE erro_descricao LIKE '%8%' OR erro_descricao LIKE '%penAlim%' OR erro_descricao LIKE '%pensao%' OR erro_descricao LIKE '%pens%'
    GROUP BY status
""")
print('\n=== CPFs com erro 8 / pensão (status atual) ===')
for r in cur.fetchall():
    print(f'  {r["status"]}: {r["cnt"]}')

conn.close()
