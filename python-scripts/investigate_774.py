"""Investigar CPF 31381951805 - ver rubrica 774 no S-1210."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2, psycopg2.extras

conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                        keepalives_interval=10, keepalives_count=3)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

CPF = "31381951805"

# 1. pipeline status
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%pipeline%'")
print("=== pipeline tables ===")
for r in cur.fetchall():
    print(r)

# 2. dados_json summary
cur.execute("SELECT id, cpf, per_apur FROM dados_json WHERE cpf = %s", (CPF,))
rows = cur.fetchall()
print("\n=== dados_json (summary) ===")
for r in rows:
    print(dict(r))

# 3. Full dados_json - find rubrica 774
cur.execute("SELECT id, cpf, per_apur, dados FROM dados_json WHERE cpf = %s LIMIT 1", (CPF,))
row = cur.fetchone()
if row:
    dados = row["dados"] if isinstance(row["dados"], dict) else json.loads(row["dados"])
    dmdev_list = dados.get("dmDev", [])
    
    print("\n=== Rubricas 774 e 607 ===")
    for i, dm in enumerate(dmdev_list):
        ide_dm = dm.get("ideDmDev", "N/A")
        info_per = dm.get("infoPerApur", {})
        ide_estab_list = info_per.get("ideEstabLot", [])
        for est in ide_estab_list:
            det_verbas = est.get("detVerbas", [])
            for v in det_verbas:
                cod = v.get("codRubr", "")
                if cod in ("774", "607"):
                    print(f"  dmDev[{i}] ideDmDev={ide_dm} rubrica={cod} ideTabRubr={v.get('ideTabRubr')} vrRubr={v.get('vrRubr')}")
    
    print("\n=== TODAS as rubricas ===")
    for i, dm in enumerate(dmdev_list):
        ide_dm = dm.get("ideDmDev", "N/A")
        info_per = dm.get("infoPerApur", {})
        ide_estab_list = info_per.get("ideEstabLot", [])
        for est in ide_estab_list:
            det_verbas = est.get("detVerbas", [])
            for v in det_verbas:
                print(f"  dmDev[{i}] {ide_dm}: cod={v.get('codRubr')} tab={v.get('ideTabRubr')} vr={v.get('vrRubr')}")

# 4. Check explorador for more context on 774 and 607
print("\n=== explorador_rubricas: 774 ===")
cur.execute("SELECT DISTINCT cod_rubr, tp_rubr, nat_rubr, cod_inc_cp, cod_inc_irrf, cod_inc_fgts FROM explorador_rubricas WHERE cod_rubr = '774' LIMIT 5")
for r in cur.fetchall():
    print(dict(r))

print("\n=== explorador_rubricas: 607 ===")
cur.execute("SELECT DISTINCT cod_rubr, tp_rubr, nat_rubr, cod_inc_cp, cod_inc_irrf, cod_inc_fgts FROM explorador_rubricas WHERE cod_rubr = '607' LIMIT 5")
for r in cur.fetchall():
    print(dict(r))

# 5. Check cruzamento_eb for both
print("\n=== cruzamento_eb: 774 ===")
cur.execute("SELECT cod_rubrica, descricao, cod_natureza, envio_status FROM cruzamento_eb WHERE cod_rubrica = '774'")
for r in cur.fetchall():
    print(dict(r))

print("\n=== cruzamento_eb: 607 ===")
cur.execute("SELECT cod_rubrica, descricao, cod_natureza, envio_status FROM cruzamento_eb WHERE cod_rubrica = '607'")
for r in cur.fetchall():
    print(dict(r))

conn.close()
