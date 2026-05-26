from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2.extras


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))

from esocial.tenant import DEFAULT_EMPRESA_ID, connect_for_empresa  # noqa: E402


PER_APUR = "2025-01"
BACKUP_DIR = ROOT / "relatorio_ana" / "S1210_JANEIRO_REMOVIDO"
TABLES = [
    "s1210_cpf_envios",
    "s1210_cpf_recibo",
    "s1210_lote1_codfunc_scope",
    "s1210_operadoras",
    "s1210_cpf_scope",
    "s1210_xlsx",
]


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


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SELECT to_regclass(%s) AS reg", (table_name,))
    return cursor.fetchone()["reg"] is not None


def fetch_rows(cursor, table_name: str, empresa_id: int) -> list[dict[str, Any]]:
    cursor.execute(
        f"SELECT * FROM {table_name} WHERE empresa_id=%s AND per_apur=%s ORDER BY id",
        (empresa_id, PER_APUR),
    )
    return [dict(row) for row in cursor.fetchall()]


def fetch_counts(cursor, empresa_id: int) -> dict[str, Any]:
    counts: dict[str, Any] = {}
    for table_name in TABLES:
        if not table_exists(cursor, table_name):
            counts[table_name] = {"missing": True, "rows": 0}
            continue
        cursor.execute(
            f"SELECT COUNT(*) AS n FROM {table_name} WHERE empresa_id=%s AND per_apur=%s",
            (empresa_id, PER_APUR),
        )
        counts[table_name] = {"rows": int(cursor.fetchone()["n"])}
    if table_exists(cursor, "v_s1210_contadores"):
        cursor.execute(
            """
            SELECT lote_num, total, ok, erro, enviando, na, pendente
              FROM v_s1210_contadores
             WHERE empresa_id=%s AND per_apur=%s
             ORDER BY lote_num
            """,
            (empresa_id, PER_APUR),
        )
        counts["v_s1210_contadores"] = [dict(row) for row in cursor.fetchall()]
    return counts


def backup_rows(cursor, empresa_id: int) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "empresa_id": empresa_id,
        "per_apur": PER_APUR,
        "before": fetch_counts(cursor, empresa_id),
        "tables": {},
    }
    for table_name in TABLES:
        if table_exists(cursor, table_name):
            payload["tables"][table_name] = fetch_rows(cursor, table_name, empresa_id)
    path = BACKUP_DIR / f"backup_s1210_janeiro_empresa_{empresa_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    return path


def reset_january(empresa_id: int, execute: bool) -> dict[str, Any]:
    conn = connect_for_empresa(empresa_id)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            before = fetch_counts(cursor, empresa_id)
            backup_path = backup_rows(cursor, empresa_id)
            deleted: dict[str, int] = {}
            if execute:
                for table_name in TABLES:
                    if not table_exists(cursor, table_name):
                        deleted[table_name] = 0
                        continue
                    cursor.execute(
                        f"DELETE FROM {table_name} WHERE empresa_id=%s AND per_apur=%s",
                        (empresa_id, PER_APUR),
                    )
                    deleted[table_name] = cursor.rowcount
                after = fetch_counts(cursor, empresa_id)
                conn.commit()
            else:
                after = before
                conn.rollback()
        return {
            "empresa_id": empresa_id,
            "per_apur": PER_APUR,
            "execute": execute,
            "backup": str(backup_path),
            "before": before,
            "deleted": deleted,
            "after": after,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove janeiro/2025 do escopo S-1210 anual com backup JSON.")
    parser.add_argument("--empresa-id", type=int, default=DEFAULT_EMPRESA_ID)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    print(json.dumps(reset_january(args.empresa_id, args.execute), ensure_ascii=False, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
