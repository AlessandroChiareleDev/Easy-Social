"""Buscar dados S-1210 da Adriana para preenchimento manual no portal."""
import psycopg2, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor()

CPF = "31381951805"

# Buscar S-1210 da Adriana
cur.execute("""
    SELECT nr_recibo, dados_json, created_at, per_apur
    FROM explorador_eventos
    WHERE cpf = %s AND tipo_evento = 'S-1210'
    ORDER BY per_apur, created_at
""", (CPF,))
rows = cur.fetchall()
print(f"S-1210 para CPF {CPF}: {len(rows)} evento(s)")
for r in rows:
    print(f"\n  per_apur={r[3]} recibo={r[0]} em {r[2]}")
    dados = r[1] if isinstance(r[1], dict) else json.loads(r[1] or '{}')
    print(f"  dados_json completo:")
    print(json.dumps(dados, indent=2, ensure_ascii=False))

# Buscar S-1200 da Adriana (pra ver demonstrativos)
print("\n" + "=" * 60)
cur.execute("""
    SELECT nr_recibo, dados_json, created_at, per_apur
    FROM explorador_eventos
    WHERE cpf = %s AND tipo_evento = 'S-1200'
    ORDER BY per_apur, created_at
""", (CPF,))
rows2 = cur.fetchall()
print(f"S-1200 para CPF {CPF}: {len(rows2)} evento(s)")
for r in rows2:
    print(f"\n  per_apur={r[3]} recibo={r[0]} em {r[2]}")
    dados = r[1] if isinstance(r[1], dict) else json.loads(r[1] or '{}')
    print(f"  dados_json completo:")
    print(json.dumps(dados, indent=2, ensure_ascii=False))

# Also check the XML file if exists
xml_path = "/opt/easy-social/xmls_set2025/"
print("\n" + "=" * 60)
print("Procurando XMLs da Adriana...")
import glob
for f in glob.glob(f"{xml_path}*31381951805*") + glob.glob(f"{xml_path}*S-1210*"):
    if "31381951805" in f or "S-1210" in f:
        print(f"  Encontrado: {f}")

# Check pipeline_cpf_results for her
cur.execute("""
    SELECT cpf, status, nr_recibo_original, nr_recibo_novo, pagamentos, info_ir_cr, erro_descricao
    FROM pipeline_cpf_results
    WHERE cpf = %s
""", (CPF,))
rows3 = cur.fetchall()
print(f"\npipeline_cpf_results para {CPF}: {len(rows3)}")
for r in rows3:
    print(f"  status={r[1]} recibo_orig={r[2]} recibo_novo={r[3]}")
    print(f"  pagamentos: {r[4]}")
    print(f"  info_ir_cr: {r[5]}")
    if r[6]:
        print(f"  erro: {r[6]}")

conn.close()
