import psycopg2, json
from db_config import DB_CONFIG, LOCAL_DB_CONFIG

# 1. Tabelas locais
conn = psycopg2.connect(**LOCAL_DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [r[0] for r in cur.fetchall()]
print("Tabelas locais:", tables)

# 2. Buscar no pipeline_audit se existe
for t in tables:
    if 'pipeline' in t or 'audit' in t or 'recibo' in t:
        cur.execute(f"SELECT * FROM {t} LIMIT 3")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        print(f"\nTabela {t}: {cols}")
        for r in rows:
            print(f"  {r}")

conn.close()

# 3. Buscar nome no explorador via Supabase
conn2 = psycopg2.connect(**DB_CONFIG)
cur2 = conn2.cursor()
# Tentar qualquer evento para este CPF que tenha nmTrab no JSON
cur2.execute("""
    SELECT tipo_evento, per_apur, 
           dados_json->>'nmTrab' as nome,
           dados_json->>'cpfTrab' as cpf_trab
    FROM explorador_eventos
    WHERE cpf = '08132588983'
    LIMIT 10
""")
rows = cur2.fetchall()
print(f"\nExplorador para CPF 08132588983: {len(rows)} registros")
for r in rows:
    print(f"  {r}")

# 4. Buscar nome em trabalhadores / funcionários do Supabase
cur2.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND (table_name LIKE '%trab%' OR table_name LIKE '%func%' OR table_name LIKE '%pessoa%' OR table_name LIKE '%empregad%')")
tab2 = [r[0] for r in cur2.fetchall()]
print(f"\nTabelas Supabase relevantes: {tab2}")

# 5. Se explorador não tem, buscar direto no JSON com chave parcial
cur2.execute("""
    SELECT dados_json
    FROM explorador_eventos
    WHERE cpf = '08132588983'
    LIMIT 1
""")
row = cur2.fetchone()
if row:
    print(f"\nDados JSON exemplo: {json.dumps(row[0], indent=2, ensure_ascii=False)[:500]}")
else:
    print("\nNenhum evento no explorador para este CPF")

conn2.close()
