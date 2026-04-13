"""SOMENTE LEITURA - listar 95 CPFs sem S-1210 e seus erros."""
import psycopg2, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

# CPFs com S-1200 mas SEM S-1210
cur.execute("""
    SELECT DISTINCT e1200.cpf
    FROM explorador_eventos e1200
    LEFT JOIN explorador_eventos e1210
        ON e1200.cpf = e1210.cpf
        AND e1210.per_apur = '2025-09'
        AND e1210.tipo_evento = 'S-1210'
    WHERE e1200.per_apur = '2025-09'
      AND e1200.tipo_evento = 'S-1200'
      AND e1210.cpf IS NULL
    ORDER BY e1200.cpf
""")
cpfs = [r[0] for r in cur.fetchall()]
print(f"Total CPFs com S-1200 sem S-1210: {len(cpfs)}")

# Checar pipeline_cpf_results pra esses CPFs
if cpfs:
    cur.execute("""
        SELECT cpf, status, nr_recibo_original, nr_recibo_novo, lote_num, processed_at,
               pagamentos, info_ir_cr
        FROM pipeline_cpf_results
        WHERE cpf = ANY(%s)
        ORDER BY cpf
    """, (cpfs,))
    rows = cur.fetchall()
    print(f"\npipeline_cpf_results encontrados: {len(rows)}")
    
    status_count = {}
    for r in rows:
        st = r[1] or "NULL"
        status_count[st] = status_count.get(st, 0) + 1
    print(f"Status breakdown: {status_count}")
    
    print(f"\n{'CPF':<15} {'STATUS':<15} {'RECIBO_ORIG':<30} {'RECIBO_NOVO':<30} {'LOTE':<6}")
    print("-" * 100)
    for r in rows:
        cpf, status, rec_orig, rec_novo, lote, proc_at, pgtos, ir = r
        print(f"{cpf:<15} {str(status):<15} {str(rec_orig or '-'):<30} {str(rec_novo or '-'):<30} {str(lote or '-'):<6}")

# CPFs sem pipeline_cpf_results
cpfs_in_pipeline = set()
if cpfs:
    cur.execute("""
        SELECT DISTINCT cpf FROM pipeline_cpf_results WHERE cpf = ANY(%s)
    """, (cpfs,))
    cpfs_in_pipeline = {r[0] for r in cur.fetchall()}

cpfs_sem_pipeline = [c for c in cpfs if c not in cpfs_in_pipeline]
if cpfs_sem_pipeline:
    print(f"\nCPFs SEM registro em pipeline_cpf_results: {len(cpfs_sem_pipeline)}")
    for c in cpfs_sem_pipeline:
        print(f"  {c}")

# Checar se tem erros no pipeline_errors ou similar
try:
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%error%' OR table_name LIKE '%log%' OR table_name LIKE '%fail%'
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    if tables:
        print(f"\nTabelas de erro/log: {[t[0] for t in tables]}")
except:
    pass

# Checar pipeline_errors se existe
try:
    cur.execute("SELECT COUNT(*) FROM pipeline_errors WHERE cpf = ANY(%s)", (cpfs,))
    errs = cur.fetchone()[0]
    print(f"\npipeline_errors para esses CPFs: {errs}")
    if errs > 0:
        cur.execute("""
            SELECT cpf, error_message, step, created_at
            FROM pipeline_errors
            WHERE cpf = ANY(%s)
            ORDER BY cpf
        """, (cpfs,))
        for r in cur.fetchall():
            print(f"  {r[0]} step={r[2]} err={str(r[1])[:120]} em {r[3]}")
except Exception as e:
    print(f"\npipeline_errors: {e}")

# Checar pipeline_lote_results se existe
try:
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'pipeline_lote_results' ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    if cols:
        print(f"\npipeline_lote_results cols: {cols}")
except:
    pass

conn.close()
print("\nNADA alterado.")
