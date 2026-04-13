"""Investigar CPF 31381951805 - S-1200 e S-1210 no explorador."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

CPF = "31381951805"
PER = "2025-09"

# 1. explorador_eventos - S-1200 and S-1210
for tipo in ['S-1200', 'S-1210']:
    cur.execute("""
        SELECT id, tipo_evento, cpf, per_apur, nr_recibo, id_evento, dados_json
        FROM explorador_eventos
        WHERE cpf = %s AND per_apur = %s AND tipo_evento = %s
        ORDER BY id DESC
    """, (CPF, PER, tipo))
    rows = cur.fetchall()
    print(f"\n=== explorador_eventos: {tipo} ({len(rows)} registros) ===")
    for r in rows:
        d = dict(r)
        dados = d.pop('dados_json', {})
        print(f"  id={d['id']} recibo={d['nr_recibo']} evento={d['id_evento']}")
        if dados:
            print(f"  dados_json keys: {list(dados.keys()) if isinstance(dados, dict) else 'not dict'}")
            if isinstance(dados, dict):
                # For S-1200, look for rubricas
                if tipo == 'S-1200':
                    dmdev = dados.get('dmDev', [])
                    for i, dm in enumerate(dmdev):
                        ide = dm.get('ideDmDev', '?')
                        info_per = dm.get('infoPerApur', {})
                        estabs = info_per.get('ideEstabLot', [])
                        for est in estabs:
                            verbas = est.get('detVerbas', est.get('remunPerApur', []))
                            if isinstance(verbas, list):
                                for v in verbas:
                                    cod = v.get('codRubr', v.get('cod_rubr', '?'))
                                    if cod in ('774', '607'):
                                        print(f"  *** FOUND {cod}: {v}")
                                print(f"  dmDev[{i}] {ide}: {len(verbas)} verbas total")
                            else:
                                print(f"  dmDev[{i}] {ide}: verbas={verbas}")
                    # Print all rubrica codes
                    all_codes = []
                    for dm in dmdev:
                        for est in dm.get('infoPerApur', {}).get('ideEstabLot', []):
                            for v in est.get('detVerbas', est.get('remunPerApur', [])):
                                all_codes.append(v.get('codRubr', v.get('cod_rubr', '?')))
                    print(f"  All rubrica codes: {all_codes}")
                # For S-1210, show payment info
                elif tipo == 'S-1210':
                    print(f"  Full dados_json: {json.dumps(dados, indent=2, default=str)[:2000]}")

# 2. pipeline_cpf_results for this CPF
cur.execute("""
    SELECT id, run_id, cpf, status, nr_recibo_original, nr_recibo_novo, erro_descricao
    FROM pipeline_cpf_results WHERE cpf = %s
""", (CPF,))
rows = cur.fetchall()
print(f"\n=== pipeline_cpf_results ({len(rows)} registros) ===")
for r in rows:
    print(dict(r))

# 3. esocial_envios - last events for this CPF
cur.execute("""
    SELECT id, tipo_evento, cpf, per_apur, status, nr_recibo, protocolo, created_at
    FROM esocial_envios WHERE cpf = %s
    ORDER BY id DESC LIMIT 10
""", (CPF,))
rows = cur.fetchall()
print(f"\n=== esocial_envios (last 10) ===")
for r in rows:
    print(dict(r))

# 4. Check explorador_rubricas for 774 vs 607 comparison
print("\n=== Comparação explorador_rubricas 774 vs 607 ===")
for cod in ['774', '607']:
    cur.execute("""
        SELECT DISTINCT cod_rubr, tp_rubr, nat_rubr, cod_inc_cp, cod_inc_irrf, cod_inc_fgts
        FROM explorador_rubricas WHERE cod_rubr = %s LIMIT 3
    """, (cod,))
    rows = cur.fetchall()
    print(f"\n  {cod}:")
    for r in rows:
        print(f"    {dict(r)}")

# 5. cruzamento_eb for both
print("\n=== cruzamento_eb 774 vs 607 ===")
for cod in ['774', '607']:
    cur.execute("""
        SELECT cod_rubrica, descricao, cod_natureza, 
               incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts,
               envio_status
        FROM cruzamento_eb WHERE cod_rubrica = %s
    """, (cod,))
    rows = cur.fetchall()
    print(f"\n  {cod}:")
    for r in rows:
        print(f"    {dict(r)}")

conn.close()
