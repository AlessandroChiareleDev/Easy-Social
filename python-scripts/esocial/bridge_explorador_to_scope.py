"""
Bridge: popula s1210_xlsx + s1210_cpf_scope a partir dos S-1210 ja
importados em explorador_eventos. Assim a tela "S-1210 Anual" do V2
mostra TODOS esses CPFs como PENDENTES (sem fazer envio nenhum).

NAO toca em s1210_cpf_envios. Quem nao tem envio = pendente automatico
(via view v_s1210_contadores).

Uso:
  python -m esocial.bridge_explorador_to_scope --empresa-id 2
  python -m esocial.bridge_explorador_to_scope --empresa-id 2 --per-apur 2025-12
  python -m esocial.bridge_explorador_to_scope --empresa-id 2 --reset
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path
from typing import Optional

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from esocial.tenant import connect_for_empresa  # noqa: E402


def _ensure_virtual_xlsx(cur, empresa_id: int, per_apur: str) -> int:
    """Cria (ou reusa) a linha sintetica em s1210_xlsx para o periodo."""
    sha = hashlib.sha256(f"virtual:{empresa_id}:{per_apur}".encode()).hexdigest()
    cur.execute(
        "SELECT id FROM s1210_xlsx WHERE empresa_id=%s AND per_apur=%s AND sha256=%s",
        (empresa_id, per_apur, sha),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        """
        INSERT INTO s1210_xlsx
          (empresa_id, per_apur, nome_arquivo, tamanho_bytes, sha256,
           storage_path, aba_geral, aba_operadoras, parse_ok, totais_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s::jsonb)
        RETURNING id
        """,
        (
            empresa_id,
            per_apur,
            f"virtual_xml_dump_{per_apur}.xlsx",
            0,
            sha,
            f"virtual/xml/{empresa_id}/{per_apur}",
            "Geral",
            None,
            '{"fonte":"explorador_eventos"}',
        ),
    )
    return cur.fetchone()[0]


def populate(
    empresa_id: int,
    per_apur: Optional[str] = None,
    reset: bool = False,
) -> dict:
    conn = connect_for_empresa(empresa_id)
    conn.autocommit = False
    cur = conn.cursor()

    stats = {"periodos": 0, "cpfs_inseridos": 0, "cpfs_dup": 0, "ja_existiam": 0}
    t0 = time.time()

    try:
        if reset:
            cur.execute(
                "DELETE FROM s1210_cpf_scope WHERE empresa_id=%s "
                + ("AND per_apur=%s" if per_apur else ""),
                (empresa_id, per_apur) if per_apur else (empresa_id,),
            )
            print(f"[reset] removidos {cur.rowcount} de s1210_cpf_scope")
            cur.execute(
                "DELETE FROM s1210_xlsx WHERE empresa_id=%s AND sha256 LIKE %s "
                + ("AND per_apur=%s" if per_apur else ""),
                (
                    (empresa_id, "%", per_apur)
                    if per_apur
                    else (empresa_id, "%")
                ),
            )
            print(f"[reset] removidas {cur.rowcount} linhas virtuais de s1210_xlsx")
            conn.commit()

        # 1. Listar periodos com S-1210 (ou filtrado)
        if per_apur:
            cur.execute(
                "SELECT %s::text AS per_apur, COUNT(DISTINCT cpf) AS qt "
                "FROM explorador_eventos "
                "WHERE tipo_evento='S-1210' AND per_apur=%s "
                "AND cpf IS NOT NULL AND cpf <> ''",
                (per_apur, per_apur),
            )
        else:
            cur.execute(
                "SELECT per_apur, COUNT(DISTINCT cpf) AS qt "
                "FROM explorador_eventos "
                "WHERE tipo_evento='S-1210' "
                "AND cpf IS NOT NULL AND cpf <> '' "
                "AND per_apur IS NOT NULL AND per_apur <> '' "
                "GROUP BY per_apur ORDER BY 1"
            )
        periodos = cur.fetchall()
        if not periodos:
            print("[warn] nada encontrado em explorador_eventos para o filtro.")
            return stats

        for per, qt in periodos:
            stats["periodos"] += 1
            print(f"\n=== {per} ({qt} CPFs unicos) ===")

            xlsx_id = _ensure_virtual_xlsx(cur, empresa_id, per)
            print(f"  xlsx virtual id={xlsx_id}")

            # CPF + (1o nome encontrado nos dados, se houver)
            cur.execute(
                """
                INSERT INTO s1210_cpf_scope
                  (xlsx_id, empresa_id, per_apur, cpf, lote_num, raw_row)
                SELECT %s, %s, %s, cpf, 1,
                       jsonb_build_object('fonte','explorador_eventos','count', cnt)
                  FROM (
                    SELECT cpf, COUNT(*) AS cnt
                      FROM explorador_eventos
                     WHERE tipo_evento='S-1210' AND per_apur=%s
                       AND cpf IS NOT NULL AND cpf <> ''
                     GROUP BY cpf
                  ) t
                ON CONFLICT (empresa_id, per_apur, cpf) DO NOTHING
                """,
                (xlsx_id, empresa_id, per, per),
            )
            inseridos = cur.rowcount
            stats["cpfs_inseridos"] += inseridos
            stats["cpfs_dup"] += int(qt) - inseridos
            print(f"  inseridos={inseridos}  dup={int(qt) - inseridos}")
            conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"[err] {e}")
        raise
    finally:
        cur.close()
        conn.close()

    print(f"\n==== CONCLUIDO em {time.time()-t0:.1f}s ====")
    print(stats)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--empresa-id", type=int, required=True)
    ap.add_argument("--per-apur", default=None, help="ex: 2025-12 (omitir = todos)")
    ap.add_argument(
        "--reset",
        action="store_true",
        help="apaga scope+xlsx virtuais antes de popular",
    )
    args = ap.parse_args()
    populate(args.empresa_id, args.per_apur, args.reset)


if __name__ == "__main__":
    main()
