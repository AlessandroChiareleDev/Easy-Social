"""
API REST para De-Para de campos S-1010 (mapeamento de campos bloqueadores)

Gerencia o mapeamento de campos que precisam ser resolvidos antes do envio:
 - natRubr: natureza da rubrica (Tabela 3)
 - tpRubr: tipo da rubrica (1=Vencimento, 2=Desconto)
 - codIncPisPasep: incidência PIS/PASEP (mapeado para "00")

Endpoints:
- GET  /api/depara/resumo           Dashboard com totais por campo e status
- GET  /api/depara/bloqueadores     Lista detalhada de rubricas bloqueadas
- GET  /api/depara/naturezas        Códigos vigentes da Tabela 3 (para dropdowns)
- POST /api/depara/mapear           Mapear um campo de uma rubrica
- POST /api/depara/mapear-lote      Mapeamento em lote (automáticos)
- GET  /api/depara/preview          Preview dos campos S-1010 prontos para envio
- POST /api/depara/aplicar          Aplica mapeamentos pendentes ao cruzamento
"""

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
import psycopg2.extras

router = APIRouter(prefix="/api/depara", tags=["depara"])

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "easy_social_db"),
    "user": os.environ.get("DB_USER", "easy_social_user"),
    "password": os.environ.get("DB_PASSWORD", "sua_senha_segura"),
}

INIT_SQL = """
CREATE TABLE IF NOT EXISTS esocial_depara (
    id SERIAL PRIMARY KEY,
    cod_rubrica TEXT NOT NULL,
    campo TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT NOT NULL,
    nome_rubrica TEXT,
    regra TEXT DEFAULT 'manual',
    status VARCHAR(20) DEFAULT 'pendente',
    created_at TIMESTAMP DEFAULT NOW(),
    aplicado_em TIMESTAMP,
    UNIQUE(cod_rubrica, campo)
);
"""


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


