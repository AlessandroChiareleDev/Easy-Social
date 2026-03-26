import psycopg2

# Connect to postgres default DB to create databases
conn = psycopg2.connect(host='localhost', port=5432, dbname='postgres', user='easy_social_user', password='sua_senha_segura')
conn.autocommit = True
cur = conn.cursor()

# Create master DB if not exists
cur.execute("SELECT 1 FROM pg_database WHERE datname = 'easy_social_master'")
if cur.fetchone():
    print('easy_social_master already exists')
else:
    cur.execute('CREATE DATABASE easy_social_master')
    print('easy_social_master CREATED')

cur.close()
conn.close()

# Now connect to master DB and create tables
conn = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_master', user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()

# Usuarios table
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    nome          VARCHAR(255) NOT NULL,
    senha_hash    VARCHAR(255) NOT NULL,
    role          VARCHAR(20) DEFAULT 'operador' CHECK (role IN ('admin', 'operador')),
    ativo         BOOLEAN DEFAULT true,
    criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Empresas table
cur.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id            SERIAL PRIMARY KEY,
    nome          VARCHAR(255) NOT NULL,
    cnpj          VARCHAR(18) UNIQUE,
    db_name       VARCHAR(100) UNIQUE NOT NULL,
    db_host       VARCHAR(255) DEFAULT 'localhost',
    db_port       INTEGER DEFAULT 5432,
    ativo         BOOLEAN DEFAULT true,
    criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# N:N - user can access multiple companies
cur.execute("""
CREATE TABLE IF NOT EXISTS usuario_empresa (
    id          SERIAL PRIMARY KEY,
    usuario_id  INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    empresa_id  INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    role_emp    VARCHAR(20) DEFAULT 'operador' CHECK (role_emp IN ('admin', 'operador')),
    criado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usuario_id, empresa_id)
);
""")

# Copy naturezas_esocial from the company DB to master (shared table)
cur.execute("""
CREATE TABLE IF NOT EXISTS naturezas_esocial (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(10) UNIQUE NOT NULL,
    nome        VARCHAR(500) NOT NULL,
    descricao   TEXT,
    data_inicio DATE,
    data_fim    DATE,
    criado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
print('Tables created in easy_social_master')

# Copy naturezas_esocial data from old DB
conn2 = psycopg2.connect(host='localhost', port=5432, dbname='easy_social_db', user='easy_social_user', password='sua_senha_segura')
cur2 = conn2.cursor()
cur2.execute("SELECT codigo, nome, descricao, data_inicio, data_fim FROM naturezas_esocial ORDER BY id")
rows = cur2.fetchall()
cur2.close()
conn2.close()

# Check if already populated
cur.execute("SELECT count(*) FROM naturezas_esocial")
count = cur.fetchone()[0]
if count < len(rows):
    conn.rollback()
    cur.execute("DELETE FROM naturezas_esocial")
    conn.commit()
    for row in rows:
        cur.execute(
            "INSERT INTO naturezas_esocial (codigo, nome, descricao, data_inicio, data_fim) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (codigo) DO NOTHING",
            row
        )
    conn.commit()
    print(f'Copied {len(rows)} naturezas_esocial to master')
else:
    print(f'naturezas_esocial already has {count} rows, skipping')

# Register the existing company DB
cur.execute("SELECT count(*) FROM empresas WHERE db_name = 'easy_social_db'")
if cur.fetchone()[0] == 0:
    cur.execute(
        "INSERT INTO empresas (nome, cnpj, db_name) VALUES (%s, %s, %s) RETURNING id",
        ('Empresa Demo', '00.000.000/0001-00', 'easy_social_db')
    )
    emp_id = cur.fetchone()[0]
    conn.commit()
    print(f'Registered Empresa Demo (id={emp_id})')
else:
    cur.execute("SELECT id FROM empresas WHERE db_name = 'easy_social_db'")
    emp_id = cur.fetchone()[0]
    print(f'Empresa Demo already registered (id={emp_id})')

# Create admin user (password: admin123)
import bcrypt
senha_hash = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()

cur.execute("SELECT count(*) FROM usuarios WHERE email = 'admin@easysocial.com'")
if cur.fetchone()[0] == 0:
    cur.execute(
        "INSERT INTO usuarios (email, nome, senha_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
        ('admin@easysocial.com', 'Administrador', senha_hash, 'admin')
    )
    user_id = cur.fetchone()[0]
    # Link admin to company
    cur.execute(
        "INSERT INTO usuario_empresa (usuario_id, empresa_id, role_emp) VALUES (%s, %s, %s)",
        (user_id, emp_id, 'admin')
    )
    conn.commit()
    print(f'Created admin user (id={user_id}) linked to Empresa Demo')
else:
    print('Admin user already exists')

cur.close()
conn.close()
print('\n=== SETUP COMPLETE ===')
print('Master DB: easy_social_master')
print('Admin: admin@easysocial.com / admin123')
