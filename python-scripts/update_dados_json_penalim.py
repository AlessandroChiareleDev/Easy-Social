"""
Script para atualizar dados_json dos S-1210 no Supabase,
re-parseando os XMLs originais para incluir dedDepen e penAlim
dentro de infoIRCR (que antes eram ignorados).

Executa no VPS onde os XMLs estão em /opt/easy-social/xmls_set2025/
"""
import os
import sys
import json
import psycopg2
import psycopg2.extras
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db_config import DB_CONFIG

# Importar helpers do explorador
sys.path.insert(0, str(Path(__file__).parent / "esocial"))
from explorador_routes import _parse_xml_file


def main():
    conn = psycopg2.connect(**DB_CONFIG, options="-c statement_timeout=600000")
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Buscar APENAS S-1210 que têm infoIRCR no dados_json
            # (candidatos a ter penAlim/dedDepen faltando)
            cur.execute("""
                SELECT e.id, e.arquivo_origem, e.dados_json, i.pasta
                FROM explorador_eventos e
                JOIN explorador_importacoes i ON i.id = e.importacao_id
                WHERE e.tipo_evento = 'S-1210'
                  AND e.arquivo_origem IS NOT NULL
                  AND e.dados_json::text LIKE '%infoIRCR%'
            """)
            rows = cur.fetchall()
            print(f"S-1210 com infoIRCR no dados_json: {len(rows)}")

            updated = 0
            errors = 0
            skipped = 0

            for row in rows:
                filepath = os.path.join(row["pasta"], row["arquivo_origem"])
                if not os.path.isfile(filepath):
                    skipped += 1
                    continue

                parsed, err = _parse_xml_file(filepath)
                if err or not parsed:
                    errors += 1
                    continue

                new_dados = parsed.get("dados_json", {})

                # Check if there's new penAlim or dedDepen data
                new_ir = new_dados.get("infoIRCR", [])
                has_new_data = False
                for entry in new_ir:
                    if entry.get("penAlim") or entry.get("dedDepen"):
                        has_new_data = True
                        break

                if not has_new_data:
                    skipped += 1
                    continue

                # Update dados_json
                cur.execute("""
                    UPDATE explorador_eventos
                    SET dados_json = %s
                    WHERE id = %s
                """, (json.dumps(new_dados), row["id"]))
                updated += 1
                if updated % 50 == 0:
                    conn.commit()
                if updated <= 5:
                    cpf = new_dados.get("pagamentos", [{}])[0].get("ideDmDev", "?") if new_dados.get("pagamentos") else "?"
                    pen_count = sum(len(e.get("penAlim", [])) for e in new_ir)
                    ded_count = sum(len(e.get("dedDepen", [])) for e in new_ir)
                    print(f"  Updated id={row['id']} arquivo={row['arquivo_origem']} penAlim={pen_count} dedDepen={ded_count}")

            conn.commit()
            print(f"\nResultado:")
            print(f"  Atualizados: {updated}")
            print(f"  Erros:       {errors}")
            print(f"  Sem mudança: {skipped}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