def _ensure_table():
    """Garante que a tabela esocial_depara existe."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_SQL)
        conn.commit()
    finally:
        conn.close()


# ── Request Models ───────────────────────────────────────────────


class MapearRequest(BaseModel):
    cod_rubrica: str
    campo: str  # 'natRubr', 'tpRubr', 'codIncPisPasep'
    valor_novo: str


class MapearLoteRequest(BaseModel):
    campo: str
    mapeamentos: list[dict]  # [{cod_rubrica, valor_novo, regra}]


# ── Endpoints ────────────────────────────────────────────────────


@router.get("/resumo")
async def get_resumo():
    """Dashboard: contagens por campo e status."""
    _ensure_table()
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Total de rubricas na GL
            cur.execute("SELECT COUNT(*) as total FROM tabela_eventos_gl")
            total_gl = cur.fetchone()["total"]

            # Rubricas com natRubr expirado (bloqueadoras)
            cur.execute("""
                SELECT COUNT(DISTINCT g.raw_data->>'Código') as total
                FROM tabela_eventos_gl g
                LEFT JOIN esocial_tabela3_natureza t3
                    ON CAST(g.raw_data->>'Cód. Natureza' AS INTEGER) = t3.codigo
                WHERE t3.codigo IS NULL
                   OR (t3.dt_fim IS NOT NULL AND t3.dt_fim < CURRENT_DATE)
            """)
            natrubr_bloqueadas = cur.fetchone()["total"]

            # Já resolvidas via staging (correcoes_staging)
            cur.execute("""
                SELECT COUNT(*) as total FROM correcoes_staging
                WHERE status = 'aplicada'
            """)
            resolvidas_staging = cur.fetchone()["total"]

            # De-Para já mapeados
            cur.execute("""
                SELECT
                    campo,
                    status,
                    COUNT(*) as total
                FROM esocial_depara
                GROUP BY campo, status
            """)
            depara_stats = {}
            for row in cur.fetchall():
                campo = row["campo"]
                if campo not in depara_stats:
                    depara_stats[campo] = {"pendente": 0, "aplicado": 0}
                depara_stats[campo][row["status"]] = row["total"]

            # tpRubr: total que TEM valor Tipo no raw_data
            cur.execute("""
                SELECT COUNT(DISTINCT raw_data->>'Código') as total
                FROM tabela_eventos_gl
                WHERE raw_data->>'Tipo' IS NOT NULL
            """)
            tprubr_disponiveis = cur.fetchone()["total"]

            # codIncPisPasep: todos mapeiam para "00"
            cur.execute("""
                SELECT COUNT(DISTINCT raw_data->>'Código') as total
                FROM tabela_eventos_gl
                WHERE raw_data->>'Cód. PIS/PASEP' IS NOT NULL
            """)
            pispasep_disponiveis = cur.fetchone()["total"]

        return {
            "total_rubricas_gl": total_gl,
            "natrubr": {
                "bloqueadas": natrubr_bloqueadas,
                "resolvidas_staging": resolvidas_staging,
                "depara": depara_stats.get("natRubr", {"pendente": 0, "aplicado": 0}),
            },
            "tpRubr": {
                "disponiveis": tprubr_disponiveis,
                "depara": depara_stats.get("tpRubr", {"pendente": 0, "aplicado": 0}),
            },
            "codIncPisPasep": {
                "disponiveis": pispasep_disponiveis,
                "depara": depara_stats.get("codIncPisPasep", {"pendente": 0, "aplicado": 0}),
            },
        }
    finally:
        conn.close()


@router.get("/bloqueadores")
async def get_bloqueadores():
    """Lista rubricas com natRubr expirado/inválido que bloqueiam o envio S-1010."""
    _ensure_table()
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    g.raw_data->>'Código' as cod_rubrica,
                    g.raw_data->>'Descrição' as nome_rubrica,
                    g.raw_data->>'Cód. Natureza' as natrubr_atual,
                    t3.nome as natureza_nome,
                    t3.dt_fim as natureza_expira,
                    CASE
                        WHEN t3.codigo IS NULL THEN 'inexistente'
                        WHEN t3.dt_fim IS NOT NULL AND t3.dt_fim < CURRENT_DATE THEN 'expirado'
                        ELSE 'ok'
                    END as situacao,
                    cs.natureza_nova_codigo as correcao_staging,
                    cs.natureza_nova_nome as correcao_staging_nome,
                    dp.valor_novo as depara_valor,
                    dp.status as depara_status
                FROM tabela_eventos_gl g
                LEFT JOIN esocial_tabela3_natureza t3
                    ON CAST(g.raw_data->>'Cód. Natureza' AS INTEGER) = t3.codigo
                LEFT JOIN correcoes_staging cs
                    ON g.raw_data->>'Código' = cs.codigoevento
                    AND cs.status = 'aplicada'
                LEFT JOIN esocial_depara dp
                    ON g.raw_data->>'Código' = dp.cod_rubrica
                    AND dp.campo = 'natRubr'
                WHERE t3.codigo IS NULL
                   OR (t3.dt_fim IS NOT NULL AND t3.dt_fim < CURRENT_DATE)
                GROUP BY
                    g.raw_data->>'Código',
                    g.raw_data->>'Descrição',
                    g.raw_data->>'Cód. Natureza',
                    t3.nome, t3.dt_fim, t3.codigo,
                    cs.natureza_nova_codigo, cs.natureza_nova_nome,
                    dp.valor_novo, dp.status
                ORDER BY g.raw_data->>'Código'
            """)
            rows = cur.fetchall()

        return {"total": len(rows), "bloqueadores": rows}
    finally:
        conn.close()


@router.get("/naturezas")
async def get_naturezas_vigentes():
    """Retorna códigos vigentes da Tabela 3 para usar nos dropdowns."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT codigo, nome, dt_inicio, dt_fim
                FROM esocial_tabela3_natureza
                WHERE dt_fim IS NULL OR dt_fim >= CURRENT_DATE
                ORDER BY codigo
            """)
            rows = cur.fetchall()

        return {"total": len(rows), "naturezas": rows}
    finally:
        conn.close()


