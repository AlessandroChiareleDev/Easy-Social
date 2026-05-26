from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2.extras


V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(V2_BACKEND) not in sys.path:
    sys.path.insert(0, str(V2_BACKEND))

from app import db, tenant  # noqa: E402


DEFAULT_BACKUP_DIR = Path("relatorio_ana") / "S1210_NOVEMBRO_SCOPE_RESET"


def json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, memoryview):
        return f"<memoryview {len(value)} bytes>"
    if isinstance(value, bytes):
        return f"<bytes {len(value)} bytes>"
    return str(value)


def fetch_all(cur, sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, args)
    return [dict(row) for row in cur.fetchall()]


def fetch_one(cur, sql: str, args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    cur.execute(sql, args)
    row = cur.fetchone()
    return dict(row) if row else None


def table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
          FROM information_schema.tables
         WHERE table_schema = current_schema()
           AND table_name = %s
        """,
        (table_name,),
    )
    return cur.fetchone() is not None


def safe_rows(cur, sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    try:
        return fetch_all(cur, sql, args)
    except Exception as exc:  # noqa: BLE001
        cur.connection.rollback()
        cur.execute("BEGIN")
        return [{"error": type(exc).__name__, "message": str(exc)[:300]}]


def audit(cur, empresa_id: int, internal_id: int, per_apur: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "empresa_id_externo": empresa_id,
        "empresa_id_interno": internal_id,
        "per_apur": per_apur,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }
    out["tenant"] = fetch_one(
        cur,
        "SELECT current_schema() AS schema, current_setting('search_path') AS search_path, current_database() AS db",
    )
    out["timeline_mes"] = fetch_all(
        cur,
        "SELECT * FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s ORDER BY id",
        (internal_id, per_apur),
    )
    out["timeline_envio"] = fetch_all(
        cur,
        """
        SELECT te.id, te.timeline_mes_id, te.sequencia, te.tipo, te.status,
               te.total_tentados, te.total_sucesso, te.total_erro,
               te.iniciado_em, te.finalizado_em, te.resumo
          FROM timeline_envio te
          JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
         WHERE tm.empresa_id = %s AND tm.per_apur = %s
         ORDER BY te.sequencia, te.id
        """,
        (internal_id, per_apur),
    )
    out["timeline_items_por_status"] = fetch_all(
        cur,
        """
        SELECT it.status, it.erro_codigo, COUNT(*) AS n, COUNT(DISTINCT it.cpf) AS cpfs
          FROM timeline_envio_item it
          JOIN timeline_envio te ON te.id = it.timeline_envio_id
          JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
         WHERE tm.empresa_id = %s AND tm.per_apur = %s AND it.tipo_evento = 'S-1210'
         GROUP BY it.status, it.erro_codigo
         ORDER BY n DESC, it.status, it.erro_codigo
        """,
        (internal_id, per_apur),
    )

    for table_name in ("s1210_cpf_scope", "s1210_cpf_envios", "s1210_cpf_recibo"):
        if table_exists(cur, table_name):
            out[table_name] = fetch_all(
                cur,
                f"SELECT COUNT(*) AS n FROM {table_name} WHERE empresa_id=%s AND per_apur=%s",
                (internal_id, per_apur),
            )
        else:
            out[table_name] = [{"n": 0, "missing": True}]

    out["scope_por_lote"] = []
    if table_exists(cur, "s1210_cpf_scope"):
        out["scope_por_lote"] = fetch_all(
            cur,
            """
            SELECT lote_num, COUNT(*) AS n, COUNT(DISTINCT cpf) AS cpfs,
                   MIN(row_number) AS min_row, MAX(row_number) AS max_row
              FROM s1210_cpf_scope
             WHERE empresa_id = %s AND per_apur = %s
             GROUP BY lote_num
             ORDER BY lote_num
            """,
            (internal_id, per_apur),
        )

    out["explorador_s1210_per"] = fetch_all(
        cur,
        """
        SELECT COUNT(*) AS linhas,
               COUNT(DISTINCT e.cpf) AS cpfs,
               COUNT(*) FILTER (WHERE e.retificado_por_id IS NULL) AS heads_linhas,
               COUNT(DISTINCT e.cpf) FILTER (WHERE e.retificado_por_id IS NULL) AS heads_cpfs,
               COUNT(*) FILTER (WHERE e.origem_envio_id IS NOT NULL) AS com_origem,
               COUNT(DISTINCT e.zip_id) AS zips
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
         WHERE z.empresa_id = %s AND e.tipo_evento = 'S-1210' AND e.per_apur = %s
        """,
        (internal_id, per_apur),
    )
    out["overview_sql"] = fetch_all(
        cur,
        """
        WITH tm AS (
            SELECT id FROM timeline_mes WHERE empresa_id = %s AND per_apur = %s LIMIT 1
        ),
        scope AS (
            SELECT DISTINCT ON (ev.cpf) ev.cpf, ev.origem_envio_id
              FROM explorador_eventos ev, tm
             WHERE ev.tipo_evento = 'S-1210'
               AND ev.per_apur = %s
               AND ev.retificado_por_id IS NULL
               AND ev.cpf IS NOT NULL
             ORDER BY ev.cpf, ev.dt_processamento DESC NULLS LAST, ev.id DESC
        ),
        ult AS (
            SELECT DISTINCT ON (it.cpf) it.cpf, it.status, it.erro_codigo
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id = it.timeline_envio_id
              JOIN timeline_mes tm2 ON tm2.id = te.timeline_mes_id
             WHERE tm2.empresa_id = %s AND tm2.per_apur = %s AND it.tipo_evento = 'S-1210'
             ORDER BY it.cpf, it.criado_em DESC, it.id DESC
        )
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE u.status = 'sucesso') AS ok,
               COUNT(*) FILTER (WHERE u.status LIKE 'erro%%') AS erro,
               COUNT(*) FILTER (WHERE u.status IN ('enviando','processando')) AS enviando,
               COUNT(*) FILTER (WHERE u.status = 'sem_mudanca') AS na,
               COUNT(*) FILTER (
                   WHERE u.status IS NULL
                      OR u.status NOT IN ('sucesso','enviando','processando','sem_mudanca')
                         AND u.status NOT LIKE 'erro%%'
               ) AS pendente,
               COUNT(*) FILTER (WHERE u.status LIKE 'erro%%' AND u.erro_codigo IN ('401','459')) AS recibo_retificado,
               COUNT(*) FILTER (WHERE u.erro_codigo = '202') AS aceito_com_aviso
          FROM scope s
          LEFT JOIN ult u ON u.cpf = s.cpf
        """,
        (internal_id, per_apur, per_apur, internal_id, per_apur),
    )
    out["dtpgto_dist_per"] = fetch_all(
        cur,
        """
        SELECT COALESCE(LEFT(p.item->>'dtPgto', 7), 'sem_dtPgto') AS dtpgto_mes,
               COUNT(DISTINCT e.id) AS eventos,
               COUNT(DISTINCT e.cpf) AS cpfs,
               COUNT(*) AS pagamentos
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
          LEFT JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
         WHERE z.empresa_id = %s AND e.tipo_evento = 'S-1210' AND e.per_apur = %s
         GROUP BY 1
         ORDER BY 1
        """,
        (internal_id, per_apur),
    )
    out["per_vs_dtpgto_alvo"] = fetch_all(
        cur,
        """
        WITH pay AS (
          SELECT e.id, e.cpf, e.per_apur, LEFT(p.item->>'dtPgto', 7) AS dtpgto_mes
            FROM explorador_eventos e
            JOIN empresa_zips_brutos z ON z.id = e.zip_id
            JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
           WHERE z.empresa_id = %s AND e.tipo_evento = 'S-1210'
        )
        SELECT per_apur, dtpgto_mes, COUNT(DISTINCT id) AS eventos,
               COUNT(DISTINCT cpf) AS cpfs, COUNT(*) AS pagamentos
          FROM pay
         WHERE per_apur = %s OR dtpgto_mes = %s
         GROUP BY per_apur, dtpgto_mes
         ORDER BY per_apur, dtpgto_mes
        """,
        (internal_id, per_apur, per_apur),
    )
    out["zips_s1210_per"] = fetch_all(
        cur,
        """
        SELECT z.id, z.nome_arquivo_original, z.dt_ini, z.dt_fim, z.perapur_dominante,
               z.extracao_status, z.total_xmls,
               COUNT(*) AS s1210_linhas, COUNT(DISTINCT e.cpf) AS cpfs,
               MIN(LEFT(p.item->>'dtPgto', 7)) AS min_dtpgto_mes,
               MAX(LEFT(p.item->>'dtPgto', 7)) AS max_dtpgto_mes
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
          LEFT JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
         WHERE z.empresa_id = %s AND e.tipo_evento = 'S-1210' AND e.per_apur = %s
         GROUP BY z.id, z.nome_arquivo_original, z.dt_ini, z.dt_fim,
                  z.perapur_dominante, z.extracao_status, z.total_xmls
         ORDER BY z.id
        """,
        (internal_id, per_apur),
    )
    out["zips_dtpgto_alvo"] = fetch_all(
        cur,
        """
        SELECT z.id, z.nome_arquivo_original, z.dt_ini, z.dt_fim, z.perapur_dominante,
               z.extracao_status, COUNT(DISTINCT e.id) AS eventos,
               COUNT(DISTINCT e.cpf) AS cpfs
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
          JOIN LATERAL jsonb_array_elements(COALESCE(e.dados_json->'pagamentos', '[]'::jsonb)) p(item) ON TRUE
         WHERE z.empresa_id = %s AND e.tipo_evento = 'S-1210' AND LEFT(p.item->>'dtPgto', 7) = %s
         GROUP BY z.id, z.nome_arquivo_original, z.dt_ini, z.dt_fim,
                  z.perapur_dominante, z.extracao_status
         ORDER BY z.id
        """,
        (internal_id, per_apur),
    )
    out["amostras_pendentes"] = fetch_all(
        cur,
        """
        WITH tm AS (
            SELECT id FROM timeline_mes WHERE empresa_id = %s AND per_apur = %s LIMIT 1
        ),
        scope AS (
            SELECT DISTINCT ON (ev.cpf) ev.cpf, ev.id, ev.nr_recibo, ev.zip_id,
                   ev.dt_processamento, ev.dados_json
              FROM explorador_eventos ev, tm
             WHERE ev.tipo_evento = 'S-1210'
               AND ev.per_apur = %s
               AND ev.retificado_por_id IS NULL
               AND ev.cpf IS NOT NULL
             ORDER BY ev.cpf, ev.dt_processamento DESC NULLS LAST, ev.id DESC
        ),
        ult AS (
            SELECT DISTINCT ON (it.cpf) it.cpf, it.status, it.erro_codigo
              FROM timeline_envio_item it
              JOIN timeline_envio te ON te.id = it.timeline_envio_id
              JOIN timeline_mes tm2 ON tm2.id = te.timeline_mes_id
             WHERE tm2.empresa_id = %s AND tm2.per_apur = %s AND it.tipo_evento = 'S-1210'
             ORDER BY it.cpf, it.criado_em DESC, it.id DESC
        )
        SELECT s.cpf, s.id AS evento_id, s.nr_recibo, s.zip_id,
               (
                   SELECT LEFT(x->>'dtPgto', 7)
                     FROM jsonb_array_elements(COALESCE(s.dados_json->'pagamentos', '[]'::jsonb)) x
                    LIMIT 1
               ) AS dtpgto_mes,
               u.status, u.erro_codigo
          FROM scope s
          LEFT JOIN ult u ON u.cpf = s.cpf
         WHERE u.status IS NULL
            OR u.status NOT IN ('sucesso','enviando','processando','sem_mudanca')
               AND u.status NOT LIKE 'erro%%'
         ORDER BY s.cpf
         LIMIT 20
        """,
        (internal_id, per_apur, per_apur, internal_id, per_apur),
    )
    return out


def selected_explorador_columns(cur) -> str:
    cur.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = 'explorador_eventos'
         ORDER BY ordinal_position
        """
    )
    columns = [row["column_name"] for row in cur.fetchall()]
    skip = {"xml_bytes"}
    return ", ".join(f"e.{name}" for name in columns if name not in skip)


