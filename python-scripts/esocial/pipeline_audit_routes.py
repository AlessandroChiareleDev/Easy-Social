"""
Rotas Pipeline Audit — Snapshots pré/pós pipeline para comprovação
"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_config import DB_CONFIG

router = APIRouter(prefix="/api/pipeline-audit", tags=["pipeline-audit"])


class CapturaSnapshotRequest(BaseModel):
    cpf: str
    per_apur: str
    tipo: str = "pre_pipeline"  # "pre_pipeline" ou "pos_pipeline"
    descricao: str = ""
    rubrica_ids: list[str] = ["566", "596"]


@router.get("/snapshots")
async def listar_snapshots():
    """Lista todos os snapshots de pipeline (resumo)."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, cpf, per_apur, tipo, created_at,
                   dados->>'descricao' as descricao
            FROM pipeline_audit
            ORDER BY id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return {"snapshots": rows}
    finally:
        cur.close()
        conn.close()


@router.get("/snapshots/{snapshot_id}")
async def obter_snapshot(snapshot_id: int):
    """Retorna um snapshot completo com todos os dados."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, cpf, per_apur, tipo, dados, created_at
            FROM pipeline_audit
            WHERE id = %s
        """, (snapshot_id,))
        row = cur.fetchone()
        if not row:
            return {"error": "Snapshot não encontrado"}, 404
        result = dict(row)
        if result.get("created_at"):
            result["created_at"] = result["created_at"].isoformat()
        return {"snapshot": result}
    finally:
        cur.close()
        conn.close()


@router.get("/comparar/{cpf}")
async def comparar_snapshots(cpf: str):
    """Compara snapshots pré e pós pipeline para um CPF."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, cpf, per_apur, tipo, dados, created_at
            FROM pipeline_audit
            WHERE cpf = %s
            ORDER BY created_at ASC
        """, (cpf,))
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()

        pre = [r for r in rows if r["tipo"] == "pre_pipeline"]
        pos = [r for r in rows if r["tipo"] == "pos_pipeline"]

        comparacao = None
        if pre and pos:
            pre_dados = pre[-1]["dados"]
            pos_dados = pos[-1]["dados"]
            comparacao = _gerar_comparacao(pre_dados, pos_dados)

        return {
            "cpf": cpf,
            "snapshots": rows,
            "comparacao": comparacao,
        }
    finally:
        cur.close()
        conn.close()


def _gerar_comparacao(pre: dict, pos: dict) -> dict:
    """Gera diff entre snapshot pré e pós."""
    diff = {}

    # Comparar cruzamento_eb
    pre_rubricas = {r["cod_rubrica"]: r for r in pre.get("cruzamento_eb", [])}
    pos_rubricas = {r["cod_rubrica"]: r for r in pos.get("cruzamento_eb", [])}

    mudancas_rubricas = []
    for cod, pre_r in pre_rubricas.items():
        pos_r = pos_rubricas.get(cod, {})
        campos_mudados = {}
        for campo in ["incid_irrf", "incid_inss", "incid_fgts", "corrigido", "envio_status"]:
            if str(pre_r.get(campo)) != str(pos_r.get(campo)):
                campos_mudados[campo] = {
                    "antes": pre_r.get(campo),
                    "depois": pos_r.get(campo),
                }
        if campos_mudados:
            mudancas_rubricas.append({
                "cod_rubrica": cod,
                "descricao": pre_r.get("descricao", ""),
                "mudancas": campos_mudados,
            })
    diff["rubricas"] = mudancas_rubricas

    # Comparar S-5002
    pre_s5002 = pre.get("s5002_vigente", {}).get("totalizadores", [])
    pos_s5002 = pos.get("s5002_vigente", {}).get("totalizadores", [])
    diff["s5002"] = {
        "antes": pre_s5002,
        "depois": pos_s5002,
    }

    # Comparar recibos
    diff["recibos"] = {
        "antes": pre.get("recibos_vigentes", {}),
        "depois": pos.get("recibos_vigentes", {}),
    }

    return diff


