import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_master', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# List all tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
print('=== TABELAS ===')
for r in cur.fetchall():
    print(f'  {r[0]}')

# usuarios structure
print('\n=== USUARIOS (colunas) ===')
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='usuarios' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f'  {r[0]} ({r[1]}, nullable={r[2]})')

# usuarios data
print('\n=== USUARIOS (dados) ===')
cur.execute('SELECT id, username, nome, role, ativo FROM usuarios')
for r in cur.fetchall():
    print(f'  id={r[0]} username={r[1]} nome={r[2]} role={r[3]} ativo={r[4]}')

# empresas
print('\n=== EMPRESAS ===')
cur.execute('SELECT id, nome, cnpj, db_name FROM empresas')
for r in cur.fetchall():
    print(f'  id={r[0]} nome={r[1]} cnpj={r[2]} db={r[3]}')

# usuario_empresa structure first
print('\n=== USUARIO_EMPRESA (colunas) ===')
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='usuario_empresa' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f'  {r[0]} ({r[1]})')

# usuario_empresa
print('\n=== USUARIO_EMPRESA (vinculo) ===')
cur.execute("""
    SELECT ue.usuario_id, u.username, ue.empresa_id, e.nome
    FROM usuario_empresa ue
    JOIN usuarios u ON u.id = ue.usuario_id
    JOIN empresas e ON e.id = ue.empresa_id
""")
for r in cur.fetchall():
    print(f'  user_id={r[0]} ({r[1]}) -> empresa_id={r[2]} ({r[3]})')

# usuario_empresa structure
print('\n=== USUARIO_EMPRESA (colunas) - duplicata removida ===')
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='usuario_empresa' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f'  {r[0]} ({r[1]})')

cur.close()
conn.close()
