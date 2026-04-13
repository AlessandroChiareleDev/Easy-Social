"""
Investigate error 1955 CPFs - check their state.
These CPFs failed because IR rubrica sum was negative. 
User fixed S-1010 (changed 571→33, 572→32). 
Now we need to re-send S-1210 retification.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get error 1955 CPFs
cur.execute("""
    SELECT cpf, nr_recibo_original, erro_descricao
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND status = 'erro'
    ORDER BY cpf
""")
rows = cur.fetchall()
print(f"Total remaining errors: {len(rows)}")

erro_1955 = [r for r in rows if '1955' in (r['erro_descricao'] or '')]
print(f"Error [1955]: {len(erro_1955)}")
other = [r for r in rows if '1955' not in (r['erro_descricao'] or '')]
print(f"Other errors: {len(other)}")
for r in other:
    print(f"  CPF {r['cpf']}: {(r['erro_descricao'] or '')[:80]}")

# Check: do these CPFs have valid recibos?
cpf_list = [r['cpf'] for r in erro_1955]

# How many S-1210 events per CPF?
cur.execute("""
    SELECT cpf, COUNT(*) as cnt
    FROM explorador_eventos
    WHERE cpf = ANY(%s) AND tipo_evento = 'S-1210' AND per_apur = '2025-09'
    GROUP BY cpf
""", (cpf_list,))
cnt_rows = cur.fetchall()
counts = {r['cpf']: r['cnt'] for r in cnt_rows}

one_event = sum(1 for c in cpf_list if counts.get(c, 0) == 1)
two_events = sum(1 for c in cpf_list if counts.get(c, 0) == 2)
no_events = sum(1 for c in cpf_list if counts.get(c, 0) == 0)
print(f"\nS-1210 events per CPF:")
print(f"  1 event: {one_event}")
print(f"  2 events: {two_events}")
print(f"  0 events: {no_events}")

# Check sample - do these need the same recibo treatment as 459?
# Or were they straightforward (pipeline had the right recibo)?
for r in erro_1955[:3]:
    cpf = r['cpf']
    recibo = r['nr_recibo_original']
    
    cur.execute("""
        SELECT nr_recibo, arquivo_origem 
        FROM explorador_eventos
        WHERE cpf = %s AND tipo_evento = 'S-1210' AND per_apur = '2025-09'
        ORDER BY id
    """, (cpf,))
    evts = cur.fetchall()
    
    print(f"\nCPF {cpf} | pipeline recibo: {recibo}")
    for e in evts:
        marker = " <<<USED" if e['nr_recibo'] == recibo else ""
        print(f"  recibo={e['nr_recibo']} arq={e['arquivo_origem']}{marker}")

# Check if any 1955 CPFs also had the same 459 issue (S-3000 exclusion)
cur.execute("""
    SELECT e.cpf, COUNT(*) as s3000_cnt
    FROM explorador_eventos e
    WHERE e.cpf = ANY(%s) AND e.tipo_evento = 'S-3000' AND e.per_apur = '2025-09'
    GROUP BY e.cpf
""", (cpf_list,))
s3000_cpfs = cur.fetchall()
print(f"\nCPFs with S-3000 (exclusion): {len(s3000_cpfs)}")

conn.close()