@router.post("/capturar")
async def capturar_snapshot(req: CapturaSnapshotRequest):
    """
    Captura snapshot do estado atual para comprovação PRÉ ou PÓS pipeline.
    Grava automaticamente no banco (pipeline_audit).
    """
    if req.tipo not in ("pre_pipeline", "pos_pipeline"):
        raise HTTPException(400, "tipo deve ser 'pre_pipeline' ou 'pos_pipeline'")
    if not req.cpf or len(req.cpf) != 11:
        raise HTTPException(400, "CPF deve ter 11 dígitos")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        snapshot_dados: dict = {
            "cpf": req.cpf,
            "per_apur": req.per_apur,
            "capturado_em": datetime.now().isoformat(),
            "tipo": req.tipo,
            "descricao": req.descricao or f"Snapshot {req.tipo} capturado pelo frontend",
        }

        # 1. cruzamento_eb (rubricas alvo)
        cur.execute("""
            SELECT cod_rubrica, descricao, cod_natureza,
                   incid_inss, incid_irrf, incid_fgts,
                   incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts,
                   corrigido, corrigido_em, envio_status, ini_valid_esocial
            FROM cruzamento_eb
            WHERE cod_rubrica = ANY(%s)
            ORDER BY CAST(cod_rubrica AS int)
        """, (req.rubrica_ids,))
        rubricas = [dict(r) for r in cur.fetchall()]
        for r in rubricas:
            if r.get("corrigido_em"):
                r["corrigido_em"] = r["corrigido_em"].isoformat()
        snapshot_dados["cruzamento_eb"] = rubricas

        # 2. Histórico de envios
        cur.execute("""
            SELECT id, tipo_evento, modo, status, protocolo_envio,
                   codigo_resposta, descricao_resposta, total_eventos,
                   rubrica_ids, ambiente, ini_valid, created_at
            FROM esocial_envios
            ORDER BY id DESC LIMIT 10
        """)
        envios = [dict(r) for r in cur.fetchall()]
        for r in envios:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        snapshot_dados["esocial_envios"] = envios

        # 3. Config eSocial
        cur.execute("SELECT * FROM config_esocial LIMIT 5")
        configs = [dict(r) for r in cur.fetchall()]
        for r in configs:
            if r.get("updated_at"):
                r["updated_at"] = r["updated_at"].isoformat()
        snapshot_dados["config_esocial"] = configs

        # 4. Pipeline_correcao (últimos runs)
        try:
            cur.execute("""
                SELECT id, cpf, per_apur, ambiente, status, step_atual, erro,
                       s1010_nr_recibo, s1298_nr_recibo, s1200_nr_recibo,
                       s1210_nr_recibo, s1299_nr_recibo, created_at
                FROM pipeline_correcao
                WHERE cpf = %s
                ORDER BY id DESC LIMIT 5
            """, (req.cpf,))
            pipelines = [dict(r) for r in cur.fetchall()]
            for r in pipelines:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
            snapshot_dados["pipeline_runs"] = pipelines
        except Exception:
            conn.rollback()
            snapshot_dados["pipeline_runs"] = []

        # Inserir no banco
        cur2 = conn.cursor()
        cur2.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_audit (
                id serial PRIMARY KEY,
                cpf varchar(11) NOT NULL,
                per_apur varchar(7) NOT NULL,
                tipo varchar(20) NOT NULL,
                dados jsonb NOT NULL,
                created_at timestamp DEFAULT NOW()
            )
        """)
        cur2.execute("""
            INSERT INTO pipeline_audit (cpf, per_apur, tipo, dados)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (req.cpf, req.per_apur, req.tipo, json.dumps(snapshot_dados, default=str)))
        snapshot_id = cur2.fetchone()[0]
        conn.commit()

        return {
            "sucesso": True,
            "snapshot_id": snapshot_id,
            "tipo": req.tipo,
            "cpf": req.cpf,
            "per_apur": req.per_apur,
            "dados": snapshot_dados,
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Erro ao capturar snapshot: {str(e)}")
    finally:
        cur.close()
        conn.close()
