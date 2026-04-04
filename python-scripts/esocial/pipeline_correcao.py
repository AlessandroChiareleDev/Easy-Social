"""
Pipeline de Correção — Orquestrador do fluxo completo de retificação eSocial

Encadeia automaticamente:
  S-1010 (corrigir rubrica) → S-1298 (reabrir) → S-1200 (retificar remuneração)
  → S-1210 (retificar pagamento) → S-1299 (fechar) → conferir totalizadores

Cada etapa: Gerar XML → Assinar → SOAP → Enviar → Consultar (com polling)
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# ── Polling config ────────────────────────────────────────────────

MAX_POLL_RETRIES = 5
POLL_DELAY_SECS = 10  # seconds between consultation attempts

# ── DB Schema ─────────────────────────────────────────────────────

INIT_PIPELINE_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_correcao (
    id SERIAL PRIMARY KEY,
    cpf VARCHAR(11) NOT NULL,
    per_apur VARCHAR(7) NOT NULL,
    ambiente VARCHAR(2) NOT NULL DEFAULT '2',
    status VARCHAR(30) NOT NULL DEFAULT 'iniciado',
    step_atual INTEGER DEFAULT 0,
    -- Step results
    s1010_protocolo VARCHAR(100),
    s1010_nr_recibo VARCHAR(100),
    s1298_protocolo VARCHAR(100),
    s1298_nr_recibo VARCHAR(100),
    s1200_protocolo VARCHAR(100),
    s1200_nr_recibo VARCHAR(100),
    s1210_protocolo VARCHAR(100),
    s1210_nr_recibo VARCHAR(100),
    s1299_protocolo VARCHAR(100),
    s1299_nr_recibo VARCHAR(100),
    steps_log JSONB DEFAULT '[]',
    erro TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""


# ── Request/Response Models ───────────────────────────────────────


class ResponsavelRequest(BaseModel):
    nm_resp: str
    cpf_resp: str
    telefone: str
    email: str


class PipelineRequest(BaseModel):
    """Input completo para o pipeline de correção de um CPF/período."""
    # Alvo
    cpf: str               # 11 dígitos
    per_apur: str           # AAAA-MM
    ambiente: str = "2"     # "1" = produção, "2" = homologação

    # Step 1 (opcional): S-1010 — lista de cod_rubrica a corrigir
    rubrica_ids: list[str] | None = None

    # Step 2: S-1298 — reabertura
    skip_s1298: bool = False      # pula se período NÃO está fechado
    ind_apuracao: str = "1"       # "1" = mensal, "2" = 13º

    # Step 3: S-1200 retificação
    s1200_nr_recibo: str          # recibo original do S-1200
    s1200_dm_devs: list[dict]     # estrutura completa dm_devs

    # Step 4: S-1210 retificação
    s1210_nr_recibo: str          # recibo original do S-1210
    s1210_info_pgtos: list[dict]  # estrutura completa info_pgtos
    s1210_info_ir_complem: dict | None = None

    # Step 5: S-1299 — fechamento (ideRespInf removido no leiaute S-1.3)
    responsavel: ResponsavelRequest | None = None


class StepResult(BaseModel):
    step: int
    evento: str
    status: str             # "ok", "erro", "pulado", "timeout"
    protocolo: str | None = None
    nr_recibo: str | None = None
    codigo_resposta: str | None = None
    descricao: str | None = None
    detalhes: dict | None = None


class PipelineResponse(BaseModel):
    pipeline_id: int | None = None
    cpf: str
    per_apur: str
    status: str             # "completo", "erro", "parcial"
    total_steps: int = 0
    steps_ok: int = 0
    steps: list[StepResult] = []
    totalizadores: dict | None = None


# ── Helpers ───────────────────────────────────────────────────────


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


def _load_cert_ativo() -> dict | None:
    local_conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with local_conn.cursor() as cur:
            cur.execute(
                "SELECT id, cnpj, titular, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0], "cnpj": row[1], "titular": row[2],
                "arquivo_path": row[3], "senha_encrypted": row[4],
            }
    finally:
        local_conn.close()


def _safe_json(val, default=None):
    if val is None:
        return default
    if isinstance(val, (list, dict)):
        return val
    return json.loads(val)


def _enviar_e_consultar(
    xml_bytes: bytes,
    pfx_data: bytes,
    senha: str,
    empregador: dict,
    transmissor: dict,
    grupo: str,
    is_producao: bool,
) -> dict:
    """
    Pipeline atômico: Assinar → SOAP → Enviar → Polling de consulta.
    Retorna dict com {sucesso, protocolo, nr_recibo, codigo_resposta, descricao, eventos, erro}.
    """
    # 1. Assinar
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)

    # 2. SOAP
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador, transmissor, grupo=grupo
    )

    # 3. Enviar
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        return {
            "sucesso": False,
            "protocolo": resultado.get("protocolo"),
            "nr_recibo": None,
            "codigo_resposta": resultado.get("codigo_resposta"),
            "descricao": resultado.get("descricao"),
            "eventos": [],
            "erro": resultado.get("erro") or resultado.get("descricao"),
        }

    protocolo = resultado.get("protocolo")
    if not protocolo:
        return {
            "sucesso": False, "protocolo": None, "nr_recibo": None,
            "codigo_resposta": resultado.get("codigo_resposta"),
            "descricao": "Envio OK mas sem protocolo",
            "eventos": [], "erro": "Sem protocolo no retorno",
        }

    # 4. Polling de consulta
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
    nr_recibo = None
    consulta_result = None

    for attempt in range(MAX_POLL_RETRIES):
        time.sleep(POLL_DELAY_SECS)
        consulta_result = ESocialClient.consultar_lote(
            protocolo, pfx_data, senha, url=url_consulta
        )
        eventos = consulta_result.get("eventos", [])

        # Check if processing is done
        if consulta_result.get("sucesso") and eventos:
            for ev in eventos:
                if ev.get("nr_recibo"):
                    nr_recibo = ev["nr_recibo"]
                    break
            if nr_recibo:
                break
        elif consulta_result.get("codigo_resposta") == "101":
            # 101 = "Em processamento" — retry
            continue
        elif consulta_result.get("sucesso") is False:
            break

    return {
        "sucesso": nr_recibo is not None,
        "protocolo": protocolo,
        "nr_recibo": nr_recibo,
        "codigo_resposta": consulta_result.get("codigo_resposta") if consulta_result else None,
        "descricao": consulta_result.get("descricao") if consulta_result else None,
        "eventos": consulta_result.get("eventos", []) if consulta_result else [],
        "erro": None if nr_recibo else "Consulta não retornou recibo após polling",
    }


# ── Pipeline Executor ─────────────────────────────────────────────


def _executar_pipeline(
    req: PipelineRequest,
    pfx_data: bytes,
    senha: str,
    cnpj: str,
    conn,
) -> PipelineResponse:
    """
    Executa o pipeline completo de 5 etapas sincronamente.
    Cada etapa: gerar XML → assinar → SOAP → enviar → consultar.
    Se uma etapa falha, retorna resultado parcial.
    """
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    transmissor = {"tpInsc": 1, "nrInsc": cnpj}
    is_producao = req.ambiente == "1"
    tp_amb = req.ambiente

    steps: list[StepResult] = []
    steps_ok = 0

    # ── Criar registro no banco ──
    pipeline_id = None
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_PIPELINE_SQL)
            cur.execute(
                """INSERT INTO pipeline_correcao (cpf, per_apur, ambiente, status)
                   VALUES (%s, %s, %s, 'iniciado') RETURNING id""",
                (req.cpf, req.per_apur, req.ambiente),
            )
            pipeline_id = cur.fetchone()[0]
            conn.commit()
    except Exception:
        pass

    def _update_pipeline(step_num, protocolo=None, nr_recibo=None, status="em_andamento", erro=None):
        try:
            col_map = {1: "s1010", 2: "s1298", 3: "s1200", 4: "s1210", 5: "s1299"}
            prefix = col_map.get(step_num, "")
            with conn.cursor() as cur:
                cur.execute(
                    f"""UPDATE pipeline_correcao
                        SET step_atual = %s, {prefix}_protocolo = COALESCE(%s, {prefix}_protocolo),
                            {prefix}_nr_recibo = COALESCE(%s, {prefix}_nr_recibo),
                            status = %s, erro = %s, updated_at = NOW(),
                            steps_log = %s
                        WHERE id = %s""",
                    (step_num, protocolo, nr_recibo, status, erro,
                     json.dumps([s.model_dump() for s in steps]), pipeline_id),
                )
                conn.commit()
        except Exception:
            pass

    def _make_error_response(msg):
        return PipelineResponse(
            pipeline_id=pipeline_id, cpf=req.cpf, per_apur=req.per_apur,
            status="erro", total_steps=len(steps), steps_ok=steps_ok, steps=steps,
        )

    # ══════════════════════════════════════════════════════════════
    # STEP 1: S-1010 (opcional — corrigir rubricas)
    # ══════════════════════════════════════════════════════════════

    if req.rubrica_ids:
        _update_pipeline(1, status="em_andamento")

        try:
            # Buscar dados das rubricas no cruzamento_eb
            # IMPORTANTE: incid_base_legal_* contém os valores CORRETOS (formato "CODE - Base legal")
            #             incid_inss/irrf/fgts contém os valores ATUAIS do sistema (potencialmente ERRADOS)
            with conn.cursor() as cur:
                placeholders = ",".join(["%s"] * len(req.rubrica_ids))
                cur.execute(
                    f"""SELECT cod_rubrica, descricao, cod_natureza,
                               incid_base_legal_inss, incid_base_legal_irrf,
                               incid_base_legal_fgts, ini_valid_esocial
                        FROM cruzamento_eb
                        WHERE cod_rubrica IN ({placeholders})""",
                    req.rubrica_ids,
                )
                rows = cur.fetchall()

            if not rows:
                step = StepResult(step=1, evento="S-1010", status="erro",
                                  descricao="Nenhuma rubrica encontrada no cruzamento_eb")
                steps.append(step)
                _update_pipeline(1, status="erro", erro="Rubricas não encontradas")
                return _make_error_response("Rubricas não encontradas")

            def _extrair_codigo(base_legal: str | None) -> str:
                """Extrai código numérico de 'CODE - Base legal text'. Ex: '11 - Artigo...' → '11'"""
                if not base_legal or base_legal.startswith("Rubrica não encontrada"):
                    return "00"
                return base_legal.split(" - ")[0].strip() or "00"

            # Gerar XMLs para cada rubrica
            xmls = []
            for i, row in enumerate(rows):
                # row: 0=cod_rubrica, 1=descricao, 2=cod_natureza,
                #      3=base_legal_inss, 4=base_legal_irrf, 5=base_legal_fgts,
                #      6=ini_valid_esocial
                nat_rubr = (row[2] or "").split(" - ")[0].strip() if row[2] else ""
                rubrica = {
                    "codRubr": row[0],
                    "ideTabRubr": "1",
                    "iniValid": row[6] or req.per_apur.replace("-", "-"),
                    "dscRubr": (row[1] or "RUBRICA")[:100],
                    "natRubr": nat_rubr,
                    "tpRubr": "1",
                    "codIncCP": _extrair_codigo(row[3]),
                    "codIncIRRF": _extrair_codigo(row[4]),
                    "codIncFGTS": _extrair_codigo(row[5]),
                }

                xml_bytes = S1010XMLGenerator.gerar_alteracao(
                    empregador, rubrica, seq=i + 1, tp_amb=tp_amb
                )
                xmls.append(xml_bytes)

            # Assinar todos
            xmls_assinados = [S1010XMLSigner.assinar(x, pfx_data, senha) for x in xmls]

            # SOAP (grupo=1 para tabelas)
            soap = SOAPEnvelopeBuilder.montar_envio(
                xmls_assinados, empregador, transmissor, grupo="1"
            )

            # Enviar
            url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
            resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

            if not resultado.get("sucesso"):
                step = StepResult(
                    step=1, evento="S-1010", status="erro",
                    protocolo=resultado.get("protocolo"),
                    codigo_resposta=resultado.get("codigo_resposta"),
                    descricao=resultado.get("descricao"),
                )
                steps.append(step)
                _update_pipeline(1, resultado.get("protocolo"), status="erro",
                                 erro=resultado.get("descricao"))
                return _make_error_response("S-1010 envio falhou")

            # Polling
            protocolo = resultado.get("protocolo")
            url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
            nr_recibo_s1010 = None

            for _ in range(MAX_POLL_RETRIES):
                time.sleep(POLL_DELAY_SECS)
                consulta = ESocialClient.consultar_lote(
                    protocolo, pfx_data, senha, url=url_consulta
                )
                for ev in consulta.get("eventos", []):
                    if ev.get("nr_recibo"):
                        nr_recibo_s1010 = ev["nr_recibo"]
                        break
                if nr_recibo_s1010 or consulta.get("codigo_resposta") != "101":
                    break

            step = StepResult(
                step=1, evento="S-1010",
                status="ok" if nr_recibo_s1010 else "timeout",
                protocolo=protocolo, nr_recibo=nr_recibo_s1010,
                codigo_resposta=consulta.get("codigo_resposta") if consulta else None,
                descricao=consulta.get("descricao") if consulta else None,
                detalhes={"rubricas": req.rubrica_ids},
            )
            steps.append(step)

            if nr_recibo_s1010:
                steps_ok += 1
                _update_pipeline(1, protocolo, nr_recibo_s1010, status="em_andamento")
            else:
                _update_pipeline(1, protocolo, status="erro", erro="Timeout na consulta S-1010")
                return _make_error_response("S-1010 consulta timeout")

        except Exception as e:
            step = StepResult(step=1, evento="S-1010", status="erro", descricao=str(e))
            steps.append(step)
            _update_pipeline(1, status="erro", erro=str(e))
            return _make_error_response(str(e))
    else:
        steps.append(StepResult(step=1, evento="S-1010", status="pulado",
                                descricao="Sem rubrica_ids — já corrigido previamente"))
        steps_ok += 1

    # ══════════════════════════════════════════════════════════════
    # STEP 2: S-1298 (Reabertura)
    # ══════════════════════════════════════════════════════════════

    if not req.skip_s1298:
        _update_pipeline(2, status="em_andamento")

        try:
            xml_bytes = S1298XMLGenerator.gerar(
                empregador, req.per_apur, req.ind_apuracao, tp_amb=tp_amb
            )
            result = _enviar_e_consultar(
                xml_bytes, pfx_data, senha, empregador, transmissor,
                grupo="3", is_producao=is_producao,
            )

            step = StepResult(
                step=2, evento="S-1298",
                status="ok" if result["sucesso"] else "erro",
                protocolo=result["protocolo"],
                nr_recibo=result["nr_recibo"],
                codigo_resposta=result["codigo_resposta"],
                descricao=result["descricao"],
            )
            steps.append(step)

            if result["sucesso"]:
                steps_ok += 1
                _update_pipeline(2, result["protocolo"], result["nr_recibo"])
            else:
                _update_pipeline(2, result["protocolo"], status="erro",
                                 erro=result.get("erro"))
                return _make_error_response("S-1298 falhou")

        except Exception as e:
            step = StepResult(step=2, evento="S-1298", status="erro", descricao=str(e))
            steps.append(step)
            _update_pipeline(2, status="erro", erro=str(e))
            return _make_error_response(str(e))
    else:
        steps.append(StepResult(step=2, evento="S-1298", status="pulado",
                                descricao="skip_s1298=True — período não fechado"))
        steps_ok += 1

    # ══════════════════════════════════════════════════════════════
    # STEP 3: S-1200 (Retificação de Remuneração)
    # ══════════════════════════════════════════════════════════════

    _update_pipeline(3, status="em_andamento")

    try:
        xml_bytes = S1200XMLGenerator.gerar(
            empregador=empregador,
            trabalhador={"cpfTrab": req.cpf},
            dm_devs=req.s1200_dm_devs,
            per_apur=req.per_apur,
            ind_retif="2",
            nr_recibo=req.s1200_nr_recibo,
            ind_apuracao=req.ind_apuracao,
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(
            xml_bytes, pfx_data, senha, empregador, transmissor,
            grupo="3", is_producao=is_producao,
        )

        step = StepResult(
            step=3, evento="S-1200",
            status="ok" if result["sucesso"] else "erro",
            protocolo=result["protocolo"],
            nr_recibo=result["nr_recibo"],
            codigo_resposta=result["codigo_resposta"],
            descricao=result["descricao"],
        )
        steps.append(step)

        if result["sucesso"]:
            steps_ok += 1
            _update_pipeline(3, result["protocolo"], result["nr_recibo"])
        else:
            _update_pipeline(3, result["protocolo"], status="erro",
                             erro=result.get("erro"))
            return _make_error_response("S-1200 retificação falhou")

    except Exception as e:
        step = StepResult(step=3, evento="S-1200", status="erro", descricao=str(e))
        steps.append(step)
        _update_pipeline(3, status="erro", erro=str(e))
        return _make_error_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 4: S-1210 (Retificação de Pagamento)
    # ══════════════════════════════════════════════════════════════

    _update_pipeline(4, status="em_andamento")

    try:
        xml_bytes = S1210XMLGenerator.gerar(
            empregador=empregador,
            beneficiario={"cpfBenef": req.cpf},
            info_pgtos=req.s1210_info_pgtos,
            per_apur=req.per_apur,
            ind_retif="2",
            nr_recibo=req.s1210_nr_recibo,
            info_ir_complem=req.s1210_info_ir_complem,
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(
            xml_bytes, pfx_data, senha, empregador, transmissor,
            grupo="3", is_producao=is_producao,
        )

        step = StepResult(
            step=4, evento="S-1210",
            status="ok" if result["sucesso"] else "erro",
            protocolo=result["protocolo"],
            nr_recibo=result["nr_recibo"],
            codigo_resposta=result["codigo_resposta"],
            descricao=result["descricao"],
        )
        steps.append(step)

        if result["sucesso"]:
            steps_ok += 1
            _update_pipeline(4, result["protocolo"], result["nr_recibo"])
        else:
            _update_pipeline(4, result["protocolo"], status="erro",
                             erro=result.get("erro"))
            return _make_error_response("S-1210 retificação falhou")

    except Exception as e:
        step = StepResult(step=4, evento="S-1210", status="erro", descricao=str(e))
        steps.append(step)
        _update_pipeline(4, status="erro", erro=str(e))
        return _make_error_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 5: S-1299 (Fechamento)
    # ══════════════════════════════════════════════════════════════

    _update_pipeline(5, status="em_andamento")

    try:
        xml_bytes = S1299XMLGenerator.gerar(
            empregador=empregador,
            per_apur=req.per_apur,
            ind_apuracao=req.ind_apuracao,
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(
            xml_bytes, pfx_data, senha, empregador, transmissor,
            grupo="3", is_producao=is_producao,
        )

        step = StepResult(
            step=5, evento="S-1299",
            status="ok" if result["sucesso"] else "erro",
            protocolo=result["protocolo"],
            nr_recibo=result["nr_recibo"],
            codigo_resposta=result["codigo_resposta"],
            descricao=result["descricao"],
        )
        steps.append(step)

        if result["sucesso"]:
            steps_ok += 1
            _update_pipeline(5, result["protocolo"], result["nr_recibo"], status="completo")
        else:
            _update_pipeline(5, result["protocolo"], status="erro",
                             erro=result.get("erro"))
            return _make_error_response("S-1299 fechamento falhou")

    except Exception as e:
        step = StepResult(step=5, evento="S-1299", status="erro", descricao=str(e))
        steps.append(step)
        _update_pipeline(5, status="erro", erro=str(e))
        return _make_error_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # RESULTADO FINAL
    # ══════════════════════════════════════════════════════════════

    return PipelineResponse(
        pipeline_id=pipeline_id,
        cpf=req.cpf,
        per_apur=req.per_apur,
        status="completo",
        total_steps=len(steps),
        steps_ok=steps_ok,
        steps=steps,
    )


# ── Routes ────────────────────────────────────────────────────────


@router.post("/executar")
async def executar_pipeline(req: PipelineRequest):
    """
    Executa o pipeline completo de correção para um CPF/período.

    Encadeia: S-1010 → S-1298 → S-1200 (retif) → S-1210 (retif) → S-1299
    Cada etapa aguarda confirmação (polling) antes de prosseguir.

    ⚠ Operação longa (~60-90s). Para teste com 1 CPF.
    """
    # Validações
    if not req.cpf or len(req.cpf) != 11 or not req.cpf.isdigit():
        raise HTTPException(status_code=400, detail="CPF deve ter 11 dígitos numéricos")
    if not re.match(r"^\d{4}-\d{2}$", req.per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")
    if req.ambiente not in ("1", "2"):
        raise HTTPException(status_code=400, detail="ambiente deve ser '1' ou '2'")
    if not req.s1200_dm_devs:
        raise HTTPException(status_code=400, detail="s1200_dm_devs é obrigatório")
    if not req.s1200_nr_recibo:
        raise HTTPException(status_code=400, detail="s1200_nr_recibo é obrigatório")
    if not req.s1210_info_pgtos:
        raise HTTPException(status_code=400, detail="s1210_info_pgtos é obrigatório")
    if not req.s1210_nr_recibo:
        raise HTTPException(status_code=400, detail="s1210_nr_recibo é obrigatório")

    # Certificado
    cert_info = _load_cert_ativo()
    if not cert_info:
        raise HTTPException(status_code=400, detail="Nenhum certificado A1 ativo")

    senha = CertificateManager.decrypt_password(cert_info["senha_encrypted"])
    with open(cert_info["arquivo_path"], "rb") as f:
        pfx_data = f.read()

    cnpj = cert_info["cnpj"]

    conn = _get_conn()
    try:
        result = _executar_pipeline(req, pfx_data, senha, cnpj, conn)
        return result.model_dump()
    finally:
        conn.close()


@router.get("/status/{pipeline_id}")
async def consultar_pipeline(pipeline_id: int):
    """Consulta status de um pipeline já iniciado."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, cpf, per_apur, ambiente, status, step_atual,
                          s1010_protocolo, s1010_nr_recibo,
                          s1298_protocolo, s1298_nr_recibo,
                          s1200_protocolo, s1200_nr_recibo,
                          s1210_protocolo, s1210_nr_recibo,
                          s1299_protocolo, s1299_nr_recibo,
                          steps_log, erro, created_at, updated_at
                   FROM pipeline_correcao WHERE id = %s""",
                (pipeline_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Pipeline não encontrado")

            return {
                "pipeline_id": row[0],
                "cpf": row[1],
                "per_apur": row[2],
                "ambiente": row[3],
                "status": row[4],
                "step_atual": row[5],
                "s1010": {"protocolo": row[6], "nr_recibo": row[7]},
                "s1298": {"protocolo": row[8], "nr_recibo": row[9]},
                "s1200": {"protocolo": row[10], "nr_recibo": row[11]},
                "s1210": {"protocolo": row[12], "nr_recibo": row[13]},
                "s1299": {"protocolo": row[14], "nr_recibo": row[15]},
                "steps_log": _safe_json(row[16], []),
                "erro": row[17],
                "created_at": str(row[18]) if row[18] else None,
                "updated_at": str(row[19]) if row[19] else None,
            }
    finally:
        conn.close()


@router.get("/historico")
async def listar_pipelines(limit: int = 20):
    """Lista pipelines executados."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_PIPELINE_SQL)
            conn.commit()
            cur.execute(
                """SELECT id, cpf, per_apur, ambiente, status, step_atual,
                          s1010_nr_recibo, s1298_nr_recibo, s1200_nr_recibo,
                          s1210_nr_recibo, s1299_nr_recibo,
                          erro, created_at, updated_at
                   FROM pipeline_correcao
                   ORDER BY created_at DESC LIMIT %s""",
                (limit,),
            )
            rows = cur.fetchall()

            return [
                {
                    "pipeline_id": r[0], "cpf": r[1], "per_apur": r[2],
                    "ambiente": r[3], "status": r[4], "step_atual": r[5],
                    "recibos": {
                        "s1010": r[6], "s1298": r[7], "s1200": r[8],
                        "s1210": r[9], "s1299": r[10],
                    },
                    "erro": r[11],
                    "created_at": str(r[12]) if r[12] else None,
                    "updated_at": str(r[13]) if r[13] else None,
                }
                for r in rows
            ]
    finally:
        conn.close()