@router.post("/mapear")
async def mapear_campo(req: MapearRequest):
    """Mapeia um campo de uma rubrica específica."""
    if req.campo not in ("natRubr", "tpRubr", "codIncPisPasep"):
        raise HTTPException(status_code=400, detail=f"Campo inválido: {req.campo}")

    _ensure_table()
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Buscar valor anterior
            if req.campo == "natRubr":
                cur.execute(
                    "SELECT raw_data->>'Cód. Natureza' as val FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                    (req.cod_rubrica,),
                )
            elif req.campo == "tpRubr":
                cur.execute(
                    "SELECT raw_data->>'Tipo' as val FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                    (req.cod_rubrica,),
                )
            elif req.campo == "codIncPisPasep":
                cur.execute(
                    "SELECT raw_data->>'Cód. PIS/PASEP' as val FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                    (req.cod_rubrica,),
                )

            row = cur.fetchone()
            valor_anterior = row["val"] if row else None

            # Nome da rubrica
            cur.execute(
                "SELECT raw_data->>'Descrição' as nome FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                (req.cod_rubrica,),
            )
            nome_row = cur.fetchone()
            nome = nome_row["nome"] if nome_row else None

            # Upsert
            cur.execute(
                """
                INSERT INTO esocial_depara (cod_rubrica, campo, valor_anterior, valor_novo, nome_rubrica, regra, status)
                VALUES (%s, %s, %s, %s, %s, 'manual', 'pendente')
                ON CONFLICT (cod_rubrica, campo) DO UPDATE SET
                    valor_anterior = EXCLUDED.valor_anterior,
                    valor_novo = EXCLUDED.valor_novo,
                    nome_rubrica = EXCLUDED.nome_rubrica,
                    regra = 'manual',
                    status = 'pendente',
                    aplicado_em = NULL
                RETURNING *
                """,
                (req.cod_rubrica, req.campo, valor_anterior, req.valor_novo, nome),
            )
            result = cur.fetchone()
        conn.commit()

        return {"success": True, "depara": result}
    finally:
        conn.close()


@router.post("/mapear-lote")
async def mapear_lote(req: MapearLoteRequest):
    """Mapeamento em lote para um campo específico (ex: tpRubr automático)."""
    if req.campo not in ("natRubr", "tpRubr", "codIncPisPasep"):
        raise HTTPException(status_code=400, detail=f"Campo inválido: {req.campo}")

    _ensure_table()
    conn = _get_conn()
    inseridos = 0
    erros = []

    try:
        with conn.cursor() as cur:
            for m in req.mapeamentos:
                cod = m.get("cod_rubrica")
                val = m.get("valor_novo")
                regra = m.get("regra", "automatico")

                if not cod or not val:
                    erros.append({"cod_rubrica": cod, "erro": "Campos obrigatórios ausentes"})
                    continue

                try:
                    # Buscar valor anterior e nome
                    if req.campo == "natRubr":
                        cur.execute(
                            "SELECT raw_data->>'Cód. Natureza' as val, raw_data->>'Descrição' as nome FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                            (cod,),
                        )
                    elif req.campo == "tpRubr":
                        cur.execute(
                            "SELECT raw_data->>'Tipo' as val, raw_data->>'Descrição' as nome FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                            (cod,),
                        )
                    else:
                        cur.execute(
                            "SELECT raw_data->>'Cód. PIS/PASEP' as val, raw_data->>'Descrição' as nome FROM tabela_eventos_gl WHERE raw_data->>'Código' = %s LIMIT 1",
                            (cod,),
                        )

                    row = cur.fetchone()
                    valor_anterior = row[0] if row else None
                    nome = row[1] if row else None

                    cur.execute(
                        """
                        INSERT INTO esocial_depara (cod_rubrica, campo, valor_anterior, valor_novo, nome_rubrica, regra, status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'pendente')
                        ON CONFLICT (cod_rubrica, campo) DO UPDATE SET
                            valor_anterior = EXCLUDED.valor_anterior,
                            valor_novo = EXCLUDED.valor_novo,
                            nome_rubrica = EXCLUDED.nome_rubrica,
                            regra = EXCLUDED.regra,
                            status = 'pendente',
                            aplicado_em = NULL
                        """,
                        (cod, req.campo, valor_anterior, val, nome, regra),
                    )
                    inseridos += 1
                except Exception as e:
                    erros.append({"cod_rubrica": cod, "erro": str(e)})

        conn.commit()
        return {"success": True, "inseridos": inseridos, "erros": erros}
    finally:
        conn.close()


