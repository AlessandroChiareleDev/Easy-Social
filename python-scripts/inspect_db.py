import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

cur.execute("""
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name IN ('analise_natureza','tabela_eb','tabela_eventos_gl','dinamica','naturezas_esocial','auditoria_naturezas')
ORDER BY table_name, ordinal_position
""")

current_table = ''
for row in cur.fetchall():
    if row[0] != current_table:
        current_table = row[0]
        print(f'\n=== {current_table} ===')
    print(f'  {row[1]} ({row[2]})')

# Count rows
print('\n=== ROW COUNTS ===')
for t in ['analise_natureza','tabela_eb','tabela_eventos_gl','dinamica','naturezas_esocial','auditoria_naturezas']:
    cur.execute(f"SELECT count(*) FROM {t}")
    print(f'  {t}: {cur.fetchone()[0]}')

cur.close()
conn.close()
