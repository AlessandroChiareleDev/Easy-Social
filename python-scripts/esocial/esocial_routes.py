"""
API REST para orquestração do envio S-1010 ao eSocial
Ambiente: configurável (tpAmb=1 produção / tpAmb=2 homologação)

Endpoints:
- GET  /api/esocial/rubricas-pendentes    Rubricas inconsistentes do cruzamento EB
- POST /api/esocial/s1010/enviar          Gerar XML → Assinar → SOAP → Enviar
- GET  /api/esocial/s1010/consultar/{p}   Consultar resultado pelo protocolo
- GET  /api/esocial/envios                Histórico de envios
"""

import re
import os
import json
from datetime import datetime


def _safe_json(val, default=None):
    """Parse JSONB value safely - psycopg2 may return str or already-parsed object."""
    if val is None:
        return default
    if isinstance(val, (list, dict)):
        return val
    return json.loads(val)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2

from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG

router = APIRouter(prefix="/api/esocial", tags=["esocial"])

INIT_ENVIOS_SQL = """
CREATE TABLE IF NOT EXISTS esocial_envios (
    id SERIAL PRIMARY KEY,
    tipo_evento VARCHAR(10) NOT NULL DEFAULT 'S-1010',
    modo VARCHAR(20) NOT NULL DEFAULT 'alteracao',
    ambiente VARCHAR(2) NOT NULL DEFAULT '2',
    ini_valid VARCHAR(10),
    status VARCHAR(30) NOT NULL DEFAULT 'enviado',
    protocolo_envio VARCHAR(100),
    codigo_resposta VARCHAR(10),
    descricao_resposta TEXT,
    total_eventos INTEGER DEFAULT 0,
    rubrica_ids JSONB,
    rubrica_detalhes JSONB,
    xml_enviado TEXT,
    xml_retorno TEXT,
    recibo_consulta JSONB,
    ocorrencias JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

# SQL para adicionar colunas novas se tabela já existe
MIGRATE_ENVIOS_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='esocial_envios' AND column_name='ambiente') THEN
        ALTER TABLE esocial_envios ADD COLUMN ambiente VARCHAR(2) NOT NULL DEFAULT '2';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='esocial_envios' AND column_name='ini_valid') THEN
        ALTER TABLE esocial_envios ADD COLUMN ini_valid VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='esocial_envios' AND column_name='rubrica_detalhes') THEN
        ALTER TABLE esocial_envios ADD COLUMN rubrica_detalhes JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='esocial_envios' AND column_name='xml_enviado') THEN
        ALTER TABLE esocial_envios ADD COLUMN xml_enviado TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='esocial_envios' AND column_name='recibo_consulta') THEN
        ALTER TABLE esocial_envios ADD COLUMN recibo_consulta JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='esocial_envios' AND column_name='nr_recibo') THEN
        ALTER TABLE esocial_envios ADD COLUMN nr_recibo VARCHAR(100);
    END IF;
    -- Coluna envio_status em cruzamento_eb: pendente | enviado | feito
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cruzamento_eb' AND column_name='envio_status') THEN
        ALTER TABLE cruzamento_eb ADD COLUMN envio_status VARCHAR(20) DEFAULT 'pendente';
    END IF;
    -- Coluna ini_valid_esocial em cruzamento_eb: iniValid confirmado por envio bem-sucedido
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cruzamento_eb' AND column_name='ini_valid_esocial') THEN
        ALTER TABLE cruzamento_eb ADD COLUMN ini_valid_esocial VARCHAR(10);
    END IF;
END $$;
"""

# SQL para criar tabela config_esocial (data de início da empresa no eSocial)
INIT_CONFIG_ESOCIAL_SQL = """
CREATE TABLE IF NOT EXISTS config_esocial (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(20) NOT NULL UNIQUE,
    ini_valid_padrao VARCHAR(10),
    auto_detected BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW()
);
"""


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ── Request Models ────────────────────────────────────────────────


class EnviarRequest(BaseModel):
    rubrica_ids: list[str]   # cod_rubrica do cruzamento_eb
    ini_valid: str = ""      # formato AAAA-MM (vazio = auto da Tabela 3)
    modo: str = "inclusao"   # "inclusao" ou "alteracao"
    ambiente: str = "2"      # "1" = produção, "2" = homologação


# ── Helpers ───────────────────────────────────────────────────────


def _load_cert_ativo(cursor=None) -> dict:
    """Carrega certificado ativo do banco LOCAL. Retorna dict ou None."""
    local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with local_conn.cursor() as local_cur:
            local_cur.execute(
                "SELECT id, cnpj, titular, arquivo_path, senha_encrypted, ativo "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = local_cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "cnpj": row[1],
                "titular": row[2],
                "arquivo_path": row[3],
                "senha_encrypted": row[4],
            }
    finally:
        local_conn.close()


