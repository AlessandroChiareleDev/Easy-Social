"""Check full error details and think about alternative approaches for error 459."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Full error message for first few CPFs
cur.execute("""
    SELECT cpf, nr_recibo_original, erro_descricao
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND erro_descricao LIKE '%%[459]%%'
    ORDER BY cpf LIMIT 3
""")
for r in cur.fetchall():
    print(f"CPF: {r['cpf']}")
    print(f"Recibo orig: {r['nr_recibo_original']}")
    print(f"Erro: {r['erro_descricao']}")
    print()

# Also check: for these CPFs, is there a S-5002 response matching the 
# lote 28 recibo? If so, the retorno might tell us if data was correct
print("=" * 60)
print("Checking S-5002 dados_json for lote 28 events...")
cur.execute("""
    SELECT p.cpf, p.nr_recibo_original, e.dados_json, e.arquivo_origem
    FROM pipeline_cpf_results p
    JOIN explorador_eventos e ON e.cpf = p.cpf 
        AND e.tipo_evento = 'S-5002' 
        AND e.per_apur = '2025-09'
        AND e.arquivo_origem LIKE '%%' || REPLACE(p.nr_recibo_original, '.', '') || '%%'
    WHERE p.run_id = 1 AND p.erro_descricao LIKE '%%[459]%%'
    LIMIT 3
""")
results = cur.fetchall()
print(f"Found {len(results)} matching S-5002 events")
for r in results:
    import json
    dj = r['dados_json'] or {}
    print(f"\nCPF: {r['cpf']}")
    print(f"Recibo orig: {r['nr_recibo_original']}")
    print(f"S-5002 arquivo: {r['arquivo_origem']}")
    # Print just the key parts of dados_json
    if isinstance(dj, dict):
        print(f"Keys: {list(dj.keys())}")
        if 'infoIRCR' in dj:
            for ir in dj['infoIRCR'][:2]:
                print(f"  codIncIRRF={ir.get('codIncIRRF')} vrIRRF={ir.get('vrIRRF')}")

conn.close()