def backup_rows(cur, empresa_id: int, internal_id: int, per_apur: str, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = backup_dir / f"backup_escopo_s1210_{per_apur.replace('-', '')}_{stamp}.json"
    timeline_mes = fetch_all(
        cur,
        "SELECT * FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s ORDER BY id",
        (internal_id, per_apur),
    )
    timeline_envio = fetch_all(
        cur,
        """
        SELECT te.*
          FROM timeline_envio te
          JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
         WHERE tm.empresa_id = %s AND tm.per_apur = %s
         ORDER BY te.sequencia, te.id
        """,
        (internal_id, per_apur),
    )
    envio_ids = [row["id"] for row in timeline_envio]
    timeline_items: list[dict[str, Any]] = []
    if envio_ids:
        timeline_items = fetch_all(
            cur,
            """
            SELECT *
              FROM timeline_envio_item
             WHERE timeline_envio_id = ANY(%s)
             ORDER BY timeline_envio_id, id
            """,
            (envio_ids,),
        )
    cols = selected_explorador_columns(cur)
    explorador = fetch_all(
        cur,
        f"""
        SELECT {cols}
          FROM explorador_eventos e
          JOIN empresa_zips_brutos z ON z.id = e.zip_id
         WHERE z.empresa_id = %s
           AND e.tipo_evento = 'S-1210'
           AND e.per_apur = %s
         ORDER BY e.id
        """,
        (internal_id, per_apur),
    )
    legacy: dict[str, list[dict[str, Any]]] = {}
    for table_name in ("s1210_cpf_scope", "s1210_cpf_envios", "s1210_cpf_recibo"):
        if table_exists(cur, table_name):
            legacy[table_name] = fetch_all(
                cur,
                f"SELECT * FROM {table_name} WHERE empresa_id=%s AND per_apur=%s ORDER BY 1",
                (internal_id, per_apur),
            )
        else:
            legacy[table_name] = []
    payload = {
        "backup_kind": "s1210_scope_reset",
        "empresa_id_externo": empresa_id,
        "empresa_id_interno": internal_id,
        "per_apur": per_apur,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "timeline_mes": timeline_mes,
        "timeline_envio": timeline_envio,
        "timeline_envio_item": timeline_items,
        "explorador_eventos_s1210_sem_xml_bytes": explorador,
        "legacy": legacy,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, default=json_default, indent=2), encoding="utf-8")
    return path


