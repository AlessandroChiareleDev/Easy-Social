import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db',
    user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# Schema of rubrica_corrections
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'rubrica_corrections' ORDER BY ordinal_position")
print('=== rubrica_corrections schema ===')
for r in cur.fetchall():
    print(f'  {r[0]} ({r[1]})')

# Check Tipo and PIS/PASEP values
print('\n=== Tipo (tpRubr candidate) ===')
cur.execute("SELECT raw_data->>'Tipo' AS tp, COUNT(*) FROM tabela_eventos_gl GROUP BY tp ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  Tipo={r[0]}: {r[1]}')

print('\n=== PIS/PASEP - Incidência no eSocial ===')
cur.execute("SELECT raw_data->>'PIS/PASEP - Incidência no eSocial' AS pis, COUNT(*) FROM tabela_eventos_gl GROUP BY pis ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  PIS/PASEP_Inc={r[0]}: {r[1]}')

print('\n=== Cód. PIS/PASEP ===')
cur.execute("SELECT raw_data->>'Cód. PIS/PASEP' AS pis, COUNT(*) FROM tabela_eventos_gl GROUP BY pis ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  Cod.PIS={r[0]}: {r[1]}')

print('\n=== Cód. INSS ===')
cur.execute("SELECT raw_data->>'Cód. INSS' AS inss, COUNT(*) FROM tabela_eventos_gl GROUP BY inss ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  Cod.INSS={r[0]}: {r[1]}')

print('\n=== Cód. IRRF ===')
cur.execute("SELECT raw_data->>'Cód. IRRF' AS irrf, COUNT(*) FROM tabela_eventos_gl GROUP BY irrf ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  Cod.IRRF={r[0]}: {r[1]}')

print('\n=== Cód. FGTS ===')
cur.execute("SELECT raw_data->>'Cód. FGTS' AS fgts, COUNT(*) FROM tabela_eventos_gl GROUP BY fgts ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  Cod.FGTS={r[0]}: {r[1]}')

print('\n=== INSS - Incidência no eSocial ===')
cur.execute("SELECT raw_data->>'INSS - Incidência no eSocial' AS inss, COUNT(*) FROM tabela_eventos_gl GROUP BY inss ORDER BY COUNT(*) DESC LIMIT 5")
for r in cur.fetchall():
    print(f'  INSS_Inc={r[0]}: {r[1]}')

print('\n=== Tipo Evento ===')
cur.execute("SELECT raw_data->>'Tipo Evento' AS te, COUNT(*) FROM tabela_eventos_gl GROUP BY te ORDER BY COUNT(*) DESC LIMIT 10")
for r in cur.fetchall():
    print(f'  TipoEvento={r[0]}: {r[1]}')

# Sample one full record to see all values
print('\n=== AMOSTRA: 1 registro completo (rubrica 19) ===')
cur.execute("SELECT raw_data FROM tabela_eventos_gl WHERE raw_data->>'Código' = '19' LIMIT 1")
row = cur.fetchone()
if row:
    import json
    data = row[0]
    for k, v in sorted(data.items()):
        if v not in (None, '', 'None'):
            print(f'  {k}: {v}')

# Sample rubrica_corrections record
print('\n=== AMOSTRA: rubrica_corrections (rubrica 19) ===')
cur.execute("SELECT * FROM rubrica_corrections WHERE cod_rubrica = '19' LIMIT 1")
cols = [d[0] for d in cur.description]
row = cur.fetchone()
if row:
    for c, v in zip(cols, row):
        if v not in (None, ''):
            print(f'  {c}: {v}')

conn.close()
