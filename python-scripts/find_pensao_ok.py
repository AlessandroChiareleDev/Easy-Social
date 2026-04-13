import sys, psycopg2, psycopg2.extras, os
sys.path.insert(0, "/opt/easy-social/python-scripts")
from db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1. Ver importacoes (pastas de onde vieram os XMLs)
print("=== IMPORTAÇÕES ===")
cur.execute("SELECT id, pasta, periodo, total_arquivos FROM explorador_importacoes ORDER BY id")
for r in cur.fetchall():
    print(f"  ID={r['id']} pasta={r['pasta']} periodo={r['periodo']} arquivos={r['total_arquivos']}")
    # Checar se pasta ainda existe
    if os.path.isdir(r['pasta']):
        files = os.listdir(r['pasta'])
        xmls = [f for f in files if f.endswith('.xml')]
        print(f"    -> PASTA EXISTE! {len(xmls)} XMLs encontrados")
    else:
        print(f"    -> Pasta NÃO existe mais")

# 2. Ver arquivo_origem de alguns eventos
print("\n=== EXEMPLOS de arquivo_origem ===")
cur.execute("SELECT arquivo_origem FROM explorador_eventos LIMIT 5")
for r in cur.fetchall():
    print(f"  {r['arquivo_origem']}")

# 3. Checar uploads temp
print("\n=== UPLOADS TEMP ===")
for d in ["/opt/easy-social/python-scripts/uploads", "/tmp/explorador_uploads"]:
    if os.path.isdir(d):
        files = os.listdir(d)
        print(f"  {d}: {len(files)} arquivos")
    else:
        print(f"  {d}: NÃO EXISTE")

conn.close()