def reset_scope(cur, internal_id: int, per_apur: str) -> dict[str, int]:
    timeline_mes_rows = fetch_all(
        cur,
        "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s FOR UPDATE",
        (internal_id, per_apur),
    )
    timeline_mes_ids = [row["id"] for row in timeline_mes_rows]
    envio_ids: list[int] = []
    if timeline_mes_ids:
        envio_ids = [
            row["id"]
            for row in fetch_all(
                cur,
                "SELECT id FROM timeline_envio WHERE timeline_mes_id = ANY(%s) ORDER BY id FOR UPDATE",
                (timeline_mes_ids,),
            )
        ]

    counts = {
        "origem_envio_null": 0,
        "timeline_envio_item_deleted": 0,
        "timeline_envio_deleted": 0,
        "timeline_mes_deleted": 0,
        "s1210_cpf_scope_deleted": 0,
        "s1210_cpf_envios_deleted": 0,
        "s1210_cpf_recibo_deleted": 0,
    }

    if envio_ids:
        cur.execute(
            """
            UPDATE explorador_eventos e
               SET origem_envio_id = NULL
              FROM empresa_zips_brutos z
             WHERE z.id = e.zip_id
               AND z.empresa_id = %s
               AND e.tipo_evento = 'S-1210'
               AND e.per_apur = %s
               AND e.origem_envio_id = ANY(%s)
            """,
            (internal_id, per_apur, envio_ids),
        )
        counts["origem_envio_null"] = cur.rowcount
        cur.execute("DELETE FROM timeline_envio_item WHERE timeline_envio_id = ANY(%s)", (envio_ids,))
        counts["timeline_envio_item_deleted"] = cur.rowcount

    if timeline_mes_ids:
        cur.execute("UPDATE timeline_mes SET head_envio_id = NULL WHERE id = ANY(%s)", (timeline_mes_ids,))
        cur.execute("DELETE FROM timeline_envio WHERE timeline_mes_id = ANY(%s)", (timeline_mes_ids,))
        counts["timeline_envio_deleted"] = cur.rowcount
        cur.execute("DELETE FROM timeline_mes WHERE id = ANY(%s)", (timeline_mes_ids,))
        counts["timeline_mes_deleted"] = cur.rowcount

    for table_name, key in (
        ("s1210_cpf_scope", "s1210_cpf_scope_deleted"),
        ("s1210_cpf_envios", "s1210_cpf_envios_deleted"),
        ("s1210_cpf_recibo", "s1210_cpf_recibo_deleted"),
    ):
        if table_exists(cur, table_name):
            cur.execute(
                f"DELETE FROM {table_name} WHERE empresa_id=%s AND per_apur=%s",
                (internal_id, per_apur),
            )
            counts[key] = cur.rowcount
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita e zera escopo/timeline S-1210 de um mês.")
    parser.add_argument("--empresa-id", type=int, default=2)
    parser.add_argument("--per-apur", default="2025-11")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--apply", action="store_true", help="Executa a remoção; sem isso roda dry-run.")
    args = parser.parse_args()

    internal_id = tenant.internal_empresa_id(args.empresa_id)
    conn = db.connect(empresa_id=args.empresa_id)
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            before = audit(cur, args.empresa_id, internal_id, args.per_apur)
            if not args.apply:
                conn.rollback()
                print(json.dumps({"mode": "dry-run", "before": before}, ensure_ascii=False, default=json_default, indent=2))
                return 0

            backup_path = backup_rows(cur, args.empresa_id, internal_id, args.per_apur, args.backup_dir)
            counts = reset_scope(cur, internal_id, args.per_apur)
            after = audit(cur, args.empresa_id, internal_id, args.per_apur)
            conn.commit()
            print(
                json.dumps(
                    {
                        "mode": "apply",
                        "backup_path": str(backup_path),
                        "deleted_or_reset": counts,
                        "before": before,
                        "after": after,
                    },
                    ensure_ascii=False,
                    default=json_default,
                    indent=2,
                )
            )
            return 0
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())