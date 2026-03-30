"""
Importa a Tabela 3 do eSocial (Natureza das Rubricas) para o PostgreSQL.
Fonte: setup-inicial/tb16098.txt (baixada do frontend do eSocial)
"""
import os
import sys
import psycopg2

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "easy_social_db"),
    "user": os.environ.get("DB_USER", "easy_social_user"),
    "password": os.environ.get("DB_PASSWORD", "sua_senha_segura"),
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS esocial_tabela3_natureza (
    codigo INTEGER PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    dt_inicio DATE NOT NULL,
    dt_fim DATE,
    descricao TEXT,
    versao INTEGER DEFAULT 17
);
"""

TXT_PATH = os.path.join(os.path.dirname(__file__), '..', 'setup-inicial', 'tb16098.txt')


def parse_date(d):
    """Converte DDMMAAAA para AAAA-MM-DD."""
    if not d or not d.strip():
        return None
    d = d.strip()
    if len(d) == 8:
        return f"{d[4:8]}-{d[2:4]}-{d[0:2]}"
    return None


def main():
    if not os.path.exists(TXT_PATH):
        print(f"ERRO: Arquivo não encontrado: {TXT_PATH}")
        sys.exit(1)

    # Ler com encoding latin-1 (arquivo do eSocial)
    with open(TXT_PATH, 'r', encoding='latin-1') as f:
        lines = f.readlines()

    # Primeira linha é header: versão=17 CODIGO, NOME, DTINICIO, DTFIM, DESCRICAO
    header = lines[0].strip()
    print(f"Header: {header}")

    records = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split('|')
        if len(parts) < 4:
            print(f"  SKIP (formato inválido): {line[:80]}")
            continue

        codigo = int(parts[0])
        nome = parts[1]
        dt_inicio = parse_date(parts[2])
        dt_fim = parse_date(parts[3]) if len(parts) > 3 else None
        descricao = parts[4] if len(parts) > 4 else ''

        records.append((codigo, nome, dt_inicio, dt_fim, descricao))

    print(f"Total registros parseados: {len(records)}")

    # Inserir no banco
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            # Limpar tabela antes de reimportar
            cur.execute("DELETE FROM esocial_tabela3_natureza")
            deleted = cur.rowcount
            if deleted:
                print(f"  Removidos {deleted} registros antigos")

            for rec in records:
                cur.execute(
                    """INSERT INTO esocial_tabela3_natureza
                       (codigo, nome, dt_inicio, dt_fim, descricao)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (codigo) DO UPDATE SET
                           nome = EXCLUDED.nome,
                           dt_inicio = EXCLUDED.dt_inicio,
                           dt_fim = EXCLUDED.dt_fim,
                           descricao = EXCLUDED.descricao""",
                    rec,
                )

            conn.commit()
            print(f"  Inseridos {len(records)} registros na tabela esocial_tabela3_natureza")

            # Stats
            cur.execute("SELECT COUNT(*) FROM esocial_tabela3_natureza")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM esocial_tabela3_natureza WHERE dt_fim IS NOT NULL")
            expirados = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM esocial_tabela3_natureza WHERE dt_fim IS NULL")
            vigentes = cur.fetchone()[0]

            print(f"\n=== RESULTADO ===")
            print(f"Total na tabela: {total}")
            print(f"Vigentes (sem dt_fim): {vigentes}")
            print(f"Expirados (com dt_fim): {expirados}")

            # Verificar codigo 2920
            cur.execute(
                "SELECT codigo, nome, dt_inicio, dt_fim FROM esocial_tabela3_natureza WHERE codigo = 2920"
            )
            row = cur.fetchone()
            if row:
                print(f"\n=== CÓDIGO 2920 ===")
                print(f"Código: {row[0]}")
                print(f"Nome: {row[1]}")
                print(f"Início: {row[2]}")
                print(f"Fim: {row[3]}")
                if row[3]:
                    print(f"STATUS: EXPIRADO em {row[3]} — NÃO PODE ser usado!")
                else:
                    print(f"STATUS: VIGENTE")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
