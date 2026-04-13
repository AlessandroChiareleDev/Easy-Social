"""Investigate error 459 CPFs - understand the situation."""
import psycopg2, psycopg2.extras, json

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1) Listar os 44 CPFs com erro 459
cur.execute("""
    SELECT cpf, nr_recibo_original, nr_recibo_novo, erro_descricao, lote_num, processed_at
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND status = 'erro' AND erro_descricao LIKE '%459%'
    ORDER BY cpf
""")
rows = cur.fetchall()
print(f'=== {len(rows)} CPFs COM ERRO 459 ===')
for r in rows:
    print(f'  CPF={r["cpf"]} recibo_orig={r["nr_recibo_original"]} recibo_novo={r["nr_recibo_novo"]} lote={r["lote_num"]}')

# 2) Para esses CPFs, ver se existem eventos no explorador que mostrem retificação bem-sucedida
cpfs_459 = [r["cpf"] for r in rows]
if cpfs_459:
    # Check columns first
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='explorador_eventos' ORDER BY ordinal_position")
    cols = [r["column_name"] for r in cur.fetchall()]
    print(f'\n=== COLUNAS explorador_eventos: {cols} ===')

    # Checar no explorador_eventos se há S-1210 para esses CPFs
    cur.execute("""
        SELECT cpf, tipo_evento, nr_recibo, per_apur, arquivo_origem, dados_json
        FROM explorador_eventos
        WHERE cpf = ANY(%s) AND tipo_evento = 'S-1210' AND per_apur = '2025-09'
        ORDER BY cpf, id DESC
    """, (cpfs_459,))
    evts = cur.fetchall()
    print(f'\n=== EVENTOS S-1210 (explorador) para esses CPFs: {len(evts)} ===')
    for e in evts[:10]:
        dj = e.get("dados_json") or {}
        ind = dj.get("indRetif") if isinstance(dj, dict) else None
        print(f'  CPF={e["cpf"]} recibo={e["nr_recibo"]} indRetif={ind} arq={e["arquivo_origem"]}')
    if len(evts) > 10:
        print(f'  ... +{len(evts)-10} mais')

    # Sample CPF - all events
    sample_cpf = cpfs_459[0]
    cur.execute("""
        SELECT id, cpf, tipo_evento, nr_recibo, per_apur, arquivo_origem
        FROM explorador_eventos
        WHERE cpf = %s
        ORDER BY id
    """, (sample_cpf,))
    sample = cur.fetchall()
    print(f'\n=== TODOS EVENTOS para CPF {sample_cpf} ===')
    for e in sample:
        print(f'  id={e["id"]} tipo={e["tipo_evento"]} recibo={e["nr_recibo"]} arq={e["arquivo_origem"]}')

conn.close()
