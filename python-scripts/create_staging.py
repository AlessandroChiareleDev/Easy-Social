import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='easy_social_db',
    user='easy_social_user',
    password='sua_senha_segura'
)
conn.autocommit = True
cur = conn.cursor()

# 1. Create correcoes_staging table
cur.execute("""
    CREATE TABLE IF NOT EXISTS correcoes_staging (
        id SERIAL PRIMARY KEY,
        analise_natureza_id INTEGER NOT NULL REFERENCES analise_natureza(id),
        codigoevento VARCHAR(20) NOT NULL,
        nome_evento VARCHAR(500),
        natureza_anterior VARCHAR(500),
        natureza_nova_codigo VARCHAR(20) NOT NULL,
        natureza_nova_nome VARCHAR(500) NOT NULL,
        motivo TEXT DEFAULT '',
        usuario_id INTEGER,
        usuario_nome VARCHAR(200) DEFAULT 'sistema',
        status VARCHAR(20) DEFAULT 'pendente',  -- pendente | aplicada | rejeitada
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        aplicado_em TIMESTAMP,
        UNIQUE(analise_natureza_id)  -- only one pending correction per rubrica
    );
""")
print("1. Tabela correcoes_staging criada")

# 2. Migrate existing corrections from analise_natureza into staging
cur.execute("""
    INSERT INTO correcoes_staging 
        (analise_natureza_id, codigoevento, nome_evento, natureza_anterior, 
         natureza_nova_codigo, natureza_nova_nome, usuario_nome, status, criado_em, aplicado_em)
    SELECT 
        a.id,
        a.col_a,
        a.col_b,
        a.natureza_anterior,
        SPLIT_PART(a.natureza_nova, '-', 1),
        SUBSTRING(a.natureza_nova FROM POSITION('-' IN a.natureza_nova) + 1),
        COALESCE(a.usuario_correcao, 'sistema'),
        'aplicada',
        COALESCE(a.data_correcao, CURRENT_TIMESTAMP),
        a.data_correcao
    FROM analise_natureza a
    WHERE a.natureza_nova IS NOT NULL
    ON CONFLICT (analise_natureza_id) DO NOTHING
""")
migrated = cur.rowcount
print(f"2. {migrated} correções existentes migradas para staging (status=aplicada)")

# 3. Reset analise_natureza corrections (so staging is the source of truth)
cur.execute("""
    UPDATE analise_natureza 
    SET natureza_nova = NULL,
        natureza_anterior = NULL,
        usuario_correcao = NULL,
        data_correcao = NULL
    WHERE natureza_nova IS NOT NULL
""")
reset = cur.rowcount
print(f"3. {reset} registros em analise_natureza resetados (staging é fonte da verdade agora)")

# 4. Check final state
cur.execute("SELECT count(*) FROM correcoes_staging")
total = cur.fetchone()[0]
cur.execute("SELECT count(*) FROM correcoes_staging WHERE status = 'aplicada'")
aplicadas = cur.fetchone()[0]
cur.execute("SELECT count(*) FROM correcoes_staging WHERE status = 'pendente'")
pendentes = cur.fetchone()[0]
print(f"\n=== ESTADO FINAL ===")
print(f"correcoes_staging: {total} total ({aplicadas} aplicadas, {pendentes} pendentes)")

cur.execute("""
    SELECT count(*) FILTER (WHERE UPPER(TRIM(col_d)) = 'VERIFICAR') as verificar,
           count(*) FILTER (WHERE UPPER(TRIM(col_d)) = 'VERIFICAR' AND natureza_nova IS NOT NULL) as com_correcao
    FROM analise_natureza
""")
row = cur.fetchone()
print(f"analise_natureza: {row[0]} a verificar, {row[1]} com natureza_nova (deve ser 0)")

cur.close()
conn.close()
print("\nDone!")
