"""Checar os erros que existiam no pipeline_cpf_results — os 3 tipos de problema."""
import psycopg2, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

# 1) Pipeline runs
print("=" * 60)
print("PIPELINE RUNS")
print("=" * 60)
cur.execute("SELECT * FROM pipeline_runs ORDER BY id")
cols = [d[0] for d in cur.description]
for r in cur.fetchall():
    row = dict(zip(cols, r))
    print(f"  run={row['id']} per={row['per_apur']} status={row['status']} "
          f"total={row['total_cpfs']} ok={row.get('cpfs_ok')} erro={row.get('cpfs_erro')}")

# 2) Status breakdown
print("\n" + "=" * 60)
print("STATUS BREAKDOWN in pipeline_cpf_results")
print("=" * 60)
cur.execute("""
    SELECT status, COUNT(*)
    FROM pipeline_cpf_results
    GROUP BY status
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 3) Error types
print("\n" + "=" * 60)
print("TIPOS DE ERRO (agrupado por erro_descricao)")
print("=" * 60)
cur.execute("""
    SELECT SUBSTRING(erro_descricao FROM 1 FOR 120) as erro_tipo, COUNT(*) as qtd
    FROM pipeline_cpf_results
    WHERE status = 'erro' OR erro_descricao IS NOT NULL
    GROUP BY SUBSTRING(erro_descricao FROM 1 FOR 120)
    ORDER BY qtd DESC
    LIMIT 20
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  [{r[1]:4d}] {r[0]}")
else:
    print("  Nenhum erro!")

# 4) Check if any are 'pendente' still
cur.execute("""
    SELECT COUNT(*) FROM pipeline_cpf_results WHERE status = 'pendente'
""")
pend = cur.fetchone()[0]
print(f"\nPendentes: {pend}")

# 5) Sample CPFs with errors
print("\n" + "=" * 60)
print("SAMPLE CPFs COM ERRO (5 por tipo)")
print("=" * 60)
cur.execute("""
    SELECT DISTINCT ON (SUBSTRING(erro_descricao FROM 1 FOR 80))
        cpf, status, erro_descricao, lote_num
    FROM pipeline_cpf_results
    WHERE erro_descricao IS NOT NULL
    ORDER BY SUBSTRING(erro_descricao FROM 1 FOR 80), cpf
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"  CPF={r[0]} status={r[1]} lote={r[3]}")
    print(f"    erro: {r[2][:200]}")

# 6) Check the old progress file
print("\n" + "=" * 60)
print("PROGRESS FILE")
print("=" * 60)
import os
progress_file = "/tmp/pipeline_batch_202509_progress.json"
if os.path.exists(progress_file):
    with open(progress_file) as f:
        prog = json.load(f)
    print(f"  cpfs_ok: {len(prog.get('cpfs_ok', []))}")
    print(f"  cpfs_erro: {len(prog.get('cpfs_erro', {}))}")
    print(f"  s1298_done: {prog.get('s1298_done')}")
    print(f"  s1299_done: {prog.get('s1299_done')}")
    print(f"  run_id: {prog.get('run_id')}")
    # Print error types from progress
    erros = prog.get("cpfs_erro", {})
    if erros:
        from collections import Counter
        tipo_counter = Counter()
        for cpf, desc in erros.items():
            key = desc[:100]
            tipo_counter[key] += 1
        print(f"\n  Tipos de erro no progress file:")
        for tipo, cnt in tipo_counter.most_common():
            print(f"    [{cnt:4d}] {tipo}")
else:
    print("  Arquivo não encontrado!")

# 7) Check result file
result_file = "/tmp/pipeline_batch_202509_result.json"
if os.path.exists(result_file):
    with open(result_file) as f:
        res = json.load(f)
    print(f"\n  Result file: {list(res.keys())}")
else:
    print(f"\n  Result file não encontrado!")

conn.close()
