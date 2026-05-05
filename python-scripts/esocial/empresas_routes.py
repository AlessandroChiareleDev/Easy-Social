"""Endpoints de empresas (multi-tenant base).

Lista master_empresas pra alimentar dropdowns/seletores no frontend,
incluindo a flag tem_dados (S-1210 ja ingerido) e db_kind.
"""
from __future__ import annotations

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException

from db_config import DB_CONFIG
from esocial.tenant import get_db_config_for_empresa, db_kind_for_empresa

router = APIRouter(prefix="/api", tags=["empresas"])


def _db():
    return psycopg2.connect(**DB_CONFIG)


def _conta_dados(empresa_id: int) -> dict:
    """Conta envios + xlsx no banco da empresa pra dizer se ela ja tem operacao."""
    cfg = get_db_config_for_empresa(empresa_id)
    out = {"xlsx": 0, "envios": 0}
    try:
        with psycopg2.connect(**cfg) as c:
            with c.cursor() as cur:
                cur.execute("SELECT to_regclass('public.s1210_xlsx')")
                if cur.fetchone()[0]:
                    cur.execute(
                        "SELECT COUNT(*) FROM s1210_xlsx WHERE empresa_id=%s",
                        (empresa_id,),
                    )
                    out["xlsx"] = int(cur.fetchone()[0])
                cur.execute("SELECT to_regclass('public.s1210_cpf_envios')")
                if cur.fetchone()[0]:
                    cur.execute(
                        "SELECT COUNT(*) FROM s1210_cpf_envios WHERE empresa_id=%s",
                        (empresa_id,),
                    )
                    out["envios"] = int(cur.fetchone()[0])
    except Exception:
        pass
    return out


@router.get("/empresas")
def listar_empresas():
    """Retorna empresas ativas + flag tem_dados + db_kind."""
    try:
        with _db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, nome, cnpj, ativo
                      FROM master_empresas
                     WHERE ativo IS TRUE
                     ORDER BY id
                    """
                )
                rows = cur.fetchall()

        empresas = []
        for r in rows:
            d = dict(r)
            counts = _conta_dados(int(d["id"]))
            d["xlsx_count"] = counts["xlsx"]
            d["envios_count"] = counts["envios"]
            d["tem_dados"] = (counts["xlsx"] + counts["envios"]) > 0
            d["db_kind"] = db_kind_for_empresa(int(d["id"]))
            empresas.append(d)
        return {"empresas": empresas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"erro ao listar empresas: {e}")