@router.get("/preview")
async def preview_s1010():
    """Preview: mostra como ficará cada rubrica para envio S-1010."""
    _ensure_table()
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT
                    g.raw_data->>'Código' as cod_rubrica,
                    g.raw_data->>'Descrição' as dsc_rubr,
                    g.raw_data->>'Tipo' as tipo_raw,
                    g.raw_data->>'Cód. Natureza' as natrubr_raw,
                    g.raw_data->>'Cód. PIS/PASEP' as pispasep_raw,
                    g.raw_data->>'Cód. INSS' as cod_inss,
                    g.raw_data->>'Cód. IRRF' as cod_irrf,
                    g.raw_data->>'Cód. FGTS' as cod_fgts,
                    -- correcoes de incidencia do Validador
                    rc.inss_correto,
                    rc.irrf_correto,
                    rc.fgts_correto,
                    rc.status as rc_status,
                    -- de-para natRubr
                    dp_nat.valor_novo as natrubr_depara,
                    dp_nat.status as natrubr_depara_status,
                    -- de-para tpRubr
                    dp_tp.valor_novo as tprubr_depara,
                    dp_tp.status as tprubr_depara_status,
                    -- de-para codIncPisPasep
                    dp_pis.valor_novo as pispasep_depara,
                    dp_pis.status as pispasep_depara_status,
                    -- staging (natureza corrigida)
                    cs.natureza_nova_codigo as staging_natrubr,
                    -- tabela 3 status
                    t3.dt_fim as natrubr_expira,
                    CASE
                        WHEN t3.codigo IS NULL THEN 'inexistente'
                        WHEN t3.dt_fim IS NOT NULL AND t3.dt_fim < CURRENT_DATE THEN 'expirado'
                        ELSE 'ok'
                    END as natrubr_status
                FROM tabela_eventos_gl g
                LEFT JOIN rubrica_corrections rc
                    ON g.raw_data->>'Código' = rc.cod_rubrica
                LEFT JOIN esocial_depara dp_nat
                    ON g.raw_data->>'Código' = dp_nat.cod_rubrica AND dp_nat.campo = 'natRubr'
                LEFT JOIN esocial_depara dp_tp
                    ON g.raw_data->>'Código' = dp_tp.cod_rubrica AND dp_tp.campo = 'tpRubr'
                LEFT JOIN esocial_depara dp_pis
                    ON g.raw_data->>'Código' = dp_pis.cod_rubrica AND dp_pis.campo = 'codIncPisPasep'
                LEFT JOIN correcoes_staging cs
                    ON g.raw_data->>'Código' = cs.codigoevento AND cs.status = 'aplicada'
                LEFT JOIN esocial_tabela3_natureza t3
                    ON CAST(g.raw_data->>'Cód. Natureza' AS INTEGER) = t3.codigo
                ORDER BY g.raw_data->>'Código'
            """)
            rows = cur.fetchall()

        # Montar preview com campos finais S-1010
        preview = []
        for r in rows:
            cod = r["cod_rubrica"]

            # natRubr: De-Para > Staging > Raw (verificar se vigente)
            if r.get("natrubr_depara"):
                nat = r["natrubr_depara"]
                nat_fonte = "depara"
            elif r.get("staging_natrubr"):
                nat = r["staging_natrubr"]
                nat_fonte = "staging"
            elif r.get("natrubr_status") == "ok":
                nat = r["natrubr_raw"]
                nat_fonte = "original"
            else:
                nat = None
                nat_fonte = "BLOQUEADO"

            # tpRubr: De-Para > Raw (Vencimento→1, Desconto→2)
            if r.get("tprubr_depara"):
                tp = r["tprubr_depara"]
                tp_fonte = "depara"
            elif r.get("tipo_raw"):
                tipo_map = {"Vencimento": "1", "Desconto": "2"}
                tp = tipo_map.get(r["tipo_raw"])
                tp_fonte = "automatico" if tp else "BLOQUEADO"
            else:
                tp = None
                tp_fonte = "BLOQUEADO"

            # codIncPisPasep: De-Para > sempre "00"
            if r.get("pispasep_depara"):
                pis = r["pispasep_depara"]
                pis_fonte = "depara"
            else:
                pis = "00"
                pis_fonte = "automatico"

            # codIncCP (INSS): Validador corrigido > Raw
            inss = r.get("inss_correto") or r.get("cod_inss")
            irrf = r.get("irrf_correto") or r.get("cod_irrf")
            fgts = r.get("fgts_correto") or r.get("cod_fgts")

            pronto = all([nat, tp, pis, inss, irrf, fgts])

            preview.append({
                "cod_rubrica": cod,
                "dsc_rubr": r.get("dsc_rubr"),
                "natRubr": {"valor": nat, "fonte": nat_fonte},
                "tpRubr": {"valor": tp, "fonte": tp_fonte},
                "codIncPisPasep": {"valor": pis, "fonte": pis_fonte},
                "codIncCP": inss,
                "codIncIRRF": irrf,
                "codIncFGTS": fgts,
                "pronto": pronto,
            })

        total_prontas = sum(1 for p in preview if p["pronto"])
        total_bloqueadas = sum(1 for p in preview if not p["pronto"])

        return {
            "total": len(preview),
            "prontas": total_prontas,
            "bloqueadas": total_bloqueadas,
            "rubricas": preview,
        }
    finally:
        conn.close()


@router.post("/aplicar")
async def aplicar_mapeamentos():
    """Aplica todos os mapeamentos pendentes (marca como aplicado)."""
    _ensure_table()
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE esocial_depara
                SET status = 'aplicado', aplicado_em = NOW()
                WHERE status = 'pendente'
                RETURNING id
                """
            )
            ids = [r[0] for r in cur.fetchall()]
        conn.commit()

        return {"success": True, "aplicados": len(ids), "ids": ids}
    finally:
        conn.close()


