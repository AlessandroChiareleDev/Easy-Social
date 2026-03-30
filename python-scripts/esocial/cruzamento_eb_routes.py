"""
Rotas para consulta da tabela cruzamento_eb (EB Skills Cruzamentos).
"""
from fastapi import APIRouter, Query
import psycopg2
import psycopg2.extras
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_config import DB_CONFIG

router = APIRouter(prefix="/api/cruzamento-eb", tags=["Cruzamento EB"])


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


@router.get("/rubricas")
def listar_rubricas(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=10, le=500),
    search: str = Query("", description="Busca por código ou descrição"),
    filtro: str = Query("todas", description="todas | inconsistentes | regulares | corrigidos | pendentes"),
):
    """Retorna as rubricas do cruzamento EB Skills com paginação e filtros."""
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Base query
    where_clauses = []
    params = []

    if search:
        where_clauses.append(
            "(cod_rubrica ILIKE %s OR descricao ILIKE %s)"
        )
        params.extend([f"%{search}%", f"%{search}%"])

    if filtro == "inconsistentes":
        where_clauses.append("""(
            incid_inss != SPLIT_PART(incid_base_legal_inss, ' - ', 1)
            OR incid_irrf != SPLIT_PART(incid_base_legal_irrf, ' - ', 1)
            OR incid_fgts != SPLIT_PART(incid_base_legal_fgts, ' - ', 1)
        )""")
    elif filtro == "regulares":
        where_clauses.append("""(
            incid_inss = SPLIT_PART(incid_base_legal_inss, ' - ', 1)
            AND incid_irrf = SPLIT_PART(incid_base_legal_irrf, ' - ', 1)
            AND incid_fgts = SPLIT_PART(incid_base_legal_fgts, ' - ', 1)
        )""")
    elif filtro == "corrigidos":
        where_clauses.append("corrigido = TRUE")
    elif filtro == "pendentes":
        where_clauses.append("""(
            (incid_inss != SPLIT_PART(incid_base_legal_inss, ' - ', 1)
            OR incid_irrf != SPLIT_PART(incid_base_legal_irrf, ' - ', 1)
            OR incid_fgts != SPLIT_PART(incid_base_legal_fgts, ' - ', 1))
            AND corrigido = FALSE
        )""")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Count
    cur.execute(f"SELECT COUNT(*) FROM cruzamento_eb WHERE {where_sql}", params)
    total = cur.fetchone()["count"]

    # Data
    offset = (page - 1) * per_page
    cur.execute(
        f"""SELECT * FROM cruzamento_eb
            WHERE {where_sql}
            ORDER BY cod_rubrica::int
            LIMIT %s OFFSET %s""",
        params + [per_page, offset],
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "rubricas": rows,
    }


@router.get("/resumo")
def resumo():
    """Retorna contadores gerais do cruzamento."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM cruzamento_eb")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM cruzamento_eb
        WHERE incid_inss != SPLIT_PART(incid_base_legal_inss, ' - ', 1)
           OR incid_irrf != SPLIT_PART(incid_base_legal_irrf, ' - ', 1)
           OR incid_fgts != SPLIT_PART(incid_base_legal_fgts, ' - ', 1)
    """)
    inconsistentes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM cruzamento_eb WHERE corrigido = TRUE")
    corrigidos = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total": total,
        "inconsistentes": inconsistentes,
        "regulares": total - inconsistentes,
        "corrigidos": corrigidos,
    }


@router.post("/marcar-corrigido/{cod_rubrica}")
def marcar_corrigido(cod_rubrica: str):
    """Marca uma rubrica como corrigida."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cruzamento_eb SET corrigido = TRUE, corrigido_em = NOW() WHERE cod_rubrica = %s",
        (cod_rubrica,),
    )
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    if affected == 0:
        return {"success": False, "message": f"Rubrica {cod_rubrica} não encontrada"}
    return {"success": True, "message": f"Rubrica {cod_rubrica} marcada como corrigida"}


@router.post("/desmarcar-corrigido/{cod_rubrica}")
def desmarcar_corrigido(cod_rubrica: str):
    """Remove a marcação de corrigida de uma rubrica."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE cruzamento_eb SET corrigido = FALSE, corrigido_em = NULL WHERE cod_rubrica = %s",
        (cod_rubrica,),
    )
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    if affected == 0:
        return {"success": False, "message": f"Rubrica {cod_rubrica} não encontrada"}
    return {"success": True, "message": f"Rubrica {cod_rubrica} desmarcada"}
