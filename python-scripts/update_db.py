import psycopg2
import bcrypt

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_master', user='easy_social_user', password='sua_senha_segura')
conn.autocommit = True
cur = conn.cursor()

# 1. Add username column if not exists
cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE;")
print('1. Coluna username adicionada')

# 2. Set username for admin (id=1 currently)
cur.execute("UPDATE usuarios SET username = 'admin' WHERE email = 'admin@easysocial.com'")
print('2. Admin username definido')

# 3. Update empresa name and CNPJ
cur.execute("""
    UPDATE empresas 
    SET nome = 'APPA SERVICOS TEMPORARIOS E EFETIVOS LTDA', 
        cnpj = '05.969.071/0001-10'
    WHERE id = 1
""")
print('3. Empresa atualizada para APPA')

# 4. Create user Ana with bcrypt hash
senha_hash = bcrypt.hashpw('123321'.encode(), bcrypt.gensalt(12)).decode()
try:
    cur.execute("""
        INSERT INTO usuarios (username, email, nome, senha_hash, role)
        VALUES ('Ana', 'ana@appa.com', 'Ana', %s, 'operador')
        RETURNING id, username, nome, role
    """, (senha_hash,))
    ana = cur.fetchone()
    print(f'4. Usuario Ana criado: id={ana[0]}, username={ana[1]}, nome={ana[2]}, role={ana[3]}')
    
    # 5. Link Ana to empresa APPA (id=1)
    cur.execute("""
        INSERT INTO usuario_empresa (usuario_id, empresa_id, role_emp)
        VALUES (%s, 1, 'operador')
        ON CONFLICT DO NOTHING
    """, (ana[0],))
    print('5. Ana vinculada a APPA')
except Exception as e:
    if '23505' in str(e):
        print('4. Ana ja existe, atualizando...')
        conn.rollback()
        conn.autocommit = True
        cur.execute("UPDATE usuarios SET username = 'Ana', senha_hash = %s WHERE email = 'ana@appa.com'", (senha_hash,))
        cur.execute("SELECT id FROM usuarios WHERE email = 'ana@appa.com'")
        ana_id = cur.fetchone()[0]
        cur.execute("INSERT INTO usuario_empresa (usuario_id, empresa_id, role_emp) VALUES (%s, 1, 'operador') ON CONFLICT DO NOTHING", (ana_id,))
        print(f'5. Ana atualizada e vinculada (id={ana_id})')
    else:
        raise

# Verify
cur.execute('SELECT id, username, email, nome, role FROM usuarios ORDER BY id')
print('\n=== USUARIOS ===')
for r in cur.fetchall():
    print(f'  id={r[0]} username={r[1]} email={r[2]} nome={r[3]} role={r[4]}')

cur.execute("""
    SELECT e.nome, e.cnpj, ue.usuario_id, ue.role_emp 
    FROM empresas e JOIN usuario_empresa ue ON ue.empresa_id = e.id 
    ORDER BY ue.usuario_id
""")
print('\n=== VINCULOS ===')
for r in cur.fetchall():
    print(f'  {r[0]} (CNPJ: {r[1]}) - user_id={r[2]} role={r[3]}')

cur.close()
conn.close()
print('\nDone!')
