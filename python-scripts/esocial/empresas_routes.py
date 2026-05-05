"""Endpoints de empresas (multi-tenant base).

Lista master_empresas pra alimentar dropdowns no frontend.
"""
from __future__ import annotations

import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException

from db_config import DB_CONFIG

router = APIRouter(prefix="/api", tags=["empresas"])


def _db():
    return psycopg2.connect(**DB_CONFIG)


@router.get("/empresas")
def listar_empresas():
    """Retorna empresas ativas pra dropdown."""
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
        return {"empresas": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"erro ao listar empresas: {e}")