def _salvar_xmls_repositorio(
    rubrica_ids: list[str], modo: str, ambiente: str, ini_valid: str,
    xmls_gerados: list[str], soap_envelope: str, resultado: dict,
):
    """Salva XMLs gerados e resultado no repositório local recibos_s1010/."""
    try:
        base_dir = os.path.join(os.path.dirname(__file__), "..", "recibos_s1010")
        os.makedirs(base_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        amb_label = "producao" if ambiente == "1" else "homologacao"
        rubricas_label = "_".join(rubrica_ids[:5])
        if len(rubrica_ids) > 5:
            rubricas_label += f"_e_mais_{len(rubrica_ids) - 5}"
        prefix = f"rub_{rubricas_label}_{amb_label}_{modo}_{timestamp}"

        # Salvar cada XML gerado
        for i, xml in enumerate(xmls_gerados):
            cod = rubrica_ids[i] if i < len(rubrica_ids) else str(i)
            filepath = os.path.join(base_dir, f"{prefix}_xml_{cod}.xml")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(xml)

        # Salvar SOAP envelope
        filepath = os.path.join(base_dir, f"{prefix}_soap.xml")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(soap_envelope)

        # Salvar resultado
        filepath = os.path.join(base_dir, f"{prefix}_resultado.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)

    except Exception:
        pass  # Não falhar o envio por erro ao salvar repositório


def _lookup_ini_valid_tabela3(cursor, nat_rubr: str) -> str:
    """Busca iniValid na tabela3_esocial_oficial pelo código de natureza.
    Retorna formato AAAA-MM. Prioriza entrada vigente (sem dt_fim)."""
    cursor.execute(
        """
        SELECT col_c FROM tabela3_esocial_oficial
        WHERE col_a = %s
        ORDER BY
            CASE WHEN col_d = '' OR col_d IS NULL THEN 0 ELSE 1 END,
            col_c DESC
        LIMIT 1
        """,
        (nat_rubr,),
    )
    row = cursor.fetchone()
    if not row or not row[0]:
        return ""
    # Converter dd/MM/yyyy -> AAAA-MM
    dt = row[0].strip()
    if "/" in dt:
        parts = dt.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}"
    return ""


def _lookup_ini_valid_batch(cursor, nat_rubrs: list[str]) -> dict:
    """Busca iniValid para múltiplos códigos de natureza de uma vez."""
    if not nat_rubrs:
        return {}
    placeholders = ",".join(["%s"] * len(nat_rubrs))
    cursor.execute(
        f"""
        SELECT DISTINCT ON (col_a) col_a, col_c
        FROM tabela3_esocial_oficial
        WHERE col_a IN ({placeholders})
        ORDER BY col_a,
            CASE WHEN col_d = '' OR col_d IS NULL THEN 0 ELSE 1 END,
            col_c DESC
        """,
        nat_rubrs,
    )
    result = {}
    for row in cursor.fetchall():
        dt = (row[1] or "").strip()
        if "/" in dt:
            parts = dt.split("/")
            if len(parts) == 3:
                result[row[0]] = f"{parts[2]}-{parts[1]}"
    return result


def _lookup_dtfim_batch(cursor, nat_rubrs: list[str]) -> dict:
    """Busca dt_fim para múltiplos códigos de natureza.
    Retorna dict: código → dt_fim (string DD/MM/AAAA) apenas para naturezas
    que NÃO possuem nenhuma entrada ativa (sem dt_fim) na Tabela 3.
    Se um código tem uma entrada ativa (dt_fim vazio/null), não é expirado."""
    if not nat_rubrs:
        return {}
    placeholders = ",".join(["%s"] * len(nat_rubrs))
    # Primeiro: encontrar códigos que TÊM pelo menos uma entrada ativa (sem dt_fim)
    cursor.execute(
        f"""
        SELECT DISTINCT col_a
        FROM tabela3_esocial_oficial
        WHERE col_a IN ({placeholders})
          AND (col_d IS NULL OR col_d = '')
        """,
        nat_rubrs,
    )
    codigos_ativos = {row[0] for row in cursor.fetchall()}

    # Segundo: para os que NÃO têm entrada ativa, buscar o dt_fim mais recente
    codigos_expirados = [c for c in nat_rubrs if c not in codigos_ativos]
    if not codigos_expirados:
        return {}
    placeholders2 = ",".join(["%s"] * len(codigos_expirados))
    cursor.execute(
        f"""
        SELECT DISTINCT ON (col_a) col_a, col_d
        FROM tabela3_esocial_oficial
        WHERE col_a IN ({placeholders2})
          AND col_d IS NOT NULL AND col_d != ''
        ORDER BY col_a, col_d DESC
        """,
        codigos_expirados,
    )
    result = {}
    for row in cursor.fetchall():
        result[row[0]] = (row[1] or "").strip()
    return result


def _resolve_ini_valid(cursor, cod_rubrica: str, nat_rubr: str, cnpj: str) -> str:
    """Resolve iniValid com 3 camadas de prioridade:
    1. Per-rubrica: ini_valid_esocial do cruzamento_eb (confirmado por envio anterior)
    2. Per-empresa: ini_valid_padrao do config_esocial (data S-1000 da empresa)
    3. Tabela 3: dt_inicio da natureza na tabela nacional (fallback)
    Retorna formato AAAA-MM."""
    # Camada 1: iniValid confirmado por envio anterior para esta rubrica
    cursor.execute(
        "SELECT ini_valid_esocial FROM cruzamento_eb WHERE cod_rubrica = %s LIMIT 1",
        (cod_rubrica,),
    )
    row = cursor.fetchone()
    if row and row[0]:
        return row[0]

    # Camada 2: data padrão da empresa (S-1000)
    ini_empresa = _get_ini_valid_empresa(cursor, cnpj)

    # Camada 3: Tabela 3
    ini_tabela3 = _lookup_ini_valid_tabela3(cursor, nat_rubr)

    # Se temos data da empresa, usar a MAIOR entre empresa e tabela3
    if ini_empresa:
        if ini_tabela3:
            return max(ini_empresa, ini_tabela3)
        return ini_empresa

    return ini_tabela3


def _get_ini_valid_empresa(cursor, cnpj: str) -> str:
    """Busca ini_valid_padrao do config_esocial para o CNPJ."""
    try:
        cursor.execute(
            "SELECT ini_valid_padrao FROM config_esocial WHERE cnpj = %s LIMIT 1",
            (cnpj,),
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else ""
    except Exception:
        return ""


def _save_ini_valid_empresa(cursor, cnpj: str, ini_valid: str, auto: bool = True):
    """Salva/atualiza ini_valid_padrao no config_esocial."""
    try:
        cursor.execute(INIT_CONFIG_ESOCIAL_SQL)
        cursor.execute(
            """INSERT INTO config_esocial (cnpj, ini_valid_padrao, auto_detected, updated_at)
               VALUES (%s, %s, %s, NOW())
               ON CONFLICT (cnpj) DO UPDATE
               SET ini_valid_padrao = EXCLUDED.ini_valid_padrao,
                   auto_detected = EXCLUDED.auto_detected,
                   updated_at = NOW()""",
            (cnpj, ini_valid, auto),
        )
    except Exception:
        pass


def _save_ini_valid_rubricas(cursor, cod_rubricas: list[str], ini_valid: str):
    """Salva ini_valid_esocial confirmado para rubricas após envio bem-sucedido."""
    if not cod_rubricas or not ini_valid:
        return
    ph = ",".join(["%s"] * len(cod_rubricas))
    try:
        cursor.execute(
            f"""UPDATE cruzamento_eb
                SET ini_valid_esocial = %s
                WHERE cod_rubrica IN ({ph}) AND (ini_valid_esocial IS NULL OR ini_valid_esocial = '')""",
            [ini_valid] + [str(r) for r in cod_rubricas],
        )
    except Exception:
        pass


def _load_rubricas_by_ids(cursor, cod_rubricas: list[str]) -> list[dict]:
    """Carrega rubricas do cruzamento_eb por cod_rubrica."""
    placeholders = ",".join(["%s"] * len(cod_rubricas))
    cursor.execute(
        f"""
        SELECT cod_rubrica, descricao, cod_natureza,
               incid_inss, incid_irrf, incid_fgts,
               incid_base_legal_inss, incid_base_legal_irrf,
               incid_base_legal_fgts, analise
        FROM cruzamento_eb
        WHERE cod_rubrica IN ({placeholders})
        """,
        cod_rubricas,
    )
    rows = cursor.fetchall()
    result = []
    for r in rows:
        # Extrair o código correto da base legal ("11 - descrição" -> "11")
        inss_correto = r[6].split(" - ")[0] if r[6] else str(r[3] or "00")
        irrf_correto = r[7].split(" - ")[0] if r[7] else str(r[4] or "00")
        fgts_correto = r[8].split(" - ")[0] if r[8] else str(r[5] or "00")

        # Extrair código de natureza ("1016 - descrição" -> "1016")
        cod_nat = r[2].split(" - ")[0] if r[2] else "1000"

        result.append({
            "cod_rubrica": str(r[0]),
            "descricao": r[1] or "",
            "cod_natureza": r[2] or "",
            "nat_rubr": cod_nat,
            "incid_inss": str(r[3] or "00"),
            "incid_irrf": str(r[4] or "00"),
            "incid_fgts": str(r[5] or "00"),
            "inss_correto": inss_correto,
            "irrf_correto": irrf_correto,
            "fgts_correto": fgts_correto,
            "base_legal_inss": r[6] or "",
            "base_legal_irrf": r[7] or "",
            "base_legal_fgts": r[8] or "",
            "analise": r[9] or "",
            "tipo": "Vencimento",  # default
            "pispasep": "00",
        })
    return result


# ── Rotas ─────────────────────────────────────────────────────────


@router.get("/rubricas-pendentes")
async def rubricas_pendentes(filtro: str = "pendentes"):
    """Retorna rubricas inconsistentes do cruzamento EB. filtro: pendentes | enviadas | todas"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            extra_filter = ""
            if filtro == "enviadas":
                extra_filter = "AND COALESCE(ce.envio_status, 'pendente') = 'enviado'"
            elif filtro != "todas":
                extra_filter = "AND (ce.corrigido IS NULL OR ce.corrigido = FALSE) AND COALESCE(ce.envio_status, 'pendente') = 'pendente'"
            cur.execute(
                f"""
                SELECT ce.id, ce.cod_rubrica, ce.descricao,
                       ce.cod_natureza,
                       ce.incid_inss, ce.incid_irrf, ce.incid_fgts,
                       SPLIT_PART(ce.incid_base_legal_inss, ' - ', 1) AS inss_correto,
                       SPLIT_PART(ce.incid_base_legal_irrf, ' - ', 1) AS irrf_correto,
                       SPLIT_PART(ce.incid_base_legal_fgts, ' - ', 1) AS fgts_correto,
                       ce.analise, ce.corrigido,
                       COALESCE(ce.envio_status, 'pendente') AS envio_status,
                       ce.ini_valid_esocial
                FROM cruzamento_eb ce
                WHERE (
                    ce.incid_inss != SPLIT_PART(ce.incid_base_legal_inss, ' - ', 1)
                    OR ce.incid_irrf != SPLIT_PART(ce.incid_base_legal_irrf, ' - ', 1)
                    OR ce.incid_fgts != SPLIT_PART(ce.incid_base_legal_fgts, ' - ', 1)
                )
                {extra_filter}
                ORDER BY ce.cod_rubrica::int ASC
                """
            )
            rows = cur.fetchall()
            rubricas = []
            nat_codes = []
            for r in rows:
                cod_nat = r[3].split(" - ")[0] if r[3] else ""
                if cod_nat:
                    nat_codes.append(cod_nat)
                rubricas.append({
                    "id": r[0],
                    "cod_rubrica": str(r[1]),
                    "descricao": r[2] or "",
                    "cod_natureza": r[3] or "",
                    "nat_rubr": cod_nat,
                    "incid_inss": str(r[4] or "00"),
                    "incid_irrf": str(r[5] or "00"),
                    "incid_fgts": str(r[6] or "00"),
                    "inss_correto": str(r[7] or "00"),
                    "irrf_correto": str(r[8] or "00"),
                    "fgts_correto": str(r[9] or "00"),
                    "analise": r[10] or "",
                    "corrigido": r[11] or False,
                    "envio_status": r[12] or "pendente",
                    "nat_rubr_raw": cod_nat,
                    "ini_valid_esocial": r[13] or "",
                })
            # Buscar iniValid e dt_fim da Tabela 3 e config empresa
            cur.execute(INIT_CONFIG_ESOCIAL_SQL)
            unique_nat_codes = list(set(nat_codes))
            ini_map = _lookup_ini_valid_batch(cur, unique_nat_codes)
            # Buscar dt_fim (validade final) de cada natureza na Tabela 3
            dtfim_map = _lookup_dtfim_batch(cur, unique_nat_codes)
            # Buscar ini_valid_padrao da empresa (via cert ativo)
            cert_info = _load_cert_ativo(cur)
            ini_empresa = ""
            if cert_info:
                ini_empresa = _get_ini_valid_empresa(cur, cert_info["cnpj"])
            for rub in rubricas:
                ini_tab3 = ini_map.get(rub["nat_rubr"], "")
                rub["ini_valid_auto"] = ini_tab3
                # Marcar natureza expirada (dt_fim preenchida na Tabela 3)
                dtfim_info = dtfim_map.get(rub["nat_rubr"])
                rub["nat_rubr_expirada"] = dtfim_info is not None
                rub["nat_rubr_dt_fim"] = dtfim_info or ""
                # Resolver: per-rubrica > per-empresa > max(empresa, tabela3)
                if rub["ini_valid_esocial"]:
                    rub["ini_valid_resolved"] = rub["ini_valid_esocial"]
                    rub["ini_valid_source"] = "rubrica"
                elif ini_empresa:
                    rub["ini_valid_resolved"] = max(ini_empresa, ini_tab3) if ini_tab3 else ini_empresa
                    rub["ini_valid_source"] = "empresa"
                elif ini_tab3:
                    rub["ini_valid_resolved"] = ini_tab3
                    rub["ini_valid_source"] = "tabela3"
                else:
                    rub["ini_valid_resolved"] = ""
                    rub["ini_valid_source"] = ""
            return {"rubricas": rubricas, "total": len(rubricas), "ini_valid_empresa": ini_empresa}
    finally:
        conn.close()


@router.post("/s1010/enviar")
async def enviar_s1010(req: EnviarRequest):
    """
    Orquestra o pipeline completo de envio S-1010:
    1. Validar entrada
    2. Carregar certificado ativo
    3. Carregar dados das rubricas
    4. Gerar XML → Assinar → Montar SOAP → Enviar
    5. Salvar resultado no banco
    """
    # Validar entrada
    if not req.rubrica_ids:
        raise HTTPException(status_code=400, detail="Nenhuma rubrica selecionada para envio")
    if len(req.rubrica_ids) > 50:
        raise HTTPException(status_code=400, detail="Máximo de 50 rubricas por lote")
    if req.ini_valid and not re.match(r"^\d{4}-\d{2}$", req.ini_valid):
        raise HTTPException(status_code=400, detail="iniValid deve ter formato AAAA-MM")
    if req.modo not in ("inclusao", "alteracao"):
        raise HTTPException(status_code=400, detail="modo deve ser 'inclusao' ou 'alteracao'")
    if req.ambiente not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ambiente deve ser '1' (produção) ou '2' (homologação)")

    is_producao = req.ambiente == "1"
    tp_amb = req.ambiente

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # 1. Carregar certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum certificado A1 ativo. Faça upload em Certificados.",
                )

            # 2. Carregar rubricas
            rubricas = _load_rubricas_by_ids(cur, req.rubrica_ids)
            if not rubricas:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhuma rubrica encontrada com os IDs informados",
                )

            # 3. Descriptografar senha e ler PFX
            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            # 4. Montar dados para o gerador
            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            generator = S1010XMLGenerator()
            eventos_assinados = []
            xmls_gerados = []  # Para salvar no repositório
            rubrica_detalhes = []  # Detalhes para o histórico
            ini_valid_usado = ""  # Track actual iniValid used (for auto-save)

            for rub in rubricas:
                tp_rubr = 1 if rub["tipo"] == "Vencimento" else 2
                pispasep = rub["pispasep"]
                if pispasep and pispasep.isdigit():
                    pispasep = f"{int(pispasep):02d}"
                else:
                    pispasep = "00"

                # iniValid: manual > per-rubrica > per-empresa > Tabela 3
                if req.ini_valid:
                    ini_val = req.ini_valid
                else:
                    cur.execute(INIT_CONFIG_ESOCIAL_SQL)
                    ini_val = _resolve_ini_valid(cur, rub["cod_rubrica"], rub["nat_rubr"], cnpj)
                    if not ini_val:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Rubrica {rub['cod_rubrica']}: não foi possível determinar iniValid automaticamente para natRubr={rub['nat_rubr']}. Configure a data da empresa ou informe manualmente.",
                        )

                rubrica_data = {
                    "codRubr": rub["cod_rubrica"],
                    "ideTabRubr": "1",
                    "iniValid": ini_val,
                    "dscRubr": rub["descricao"][:100],
                    "natRubr": rub["nat_rubr"],
                    "tpRubr": tp_rubr,
                    "codIncCP": rub["inss_correto"],
                    "codIncIRRF": rub["irrf_correto"],
                    "codIncFGTS": rub["fgts_correto"],
                    "codIncPisPasep": pispasep,
                }
                ini_valid_usado = ini_val  # Track for DB save

                # Guardar detalhes para histórico/repositório
                rubrica_detalhes.append({
                    "cod_rubrica": rub["cod_rubrica"],
                    "descricao": rub["descricao"],
                    "cod_natureza": rub["cod_natureza"],
                    "nat_rubr": rub["nat_rubr"],
                    "incid_inss": rub["incid_inss"],
                    "incid_irrf": rub["incid_irrf"],
                    "incid_fgts": rub["incid_fgts"],
                    "inss_correto": rub["inss_correto"],
                    "irrf_correto": rub["irrf_correto"],
                    "fgts_correto": rub["fgts_correto"],
                    "base_legal_inss": rub["base_legal_inss"],
                    "base_legal_irrf": rub["base_legal_irrf"],
                    "base_legal_fgts": rub["base_legal_fgts"],
                    "analise": rub["analise"],
                })

                # Gerar XML (inclusão ou alteração) com ambiente
                if req.modo == "inclusao":
                    xml_bytes = generator.gerar_inclusao(empregador, rubrica_data, tp_amb=tp_amb)
                else:
                    xml_bytes = generator.gerar_alteracao(empregador, rubrica_data, tp_amb=tp_amb)

                # Assinar XML
                xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
                eventos_assinados.append(xml_assinado)
                xmls_gerados.append(xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes)

            # 5. Montar SOAP
            builder = SOAPEnvelopeBuilder()
            soap_envelope = builder.montar_envio(
                eventos_assinados, empregador, transmissor, grupo=1
            )

            # 6. Enviar via mTLS (URL conforme ambiente)
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # 6b. Salvar XMLs no repositório local
            _salvar_xmls_repositorio(
                req.rubrica_ids, req.modo, req.ambiente, req.ini_valid,
                xmls_gerados, soap_envelope, resultado,
            )

            # 7. Salvar no banco
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, rubrica_detalhes, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1010",
                        req.modo,
                        req.ambiente,
                        ini_valid_usado or req.ini_valid,
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        len(eventos_assinados),
                        json.dumps(req.rubrica_ids),
                        json.dumps(rubrica_detalhes),
                        soap_envelope[:50000],  # Limitar tamanho
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]

                # Marcar rubricas como 'enviado' no cruzamento_eb
                if resultado.get("sucesso"):
                    ph = ",".join(["%s"] * len(req.rubrica_ids))
                    cur.execute(
                        f"""UPDATE cruzamento_eb
                            SET envio_status = 'enviado'
                            WHERE cod_rubrica IN ({ph})""",
                        [str(rid) for rid in req.rubrica_ids],
                    )

                conn.commit()
            except Exception:
                # Se falhar ao salvar, ainda retorna o resultado do envio
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "eventos_enviados": len(eventos_assinados),
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


@router.get("/s1010/consultar/{protocolo}")
async def consultar_s1010(protocolo: str, ambiente: str = "2"):
    """Consulta resultado do processamento de um lote pelo protocolo."""
    is_producao = ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Carregar certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum certificado A1 ativo",
                )

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            # Consultar eSocial (URL conforme ambiente)
            url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
            resultado = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

            # Carregar detalhes do envio original para enriquecer resposta
            envio_detalhes = None
            try:
                cur.execute(
                    """SELECT id, modo, ambiente, ini_valid, rubrica_detalhes,
                              created_at, rubrica_ids
                       FROM esocial_envios
                       WHERE protocolo_envio = %s LIMIT 1""",
                    (protocolo,),
                )
                envio_row = cur.fetchone()
                if envio_row:
                    envio_detalhes = {
                        "envio_id": envio_row[0],
                        "modo": envio_row[1],
                        "ambiente": envio_row[2] if envio_row[2] else ambiente,
                        "ini_valid": envio_row[3],
                        "rubrica_detalhes": _safe_json(envio_row[4], []),
                        "data_envio": str(envio_row[5]) if envio_row[5] else None,
                        "rubrica_ids": _safe_json(envio_row[6], []),
                    }
            except Exception:
                pass

            # Atualizar envio no banco com resultado da consulta
            try:
                # Extrair XML bruto e nr_recibo antes de remover do resultado
                xml_resposta = resultado.pop("xml_resposta", None)

                # Verificar se o lote foi processado E se os eventos individuais tiveram sucesso
                eventos = resultado.get("eventos", [])
                todos_sucesso = resultado.get("sucesso", False) and all(
                    str(ev.get("codigo_resposta", "")) in ("201", "202") for ev in eventos
                )
                status_final = "processado" if todos_sucesso else "erro"

                # Extrair nr_recibo do primeiro evento com sucesso
                nr_recibo = None
                for ev in eventos:
                    if ev.get("nr_recibo"):
                        nr_recibo = ev["nr_recibo"]
                        break

                cur.execute(
                    """UPDATE esocial_envios
                       SET status = %s, recibo_consulta = %s, xml_retorno = %s,
                           nr_recibo = %s, updated_at = NOW()
                       WHERE protocolo_envio = %s""",
                    (status_final, json.dumps(resultado), xml_resposta,
                     nr_recibo, protocolo),
                )
                # Atualizar status das rubricas no cruzamento_eb
                if envio_detalhes:
                    rub_ids = envio_detalhes.get("rubrica_ids", [])
                    ini_valid_usado = envio_detalhes.get("ini_valid", "")
                    if rub_ids:
                        ph = ",".join(["%s"] * len(rub_ids))
                        if todos_sucesso:
                            cur.execute(
                                f"""UPDATE cruzamento_eb
                                    SET corrigido = TRUE, corrigido_em = NOW(),
                                        envio_status = 'feito'
                                    WHERE cod_rubrica IN ({ph})""",
                                [str(rid) for rid in rub_ids],
                            )
                            # Auto-salvar iniValid confirmado para rubricas e empresa
                            if ini_valid_usado:
                                _save_ini_valid_rubricas(cur, [str(r) for r in rub_ids], ini_valid_usado)
                                _save_ini_valid_empresa(cur, cert_info["cnpj"], ini_valid_usado, auto=True)
                        else:
                            # Rejeitado: volta para pendente
                            cur.execute(
                                f"""UPDATE cruzamento_eb
                                    SET envio_status = 'pendente'
                                    WHERE cod_rubrica IN ({ph})""",
                                [str(rid) for rid in rub_ids],
                            )
                conn.commit()
            except Exception:
                pass

            # Enriquecer resultado com dados do envio
            resultado["envio_detalhes"] = envio_detalhes

            return resultado
    finally:
        conn.close()


@router.post("/reconsultar-todos")
async def reconsultar_todos(ambiente: str = "1"):
    """Re-consulta todos os envios processados/enviados para extrair nrRecibo correto."""
    is_producao = ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_ENVIOS_SQL)
            cur.execute(MIGRATE_ENVIOS_SQL)
            conn.commit()

            # Carregar certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            # Buscar todos envios que precisam de nr_recibo
            cur.execute(
                """SELECT id, protocolo_envio, status, ambiente
                   FROM esocial_envios
                   WHERE protocolo_envio IS NOT NULL
                     AND protocolo_envio != ''
                     AND (nr_recibo IS NULL OR nr_recibo = '')
                   ORDER BY id"""
            )
            envios = cur.fetchall()

            resultados = []
            for envio_id, protocolo, status_atual, amb in envios:
                try:
                    is_prod = (amb or ambiente) == "1"
                    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_prod)
                    resultado = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

                    xml_resposta = resultado.pop("xml_resposta", None)
                    eventos = resultado.get("eventos", [])
                    todos_sucesso = resultado.get("sucesso", False) and all(
                        str(ev.get("codigo_resposta", "")) in ("201", "202") for ev in eventos
                    )
                    status_final = "processado" if todos_sucesso else "erro"

                    nr_recibo = None
                    for ev in eventos:
                        if ev.get("nr_recibo"):
                            nr_recibo = ev["nr_recibo"]
                            break

                    cur.execute(
                        """UPDATE esocial_envios
                           SET status = %s, recibo_consulta = %s, xml_retorno = %s,
                               nr_recibo = %s, updated_at = NOW()
                           WHERE id = %s""",
                        (status_final, json.dumps(resultado), xml_resposta,
                         nr_recibo, envio_id),
                    )
                    conn.commit()

                    resultados.append({
                        "id": envio_id,
                        "protocolo": protocolo,
                        "status": status_final,
                        "nr_recibo": nr_recibo,
                        "sucesso": True,
                    })
                except Exception as e:
                    resultados.append({
                        "id": envio_id,
                        "protocolo": protocolo,
                        "nr_recibo": None,
                        "sucesso": False,
                        "erro": str(e),
                    })

            return {
                "total": len(envios),
                "resultados": resultados,
                "com_recibo": sum(1 for r in resultados if r.get("nr_recibo")),
                "sem_recibo": sum(1 for r in resultados if not r.get("nr_recibo")),
            }
    finally:
        conn.close()


@router.get("/envios")
async def listar_envios():
    """Retorna histórico de envios ao eSocial."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_ENVIOS_SQL)
            cur.execute(MIGRATE_ENVIOS_SQL)
            cur.execute(
                """SELECT id, tipo_evento, modo, status, protocolo_envio,
                          codigo_resposta, descricao_resposta, total_eventos,
                          created_at, ambiente, ini_valid, rubrica_detalhes,
                          rubrica_ids, recibo_consulta, updated_at, nr_recibo
                   FROM esocial_envios
                   ORDER BY created_at DESC
                   LIMIT 100"""
            )
            rows = cur.fetchall()
            envios = []
            for r in rows:
                envios.append({
                    "id": r[0],
                    "tipo_evento": r[1],
                    "modo": r[2],
                    "status": r[3],
                    "protocolo_envio": r[4],
                    "codigo_resposta": r[5],
                    "descricao_resposta": r[6],
                    "total_eventos": r[7],
                    "created_at": str(r[8]) if r[8] else None,
                    "ambiente": r[9] if r[9] else "2",
                    "ini_valid": r[10],
                    "rubrica_detalhes": _safe_json(r[11], []),
                    "rubrica_ids": _safe_json(r[12], []),
                    "recibo_consulta": _safe_json(r[13]),
                    "updated_at": str(r[14]) if r[14] else None,
                    "nr_recibo": r[15],
                })
            return {"envios": envios, "total": len(envios)}
    finally:
        conn.close()


# ── Editar Natureza da Rubrica ─────────────────────────────────────


class EditNaturezaRequest(BaseModel):
    cod_rubrica: str
    nova_natureza: str  # código numérico da natureza (ex: "1803")


@router.patch("/rubrica-natureza")
async def editar_natureza(req: EditNaturezaRequest):
    """Atualiza o cod_natureza de uma rubrica no cruzamento_eb."""
    if not req.cod_rubrica or not req.nova_natureza:
        raise HTTPException(status_code=400, detail="cod_rubrica e nova_natureza são obrigatórios")
    if not req.nova_natureza.isdigit():
        raise HTTPException(status_code=400, detail="nova_natureza deve ser um código numérico")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Buscar descrição da natureza na Tabela 3
            cur.execute(
                "SELECT col_b FROM tabela3_esocial_oficial WHERE col_a = %s LIMIT 1",
                (req.nova_natureza,),
            )
            row = cur.fetchone()
            if row:
                novo_valor = f"{req.nova_natureza} - {row[0]}"
            else:
                novo_valor = req.nova_natureza

            # Atualizar no cruzamento_eb
            cur.execute(
                "UPDATE cruzamento_eb SET cod_natureza = %s WHERE cod_rubrica = %s",
                (novo_valor, req.cod_rubrica),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Rubrica {req.cod_rubrica} não encontrada")
            conn.commit()
        return {"cod_rubrica": req.cod_rubrica, "cod_natureza": novo_valor, "nat_rubr": req.nova_natureza}
    finally:
        conn.close()


# ── Config Empresa eSocial ────────────────────────────────────────


class ConfigEmpresaRequest(BaseModel):
    ini_valid_padrao: str  # formato AAAA-MM


@router.get("/config-empresa")
async def get_config_empresa():
    """Retorna configuração eSocial da empresa (ini_valid_padrao do S-1000)."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_CONFIG_ESOCIAL_SQL)
            # Pegar CNPJ do certificado ativo
            cert_info = _load_cert_ativo(cur)
            cnpj = cert_info["cnpj"] if cert_info else None
            if not cnpj:
                return {"cnpj": None, "ini_valid_padrao": "", "auto_detected": False}
            cur.execute(
                "SELECT ini_valid_padrao, auto_detected FROM config_esocial WHERE cnpj = %s",
                (cnpj,),
            )
            row = cur.fetchone()
            return {
                "cnpj": cnpj,
                "ini_valid_padrao": row[0] if row else "",
                "auto_detected": row[1] if row else False,
            }
    finally:
        conn.close()


@router.post("/config-empresa")
async def set_config_empresa(req: ConfigEmpresaRequest):
    """Define a data de início da empresa no eSocial (ini_valid do S-1000)."""
    if not re.match(r"^\d{4}-\d{2}$", req.ini_valid_padrao):
        raise HTTPException(status_code=400, detail="ini_valid_padrao deve ter formato AAAA-MM")
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_CONFIG_ESOCIAL_SQL)
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")
            cnpj = cert_info["cnpj"]
            _save_ini_valid_empresa(cur, cnpj, req.ini_valid_padrao, auto=False)
            conn.commit()
        return {"cnpj": cnpj, "ini_valid_padrao": req.ini_valid_padrao, "auto_detected": False}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# EVENTOS PERIÓDICOS — S-1298 (Reabertura) e S-1299 (Fechamento)
# ══════════════════════════════════════════════════════════════════════════════


class EnviarS1298Request(BaseModel):
    per_apur: str            # AAAA-MM — período a reabrir
    ind_apuracao: str = "1"  # "1" = mensal, "2" = 13º
    ambiente: str = "2"      # "1" = produção, "2" = homologação


class EnviarS1299Request(BaseModel):
    per_apur: str            # AAAA-MM — período a fechar
    ind_apuracao: str = "1"  # "1" = mensal, "2" = 13º
    ambiente: str = "2"      # "1" = produção, "2" = homologação
    nm_resp: str             # Nome do responsável
    cpf_resp: str            # CPF do responsável
    telefone: str            # Telefone
    email: str               # Email


@router.post("/s1298/enviar")
async def enviar_s1298(req: EnviarS1298Request):
    """
    Envia S-1298 (Reabertura de Eventos Periódicos) ao eSocial.
    Pipeline: Gerar XML → Assinar → SOAP (grupo=3) → Enviar → Salvar
    """
    if not re.match(r"^\d{4}-\d{2}$", req.per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")
    if req.ambiente not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ambiente deve ser '1' ou '2'")
    if req.ind_apuracao not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ind_apuracao deve ser '1' (mensal) ou '2' (13º)")

    is_producao = req.ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # 1. Certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            # 2. Gerar XML S-1298
            xml_bytes = S1298XMLGenerator.gerar(
                empregador, req.per_apur, req.ind_apuracao, tp_amb=req.ambiente
            )

            # 3. Assinar
            xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)

            # 4. Montar SOAP (grupo=3 para periódicos)
            soap_envelope = SOAPEnvelopeBuilder.montar_envio(
                [xml_assinado], empregador, transmissor, grupo="3"
            )

            # 5. Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # 6. Salvar no banco
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1298",
                        "reabertura",
                        req.ambiente,
                        req.per_apur,
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        1,
                        json.dumps([req.per_apur]),
                        soap_envelope[:50000],
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]
                conn.commit()
            except Exception:
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "per_apur": req.per_apur,
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


@router.post("/s1299/enviar")
async def enviar_s1299(req: EnviarS1299Request):
    """
    Envia S-1299 (Fechamento de Eventos Periódicos) ao eSocial.
    Pipeline: Gerar XML → Assinar → SOAP (grupo=3) → Enviar → Salvar
    """
    if not re.match(r"^\d{4}-\d{2}$", req.per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")
    if req.ambiente not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ambiente deve ser '1' ou '2'")
    if not req.cpf_resp or len(req.cpf_resp) != 11:
        raise HTTPException(status_code=400, detail="cpf_resp deve ter 11 dígitos")

    is_producao = req.ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # 1. Certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            responsavel = {
                "nmResp": req.nm_resp,
                "cpfResp": req.cpf_resp,
                "telefone": req.telefone,
                "email": req.email,
            }

            # 2. Gerar XML S-1299
            xml_bytes = S1299XMLGenerator.gerar(
                empregador, req.per_apur, responsavel, req.ind_apuracao, tp_amb=req.ambiente
            )

            # 3. Assinar
            xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)

            # 4. Montar SOAP (grupo=3)
            soap_envelope = SOAPEnvelopeBuilder.montar_envio(
                [xml_assinado], empregador, transmissor, grupo="3"
            )

            # 5. Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # 6. Salvar
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1299",
                        "fechamento",
                        req.ambiente,
                        req.per_apur,
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        1,
                        json.dumps([req.per_apur]),
                        soap_envelope[:50000],
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]
                conn.commit()
            except Exception:
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "per_apur": req.per_apur,
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# S-1200  —  Remuneração do Trabalhador
# ─────────────────────────────────────────────────────────────────────────────

class ItensRemunRequest(BaseModel):
    codRubr: str
    ideTabRubr: str
    vrRubr: str
    indApurIR: str = "0"
    qtdRubr: str | None = None
    fatorRubr: str | None = None
    descFolha: dict | None = None  # {tpDesc, instFinanc?, nrDoc?}


class RemunPerApurRequest(BaseModel):
    matricula: str
    itensRemun: list[ItensRemunRequest]
    indSimples: str | None = None
    infoAgNocivo: dict | None = None  # {grauExp}


class IdeEstabLotRequest(BaseModel):
    tpInsc: str
    nrInsc: str
    codLotacao: str
    remunPerApur: list[RemunPerApurRequest]


class InfoPerApurRequest(BaseModel):
    ideEstabLot: list[IdeEstabLotRequest]


class DmDevRequest(BaseModel):
    ideDmDev: str
    codCateg: str | None = None
    infoPerApur: InfoPerApurRequest | None = None
    infoPerAnt: dict | None = None  # Estrutura livre p/ período anterior


class EnviarS1200Request(BaseModel):
    cpf_trab: str              # CPF do trabalhador (11 dígitos)
    per_apur: str              # AAAA-MM
    dm_devs: list[DmDevRequest]
    ind_retif: str = "1"       # "1" original, "2" retificação
    nr_recibo: str | None = None  # obrigatório se ind_retif=2
    ind_apuracao: str = "1"    # "1" mensal, "2" 13º
    ambiente: str = "2"        # "1" produção, "2" homologação


class EnviarS1200LoteRequest(BaseModel):
    eventos: list[EnviarS1200Request]
    ambiente: str = "2"


@router.post("/s1200/enviar")
async def enviar_s1200(req: EnviarS1200Request):
    """
    Envia S-1200 (Remuneração do Trabalhador) ao eSocial.
    Pipeline: Gerar XML → Assinar → SOAP (grupo=1) → Enviar → Salvar
    """
    if not re.match(r"^\d{4}-\d{2}$", req.per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")
    if req.ambiente not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ambiente deve ser '1' ou '2'")
    if not req.cpf_trab or len(req.cpf_trab) != 11 or not req.cpf_trab.isdigit():
        raise HTTPException(status_code=400, detail="cpf_trab deve ter 11 dígitos numéricos")
    if req.ind_retif == "2" and not req.nr_recibo:
        raise HTTPException(status_code=400, detail="nr_recibo é obrigatório para retificação (ind_retif=2)")
    if not req.dm_devs:
        raise HTTPException(status_code=400, detail="dm_devs não pode ser vazio")

    is_producao = req.ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # 1. Certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            trabalhador = {"cpfTrab": req.cpf_trab}
            dm_devs = [dm.model_dump(exclude_none=True) for dm in req.dm_devs]

            # 2. Gerar XML S-1200
            xml_bytes = S1200XMLGenerator.gerar(
                empregador=empregador,
                trabalhador=trabalhador,
                dm_devs=dm_devs,
                per_apur=req.per_apur,
                ind_retif=req.ind_retif,
                nr_recibo=req.nr_recibo,
                ind_apuracao=req.ind_apuracao,
                tp_amb=req.ambiente,
            )

            # 3. Assinar
            xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)

            # 4. Montar SOAP (grupo=1 para eventos não-periódicos por trabalhador)
            soap_envelope = SOAPEnvelopeBuilder.montar_envio(
                [xml_assinado], empregador, transmissor, grupo="1"
            )

            # 5. Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # 6. Salvar no banco
            modo = "retificacao" if req.ind_retif == "2" else "original"
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1200",
                        modo,
                        req.ambiente,
                        req.per_apur,
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        1,
                        json.dumps({"cpf": req.cpf_trab, "nr_recibo": req.nr_recibo}),
                        soap_envelope[:50000],
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]
                conn.commit()
            except Exception:
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "per_apur": req.per_apur,
                "cpf_trab": req.cpf_trab,
                "ind_retif": req.ind_retif,
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


@router.post("/s1200/enviar-lote")
async def enviar_s1200_lote(req: EnviarS1200LoteRequest):
    """
    Envia lote de S-1200 (múltiplos trabalhadores) ao eSocial.
    Máximo 50 eventos por lote.
    """
    if not req.eventos:
        raise HTTPException(status_code=400, detail="eventos não pode ser vazio")
    if len(req.eventos) > 50:
        raise HTTPException(status_code=400, detail=f"Máximo 50 eventos por lote. Recebido: {len(req.eventos)}")

    is_producao = req.ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            # Gerar + assinar todos os XMLs
            xmls_assinados = []
            for i, ev in enumerate(req.eventos, start=1):
                trabalhador = {"cpfTrab": ev.cpf_trab}
                dm_devs = [dm.model_dump(exclude_none=True) for dm in ev.dm_devs]
                xml_bytes = S1200XMLGenerator.gerar(
                    empregador=empregador,
                    trabalhador=trabalhador,
                    dm_devs=dm_devs,
                    per_apur=ev.per_apur,
                    ind_retif=ev.ind_retif,
                    nr_recibo=ev.nr_recibo,
                    ind_apuracao=ev.ind_apuracao,
                    seq=i,
                    tp_amb=req.ambiente,
                )
                xmls_assinados.append(S1010XMLSigner.assinar(xml_bytes, pfx_data, senha))

            # Montar SOAP com todos os eventos
            soap_envelope = SOAPEnvelopeBuilder.montar_envio(
                xmls_assinados, empregador, transmissor, grupo="1"
            )

            # Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # Salvar
            cpfs = [ev.cpf_trab for ev in req.eventos]
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1200",
                        "lote",
                        req.ambiente,
                        req.eventos[0].per_apur if req.eventos else "",
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        len(req.eventos),
                        json.dumps({"cpfs": cpfs}),
                        soap_envelope[:50000],
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]
                conn.commit()
            except Exception:
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "total_eventos": len(req.eventos),
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


# ── S-1210 — Pagamento de Rendimentos ─────────────────────────────


class InfoPgtoRequest(BaseModel):
    dtPgto: str          # AAAA-MM-DD
    tpPgto: str          # 1-9
    perRef: str | None = None  # AAAA-MM
    ideDmDev: str        # Identificador do demonstrativo (ref S-1200)
    vrLiq: str           # Valor líquido pago


class DedDepenRequest(BaseModel):
    tpRend: str
    cpfDep: str
    vlrDedDep: str


class InfoIRCRRequest(BaseModel):
    tpCR: str
    vrCR: str | None = None
    dedDepen: list[DedDepenRequest] | None = None


class InfoIRComplemRequest(BaseModel):
    infoIRCR: list[InfoIRCRRequest]


class EnviarS1210Request(BaseModel):
    cpf_benef: str              # CPF do beneficiário (11 dígitos)
    per_apur: str               # AAAA-MM
    info_pgtos: list[InfoPgtoRequest]
    ind_retif: str = "1"        # "1" original, "2" retificação
    nr_recibo: str | None = None  # obrigatório se ind_retif=2
    info_ir_complem: InfoIRComplemRequest | None = None
    ambiente: str = "2"         # "1" produção, "2" homologação


class EnviarS1210LoteRequest(BaseModel):
    eventos: list[EnviarS1210Request]
    ambiente: str = "2"


@router.post("/s1210/enviar")
async def enviar_s1210(req: EnviarS1210Request):
    """
    Envia S-1210 (Pagamento de Rendimentos) ao eSocial.
    Pipeline: Gerar XML → Assinar → SOAP (grupo=1) → Enviar → Salvar
    """
    if not re.match(r"^\d{4}-\d{2}$", req.per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")
    if req.ambiente not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ambiente deve ser '1' ou '2'")
    if not req.cpf_benef or len(req.cpf_benef) != 11 or not req.cpf_benef.isdigit():
        raise HTTPException(status_code=400, detail="cpf_benef deve ter 11 dígitos numéricos")
    if req.ind_retif == "2" and not req.nr_recibo:
        raise HTTPException(status_code=400, detail="nr_recibo é obrigatório para retificação (ind_retif=2)")
    if not req.info_pgtos:
        raise HTTPException(status_code=400, detail="info_pgtos não pode ser vazio")

    is_producao = req.ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # 1. Certificado ativo
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            beneficiario = {"cpfBenef": req.cpf_benef}
            info_pgtos = [p.model_dump(exclude_none=True) for p in req.info_pgtos]
            info_ir_complem = req.info_ir_complem.model_dump(exclude_none=True) if req.info_ir_complem else None

            # 2. Gerar XML S-1210
            xml_bytes = S1210XMLGenerator.gerar(
                empregador=empregador,
                beneficiario=beneficiario,
                info_pgtos=info_pgtos,
                per_apur=req.per_apur,
                ind_retif=req.ind_retif,
                nr_recibo=req.nr_recibo,
                info_ir_complem=info_ir_complem,
                tp_amb=req.ambiente,
            )

            # 3. Assinar
            xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)

            # 4. Montar SOAP (grupo=1 para eventos por trabalhador/beneficiário)
            soap_envelope = SOAPEnvelopeBuilder.montar_envio(
                [xml_assinado], empregador, transmissor, grupo="1"
            )

            # 5. Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # 6. Salvar no banco
            modo = "retificacao" if req.ind_retif == "2" else "original"
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1210",
                        modo,
                        req.ambiente,
                        req.per_apur,
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        1,
                        json.dumps({"cpf": req.cpf_benef, "nr_recibo": req.nr_recibo}),
                        soap_envelope[:50000],
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]
                conn.commit()
            except Exception:
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "per_apur": req.per_apur,
                "cpf_benef": req.cpf_benef,
                "ind_retif": req.ind_retif,
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


@router.post("/s1210/enviar-lote")
async def enviar_s1210_lote(req: EnviarS1210LoteRequest):
    """
    Envia lote de S-1210 (múltiplos beneficiários) ao eSocial.
    Máximo 50 eventos por lote.
    """
    if not req.eventos:
        raise HTTPException(status_code=400, detail="eventos não pode ser vazio")
    if len(req.eventos) > 50:
        raise HTTPException(status_code=400, detail=f"Máximo 50 eventos por lote. Recebido: {len(req.eventos)}")

    is_producao = req.ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            cnpj = cert_info["cnpj"]
            empregador = {"tpInsc": 1, "nrInsc": cnpj}
            transmissor = {"tpInsc": 1, "nrInsc": cnpj}

            # Gerar + assinar todos os XMLs
            xmls_assinados = []
            for i, ev in enumerate(req.eventos, start=1):
                beneficiario = {"cpfBenef": ev.cpf_benef}
                info_pgtos = [p.model_dump(exclude_none=True) for p in ev.info_pgtos]
                info_ir_complem = ev.info_ir_complem.model_dump(exclude_none=True) if ev.info_ir_complem else None
                xml_bytes = S1210XMLGenerator.gerar(
                    empregador=empregador,
                    beneficiario=beneficiario,
                    info_pgtos=info_pgtos,
                    per_apur=ev.per_apur,
                    ind_retif=ev.ind_retif,
                    nr_recibo=ev.nr_recibo,
                    info_ir_complem=info_ir_complem,
                    seq=i,
                    tp_amb=req.ambiente,
                )
                xmls_assinados.append(S1010XMLSigner.assinar(xml_bytes, pfx_data, senha))

            # Montar SOAP com todos os eventos
            soap_envelope = SOAPEnvelopeBuilder.montar_envio(
                xmls_assinados, empregador, transmissor, grupo="1"
            )

            # Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)

            # Salvar
            cpfs = [ev.cpf_benef for ev in req.eventos]
            try:
                cur.execute(INIT_ENVIOS_SQL)
                cur.execute(MIGRATE_ENVIOS_SQL)
                cur.execute(
                    """INSERT INTO esocial_envios
                       (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                        codigo_resposta, descricao_resposta, total_eventos,
                        rubrica_ids, xml_enviado, ocorrencias)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        "S-1210",
                        "lote",
                        req.ambiente,
                        req.eventos[0].per_apur if req.eventos else "",
                        "enviado" if resultado.get("sucesso") else "erro",
                        resultado.get("protocolo"),
                        resultado.get("codigo_resposta"),
                        resultado.get("descricao"),
                        len(req.eventos),
                        json.dumps({"cpfs": cpfs}),
                        soap_envelope[:50000],
                        json.dumps(resultado.get("ocorrencias", [])),
                    ),
                )
                envio_id = cur.fetchone()[0]
                conn.commit()
            except Exception:
                envio_id = None

            return {
                "sucesso": resultado.get("sucesso", False),
                "protocolo": resultado.get("protocolo"),
                "codigo_resposta": resultado.get("codigo_resposta"),
                "descricao": resultado.get("descricao"),
                "dh_recepcao": resultado.get("dh_recepcao"),
                "total_eventos": len(req.eventos),
                "envio_id": envio_id,
                "ocorrencias": resultado.get("ocorrencias", []),
                "erro": resultado.get("erro"),
            }
    finally:
        conn.close()


# ── Consulta Genérica de Protocolo ────────────────────────────────


@router.get("/consultar/{protocolo}")
async def consultar_protocolo(protocolo: str, ambiente: str = "2"):
    """
    Consulta resultado do processamento de QUALQUER lote pelo protocolo.
    Funciona para S-1010, S-1200, S-1210, S-1298, S-1299.
    Atualiza esocial_envios automaticamente.
    """
    is_producao = ambiente == "1"
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cert_info = _load_cert_ativo(cur)
            if not cert_info:
                raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

            senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
            with open(cert_info["arquivo_path"], "rb") as f:
                pfx_data = f.read()

            url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
            resultado = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

            # Atualizar envio no banco
            xml_resposta = resultado.pop("xml_resposta", None)
            eventos = resultado.get("eventos", [])
            todos_sucesso = resultado.get("sucesso", False) and all(
                str(ev.get("codigo_resposta", "")) in ("201", "202") for ev in eventos
            )
            status_final = "processado" if todos_sucesso else "erro"

            nr_recibo = None
            for ev in eventos:
                if ev.get("nr_recibo"):
                    nr_recibo = ev["nr_recibo"]
                    break

            try:
                cur.execute(
                    """UPDATE esocial_envios
                       SET status = %s, recibo_consulta = %s, xml_retorno = %s,
                           nr_recibo = %s, updated_at = NOW()
                       WHERE protocolo_envio = %s""",
                    (status_final, json.dumps(resultado), xml_resposta,
                     nr_recibo, protocolo),
                )
                conn.commit()
            except Exception:
                pass

            return resultado
    finally:
        conn.close()


# ── Totalizadores — Consulta no DB ────────────────────────────────


@router.get("/totalizadores/{cpf}/{per_apur}")
async def consultar_totalizadores(cpf: str, per_apur: str):
    """
    Consulta totalizadores (S-5001, S-5002, S-5012) de um CPF/período
    já importados no explorador_eventos.
    Retorna dados para conferência antes/depois da correção.
    """
    if not re.match(r"^\d{4}-\d{2}$", per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")
    if not cpf or not cpf.isdigit():
        raise HTTPException(status_code=400, detail="CPF deve conter apenas dígitos")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # S-5001 — INSS/FGTS
            cur.execute(
                """SELECT nr_recibo, dados_json, dt_processamento, id_evento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-5001' AND cpf = %s AND per_apur = %s
                   ORDER BY dt_processamento DESC LIMIT 1""",
                (cpf, per_apur),
            )
            row_5001 = cur.fetchone()
            s5001 = None
            if row_5001:
                s5001 = {
                    "nr_recibo": row_5001[0],
                    "dados": _safe_json(row_5001[1], {}),
                    "dt_processamento": str(row_5001[2]) if row_5001[2] else None,
                    "id_evento": row_5001[3],
                }

            # S-5002 — IRRF por CPF
            cur.execute(
                """SELECT nr_recibo, dados_json, dt_processamento, id_evento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-5002' AND cpf = %s AND per_apur = %s
                   ORDER BY dt_processamento DESC LIMIT 1""",
                (cpf, per_apur),
            )
            row_5002 = cur.fetchone()
            s5002 = None
            if row_5002:
                s5002 = {
                    "nr_recibo": row_5002[0],
                    "dados": _safe_json(row_5002[1], {}),
                    "dt_processamento": str(row_5002[2]) if row_5002[2] else None,
                    "id_evento": row_5002[3],
                }

            # S-5012 — IRRF total (não tem CPF, é consolidado por empregador)
            cur.execute(
                """SELECT nr_recibo, dados_json, dt_processamento, id_evento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-5012' AND per_apur = %s
                   ORDER BY dt_processamento DESC LIMIT 1""",
                (per_apur,),
            )
            row_5012 = cur.fetchone()
            s5012 = None
            if row_5012:
                s5012 = {
                    "nr_recibo": row_5012[0],
                    "dados": _safe_json(row_5012[1], {}),
                    "dt_processamento": str(row_5012[2]) if row_5012[2] else None,
                    "id_evento": row_5012[3],
                }

            return {
                "cpf": cpf,
                "per_apur": per_apur,
                "s5001_inss_fgts": s5001,
                "s5002_irrf_cpf": s5002,
                "s5012_irrf_total": s5012,
                "resumo": {
                    "vlrRendTrib": s5002["dados"].get("totApurMen_vlrRendTrib") if s5002 else None,
                    "vlrPrevOficial": s5002["dados"].get("totApurMen_vlrPrevOficial") if s5002 else None,
                    "vlrCRMen": s5002["dados"].get("totApurMen_vlrCRMen") if s5002 else None,
                    "infoCpCalc": s5001["dados"].get("infoCpCalc") if s5001 else None,
                },
            }
    finally:
        conn.close()


@router.get("/totalizadores/comparar/{cpf}/{per_apur}")
async def comparar_totalizadores(cpf: str, per_apur: str):
    """
    Compara totalizadores ANTES (importação original) vs DEPOIS (mais recente)
    de um CPF/período. Útil para validar se a correção surtiu efeito.
    Retorna todos os S-5002 do CPF/período ordenados por processamento.
    """
    if not re.match(r"^\d{4}-\d{2}$", per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Todos os S-5002 desse CPF/período
            cur.execute(
                """SELECT nr_recibo, dados_json, dt_processamento, id_evento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-5002' AND cpf = %s AND per_apur = %s
                   ORDER BY dt_processamento ASC""",
                (cpf, per_apur),
            )
            rows = cur.fetchall()

            historico = []
            for r in rows:
                dados = _safe_json(r[1], {})
                historico.append({
                    "nr_recibo": r[0],
                    "dt_processamento": str(r[2]) if r[2] else None,
                    "id_evento": r[3],
                    "vlrRendTrib": dados.get("totApurMen_vlrRendTrib"),
                    "vlrPrevOficial": dados.get("totApurMen_vlrPrevOficial"),
                    "vlrCRMen": dados.get("totApurMen_vlrCRMen"),
                    "infoIR": dados.get("infoIR", []),
                })

            return {
                "cpf": cpf,
                "per_apur": per_apur,
                "total_registros": len(historico),
                "historico_s5002": historico,
                "antes": historico[0] if historico else None,
                "depois": historico[-1] if len(historico) > 1 else None,
            }
    finally:
        conn.close()
