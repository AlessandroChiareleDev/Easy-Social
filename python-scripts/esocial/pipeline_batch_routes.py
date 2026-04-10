"""
Pipeline Batch Routes — API para acompanhar execuções do pipeline 98-10-99.
Tabelas: pipeline_runs, pipeline_cpf_results
"""
import json
import logging
import psycopg2
import psycopg2.extras
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from db_config import DB_CONFIG

logger = logging.getLogger("pipeline_batch")
router = APIRouter(prefix="/api/pipeline-batch", tags=["pipeline-batch"])

# ── DDL ───────────────────────────────────────────────────────

INIT_SQL = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'pipeline_runs') THEN
        CREATE TABLE pipeline_runs (
            id              SERIAL PRIMARY KEY,
            per_apur        VARCHAR(7) NOT NULL,
            status          VARCHAR(20) NOT NULL DEFAULT 'preparando',
            total_cpfs      INT DEFAULT 0,
            cpfs_ok         INT DEFAULT 0,
            cpfs_erro       INT DEFAULT 0,
            cpfs_ignorados  INT DEFAULT 0,
            s1298_done      BOOLEAN DEFAULT FALSE,
            s1298_recibo    VARCHAR(100),
            s1299_done      BOOLEAN DEFAULT FALSE,
            s1299_recibo    VARCHAR(100),
            lote_atual      INT DEFAULT 0,
            total_lotes     INT DEFAULT 0,
            started_at      TIMESTAMPTZ DEFAULT NOW(),
            finished_at     TIMESTAMPTZ,
            erro_fatal      TEXT
        );
    END IF;

    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'pipeline_cpf_results') THEN
        CREATE TABLE pipeline_cpf_results (
            id                  SERIAL PRIMARY KEY,
            run_id              INT NOT NULL REFERENCES pipeline_runs(id) ON DELETE CASCADE,
            cpf                 VARCHAR(11) NOT NULL,
            status              VARCHAR(20) NOT NULL DEFAULT 'pendente',
            nr_recibo_original  VARCHAR(100),
            nr_recibo_novo      VARCHAR(100),
            pagamentos          JSONB,
            info_ir_cr          JSONB,
            erro_descricao      TEXT,
            lote_num            INT,
            processed_at        TIMESTAMPTZ
        );
        CREATE INDEX idx_pcr_run_id ON pipeline_cpf_results(run_id);
        CREATE INDEX idx_pcr_cpf ON pipeline_cpf_results(cpf);
        CREATE INDEX idx_pcr_status ON pipeline_cpf_results(status);
    END IF;
END $$;
"""


def _get_conn():
    return psycopg2.connect(
        **DB_CONFIG,
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3,
    )


def _init_tables():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
        conn.commit()
    finally:
        conn.close()


# Init on import
try:
    _init_tables()
    logger.info("pipeline_runs / pipeline_cpf_results tables OK")
except Exception as e:
    logger.warning(f"Could not init pipeline batch tables: {e}")


# ── GET /runs ─────────────────────────────────────────────────

@router.get("/runs")
async def list_runs(per_apur: Optional[str] = Query(None)):
    """Lista execuções do pipeline, opcionalmente filtradas por período."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if per_apur:
                cur.execute("""
                    SELECT id, per_apur, status, total_cpfs, cpfs_ok, cpfs_erro, cpfs_ignorados,
                           s1298_done, s1299_done, lote_atual, total_lotes,
                           started_at, finished_at
                    FROM pipeline_runs
                    WHERE per_apur = %s
                    ORDER BY id DESC
                """, (per_apur,))
            else:
                cur.execute("""
                    SELECT id, per_apur, status, total_cpfs, cpfs_ok, cpfs_erro, cpfs_ignorados,
                           s1298_done, s1299_done, lote_atual, total_lotes,
                           started_at, finished_at
                    FROM pipeline_runs
                    ORDER BY id DESC
                    LIMIT 50
                """)
            return cur.fetchall()
    finally:
        conn.close()