@router.post("/auto-popular")
async def auto_popular():
    """
    Pré-popula mapeamentos automáticos:
    1. tpRubr: Vencimento→1, Desconto→2 (para TODAS as rubricas)
    2. codIncPisPasep: 0→00 (para TODAS as rubricas)
    3. natRubr: importa naturezas já corrigidas do staging
    """
    _ensure_table()
    conn = _get_conn()
    resultados = {"tpRubr": 0, "codIncPisPasep": 0, "natRubr_staging": 0, "erros": []}

    try:
        with conn.cursor() as cur:
            # 1. tpRubr automático
            cur.execute("""
                SELECT DISTINCT
                    raw_data->>'Código' as cod,
                    raw_data->>'Tipo' as tipo,
                    raw_data->>'Descrição' as nome
                FROM tabela_eventos_gl
                WHERE raw_data->>'Tipo' IN ('Vencimento', 'Desconto')
            """)
            tipo_map = {"Vencimento": "1", "Desconto": "2"}
            for row in cur.fetchall():
                cod, tipo, nome = row
                val = tipo_map.get(tipo)
                if val:
                    cur.execute(
                        """
                        INSERT INTO esocial_depara (cod_rubrica, campo, valor_anterior, valor_novo, nome_rubrica, regra, status)
                        VALUES (%s, 'tpRubr', %s, %s, %s, 'automatico', 'pendente')
                        ON CONFLICT (cod_rubrica, campo) DO NOTHING
                        """,
                        (cod, tipo, val, nome),
                    )
                    if cur.rowcount > 0:
                        resultados["tpRubr"] += 1

            # 2. codIncPisPasep automático
            cur.execute("""
                SELECT DISTINCT
                    raw_data->>'Código' as cod,
                    raw_data->>'Cód. PIS/PASEP' as pis,
                    raw_data->>'Descrição' as nome
                FROM tabela_eventos_gl
                WHERE raw_data->>'Cód. PIS/PASEP' IS NOT NULL
            """)
            for row in cur.fetchall():
                cod, pis, nome = row
                cur.execute(
                    """
                    INSERT INTO esocial_depara (cod_rubrica, campo, valor_anterior, valor_novo, nome_rubrica, regra, status)
                    VALUES (%s, 'codIncPisPasep', %s, '00', %s, 'automatico', 'pendente')
                    ON CONFLICT (cod_rubrica, campo) DO NOTHING
                    """,
                    (cod, pis, nome),
                )
                if cur.rowcount > 0:
                    resultados["codIncPisPasep"] += 1

            # 3. natRubr do staging (já corrigidos pelo Validador)
            cur.execute("""
                SELECT codigoevento, nome_evento, natureza_anterior, natureza_nova_codigo
                FROM correcoes_staging
                WHERE status = 'aplicada' AND natureza_nova_codigo IS NOT NULL
            """)
            for row in cur.fetchall():
                cod, nome, nat_ant, nat_nova = row
                cur.execute(
                    """
                    INSERT INTO esocial_depara (cod_rubrica, campo, valor_anterior, valor_novo, nome_rubrica, regra, status)
                    VALUES (%s, 'natRubr', %s, %s, %s, 'staging', 'pendente')
                    ON CONFLICT (cod_rubrica, campo) DO NOTHING
                    """,
                    (cod, nat_ant, nat_nova, nome),
                )
                if cur.rowcount > 0:
                    resultados["natRubr_staging"] += 1

        conn.commit()
        return {"success": True, "resultados": resultados}
    finally:
        conn.close()
