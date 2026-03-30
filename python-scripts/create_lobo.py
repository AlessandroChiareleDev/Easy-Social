import psycopg2
import bcrypt

conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_master', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

senha_hash = bcrypt.hashpw(b'180306', bcrypt.gensalt(12)).decode()

cur.execute(
    "INSERT INTO usuarios (username, email, nome, senha_hash, role) VALUES (%s, %s, %s, %s, %s) RETURNING id",
    ('Lobo', 'lobo@appa.com', 'Lobo', senha_hash, 'operador')
)
lobo_id = cur.fetchone()[0]

cur.execute(
    "INSERT INTO usuario_empresa (usuario_id, empresa_id, role_emp) VALUES (%s, %s, %s)",
    (lobo_id, 1, 'operador')
)

conn.commit()
print(f'Usuario Lobo criado (id={lobo_id}), vinculado a APPA como operador')

# Verify
cur.execute("SELECT id, username, nome, role FROM usuarios ORDER BY id")
print('\n=== USUARIOS ===')
for r in cur.fetchall():
    print(f'  id={r[0]} user={r[1]} nome={r[2]} role={r[3]}')

cur.execute("""
    SELECT ue.usuario_id, u.username, e.nome, ue.role_emp 
    FROM usuario_empresa ue 
    JOIN usuarios u ON u.id = ue.usuario_id 
    JOIN empresas e ON e.id = ue.empresa_id 
    ORDER BY ue.usuario_id
""")
print('\n=== VINCULOS ===')
for r in cur.fetchall():
    print(f'  {r[1]} -> {r[2]} ({r[3]})')

cur.close()
conn.close()