# ── GET /runs/{id} ────────────────────────────────────────────

@router.get("/runs/{run_id}")
async def get_run(run_id: int):
    """Detalhes de uma execução específica."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM pipeline_runs WHERE id = %s
            """, (run_id,))
            run = cur.fetchone()
            if not run:
                raise HTTPException(status_code=404, detail="Run não encontrada")
            return run
    finally:
        conn.close()


# ── GET /runs/{id}/cpfs ───────────────────────────────────────

@router.get("/runs/{run_id}/cpfs")
async def list_run_cpfs(
    run_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Lista paginada de CPFs de uma run com seus resultados."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Verify run exists
            cur.execute("SELECT id FROM pipeline_runs WHERE id = %s", (run_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Run não encontrada")

            conditions = ["run_id = %s"]
            params = [run_id]

            if status:
                conditions.append("status = %s")
                params.append(status)

            if search:
                clean = search.replace(".", "").replace("-", "").strip()
                conditions.append("cpf LIKE %s")
                params.append(f"%{clean}%")

            where = "WHERE " + " AND ".join(conditions)

            # Count
            cur.execute(f"SELECT COUNT(*) as total FROM pipeline_cpf_results {where}", params)
            total = cur.fetchone()["total"]

            # Fetch page
            offset = (page - 1) * page_size
            cur.execute(f"""
                SELECT id, cpf, status, nr_recibo_original, nr_recibo_novo,
                       pagamentos, info_ir_cr, erro_descricao, lote_num, processed_at
                FROM pipeline_cpf_results
                {where}
                ORDER BY
                    CASE status
                        WHEN 'erro' THEN 0
                        WHEN 'pendente' THEN 1
                        WHEN 'ok' THEN 2
                    END,
                    cpf
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            items = cur.fetchall()

            total_pages = (total + page_size - 1) // page_size if total > 0 else 1

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "items": items,
            }
    finally:
        conn.close()


# ── GET /runs/{id}/cpfs/{cpf} ─────────────────────────────────

@router.get("/runs/{run_id}/cpfs/{cpf}")
async def get_run_cpf_detail(run_id: int, cpf: str):
    """Detalhe completo de um CPF numa run."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM pipeline_cpf_results
                WHERE run_id = %s AND cpf = %s
            """, (run_id, cpf))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="CPF não encontrado nessa run")
            return row
    finally:
        conn.close()


# ── GET /runs/{id}/progresso ──────────────────────────────────

@router.get("/runs/{run_id}/progresso")
async def get_run_progress(run_id: int):
    """Progresso em tempo real de uma run."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT status, total_cpfs, cpfs_ok, cpfs_erro,
                       lote_atual, total_lotes, s1298_done, s1299_done,
                       started_at, finished_at, erro_fatal
                FROM pipeline_runs WHERE id = %s
            """, (run_id,))
            run = cur.fetchone()
            if not run:
                raise HTTPException(status_code=404, detail="Run não encontrada")

            processados = run["cpfs_ok"] + run["cpfs_erro"]
            pct = round((processados / run["total_cpfs"]) * 100, 1) if run["total_cpfs"] > 0 else 0

            return {
                **run,
                "processados": processados,
                "percentual": pct,
                "rodando": run["status"] == "rodando",
            }
    finally:
        conn.close()


# ── GET /periodos ─────────────────────────────────────────────

@router.get("/periodos")
async def list_periodos():
    """Lista períodos disponíveis (dos runs existentes + do explorador)."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT per_apur FROM (
                    SELECT per_apur FROM pipeline_runs
                    UNION
                    SELECT DISTINCT per_apur FROM explorador_eventos
                    WHERE tipo_evento = 'S-1210' AND per_apur IS NOT NULL
                ) sub
                ORDER BY per_apur DESC
            """)
            return [r["per_apur"] for r in cur.fetchall()]
    finally:
        conn.close()