@router.get("/preparar/{cpf}/{per_apur}")
async def preparar_pipeline(cpf: str, per_apur: str):
    """
    Busca dados necessários para montar o input do pipeline.
    Retorna nr_recibo do S-1200 e S-1210 originais + dados do explorador.

    ⚠ Os dados completos (dm_devs, info_pgtos) precisam vir do XML original.
    Esta rota fornece os metadados disponíveis no explorador_eventos.
    """
    if not re.match(r"^\d{4}-\d{2}$", per_apur):
        raise HTTPException(status_code=400, detail="per_apur deve ter formato AAAA-MM")

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # S-1200 mais recente para esse CPF/período
            cur.execute(
                """SELECT nr_recibo, dados_json, id_evento, dt_processamento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-1200' AND cpf = %s AND per_apur = %s
                   ORDER BY dt_processamento DESC LIMIT 1""",
                (cpf, per_apur),
            )
            s1200 = cur.fetchone()

            # S-1210 mais recente
            cur.execute(
                """SELECT nr_recibo, dados_json, id_evento, dt_processamento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-1210' AND cpf = %s AND per_apur = %s
                   ORDER BY dt_processamento DESC LIMIT 1""",
                (cpf, per_apur),
            )
            s1210 = cur.fetchone()

            # S-1299 — período fechado?
            cur.execute(
                """SELECT nr_recibo, dt_processamento
                   FROM explorador_eventos
                   WHERE tipo_evento = 'S-1299' AND per_apur = %s
                   ORDER BY dt_processamento DESC LIMIT 1""",
                (per_apur,),
            )
            s1299 = cur.fetchone()

            # Rubricas com divergência para esse CPF (do cruzamento)
            cur.execute(
                """SELECT DISTINCT cod_rubrica
                   FROM cruzamento_eb
                   WHERE divergencia = TRUE AND envio_status != 'feito'
                   LIMIT 50""",
            )
            rubricas_pendentes = [r[0] for r in cur.fetchall()]

            return {
                "cpf": cpf,
                "per_apur": per_apur,
                "periodo_fechado": s1299 is not None,
                "s1200": {
                    "nr_recibo": s1200[0] if s1200 else None,
                    "dados_explorador": _safe_json(s1200[1], {}) if s1200 else None,
                    "id_evento": s1200[2] if s1200 else None,
                    "dt_processamento": str(s1200[3]) if s1200 and s1200[3] else None,
                    "nota": "dm_devs completo deve ser extraído do XML original",
                } if s1200 else None,
                "s1210": {
                    "nr_recibo": s1210[0] if s1210 else None,
                    "dados_explorador": _safe_json(s1210[1], {}) if s1210 else None,
                    "id_evento": s1210[2] if s1210 else None,
                    "dt_processamento": str(s1210[3]) if s1210 and s1210[3] else None,
                    "nota": "info_pgtos completo deve ser extraído do XML original",
                } if s1210 else None,
                "s1299_mais_recente": {
                    "nr_recibo": s1299[0],
                    "dt_processamento": str(s1299[1]) if s1299[1] else None,
                } if s1299 else None,
                "rubricas_pendentes": rubricas_pendentes[:10],
                "instrucoes": (
                    "Para montar o PipelineRequest completo, extraia dm_devs e info_pgtos "
                    "do XML original do S-1200 e S-1210 (arquivo baixado por Denis). "
                    "Use os nr_recibo acima nos campos s1200_nr_recibo e s1210_nr_recibo."
                ),
            }
    finally:
        conn.close()
