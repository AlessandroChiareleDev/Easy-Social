"""
Importa os dados do cruzamento EB Skills para a tabela cruzamento_eb no PostgreSQL.
A tabela armazena os dados SEM a coluna de status (ok/inconsistente).
O frontend calcula o status comparando valores atuais vs corretos.
"""
import json
import psycopg2
import sys
import os

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'easy_social_db',
    'user': 'easy_social_user',
    'password': 'sua_senha_segura'
}

JSON_PATH = os.path.join(os.path.dirname(__file__), 'tabela_eb_cruzamento.json')

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cruzamento_eb (
    id SERIAL PRIMARY KEY,
    cod_rubrica VARCHAR(20) NOT NULL,
    descricao TEXT NOT NULL,
    cod_natureza TEXT,
    incid_inss VARCHAR(10),
    incid_irrf VARCHAR(10),
    incid_fgts VARCHAR(10),
    analise TEXT,
    incid_base_legal_inss TEXT,
    incid_base_legal_irrf TEXT,
    incid_base_legal_fgts TEXT,
    importado_em TIMESTAMP DEFAULT NOW()
);
"""

INSERT_SQL = """
INSERT INTO cruzamento_eb (
    cod_rubrica, descricao, cod_natureza,
    incid_inss, incid_irrf, incid_fgts, analise,
    incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def main():
    # Load JSON data
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'Loaded {len(data)} rows from JSON')

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Drop and recreate table (fresh import)
    cur.execute("DROP TABLE IF EXISTS cruzamento_eb;")
    cur.execute(CREATE_TABLE_SQL)
    print('Table cruzamento_eb created')

    # Insert all rows
    inserted = 0
    for row in data:
        cur.execute(INSERT_SQL, (
            row['idRub'],
            row['rubrica'],
            row['codNatur'],
            row['incidINSS'],
            row['incidIRRF'],
            row['incidFGTS'],
            row['analise'],
            row['incidBaseLegalINSS'],
            row['incidBaseLegalIRRF'],
            row['incidBaseLegalFGTS'],
        ))
        inserted += 1

    conn.commit()
    print(f'Inserted {inserted} rows into cruzamento_eb')

    # Verify
    cur.execute("SELECT COUNT(*) FROM cruzamento_eb")
    count = cur.fetchone()[0]
    print(f'Verification: {count} rows in cruzamento_eb')

    # Show sample
    cur.execute("""
        SELECT cod_rubrica, LEFT(descricao, 35), incid_inss, incid_irrf, incid_fgts,
               LEFT(incid_base_legal_inss, 40),
               LEFT(incid_base_legal_irrf, 40),
               LEFT(incid_base_legal_fgts, 40)
        FROM cruzamento_eb
        ORDER BY cod_rubrica::int
        LIMIT 5
    """)
    print('\n--- Amostra ---')
    for r in cur.fetchall():
        print(f'  Rub {r[0]}: {r[1]}')
        print(f'    Sistema: INSS={r[2]}, IRRF={r[3]}, FGTS={r[4]}')
        print(f'    Correto INSS: {r[5]}')
        print(f'    Correto IRRF: {r[6]}')
        print(f'    Correto FGTS: {r[7]}')

    # Count inconsistencies
    cur.execute("""
        SELECT COUNT(*) FROM cruzamento_eb
        WHERE incid_inss != SPLIT_PART(incid_base_legal_inss, ' - ', 1)
           OR incid_irrf != SPLIT_PART(incid_base_legal_irrf, ' - ', 1)
           OR incid_fgts != SPLIT_PART(incid_base_legal_fgts, ' - ', 1)
    """)
    incons = cur.fetchone()[0]
    print(f'\nInconsistências: {incons}')
    print(f'Regulares: {count - incons}')

    cur.close()
    conn.close()
    print('\nImportação concluída!')


if __name__ == '__main__':
    main()
