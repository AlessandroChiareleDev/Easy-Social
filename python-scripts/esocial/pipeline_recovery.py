"""
Pipeline de Recuperação — Fluxo multi-período para desbloquear S-1200.

Caso: S-1200 de Dez/2024 bloqueado porque S-1210 de Jan/2025
referencia os dmDevs (error 989).

Retificar S-1210 com dados idênticos NÃO libera os dmDevs.
A solução correta é EXCLUIR o S-1210 bloqueador via S-3000,
retificar o S-1200, e depois RE-INCLUIR o S-1210.

Fluxo (8 steps):
  1. S-1298 Jan/2025 (reabrir janeiro)
  2. S-1298 Dez/2024 (reabrir dezembro)
  3. S-3000 excluir S-1210 Jan/2025 (remove referências dmDevs)
  4. S-1200 retif Dez/2024 (agora desbloqueado)
  5. S-1210 retif Dez/2024 (retificar com dados idênticos → recalcular S-5002)
  6. S-1210 incluir Jan/2025 (re-incluir o evento excluído, como original)
  7. S-1299 Dez/2024 (fechar dezembro)
  8. S-1299 Jan/2025 (fechar janeiro)

Cada etapa: Gerar XML → Assinar → SOAP → Enviar → Polling consulta
"""

import asyncio
import json
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import psycopg2
import sys
import os
from requests.exceptions import ConnectionError as RequestsConnectionError
from http.client import RemoteDisconnected
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db_config import DB_CONFIG, LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

router = APIRouter(prefix="/api/pipeline", tags=["pipeline-recovery"])

MAX_POLL_RETRIES = 8
POLL_DELAY_SECS = 15
MAX_SEND_RETRIES = 5
SEND_RETRY_DELAY = 10

CONNECTION_ERROR_KEYWORDS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "cancelamento", "timed out",
    "connection refused", "10054", "10053", "winerror",
]

logger = logging.getLogger(__name__)

def _is_connection_error(resultado: dict) -> bool:
    """Check if enviar_lote result dict indicates a transient connection error."""
    if resultado.get("sucesso"):
        return False
    erro = (resultado.get("erro") or resultado.get("descricao") or "").lower()
    return any(kw in erro for kw in CONNECTION_ERROR_KEYWORDS)


# ── Models ────────────────────────────────────────────────────────

class RecoveryStepResult(BaseModel):
    step: int
    evento: str
    per_apur: str
    status: str           # "ok", "erro", "timeout"
    protocolo: str | None = None
    nr_recibo: str | None = None
    codigo_resposta: str | None = None
    descricao: str | None = None
    detalhes: dict | None = None


class RecoveryRequest(BaseModel):
    """Input para o pipeline de recuperação multi-período."""
    cpf: str
    ambiente: str = "1"         # "1" = produção
    ind_apuracao: str = "1"     # "1" = mensal

    # Período bloqueado (alvo)
    per_apur_alvo: str          # ex: "2024-12"
    s1200_nr_recibo: str        # recibo S-1200 do período alvo
    s1200_dm_devs: list[dict]   # payload completo dm_devs do S-1200

    # S-1210 do período alvo
    s1210_alvo_nr_recibo: str
    s1210_alvo_info_pgtos: list[dict]
    s1210_alvo_info_ir_complem: dict | None = None

    # Período bloqueador (que referencia os dmDevs)
    per_apur_bloqueador: str    # ex: "2025-01"
    s1210_bloq_nr_recibo: str   # recibo S-1210 do período bloqueador
    s1210_bloq_info_pgtos: list[dict]  # payload info_pgtos do S-1210 bloqueador


class RecoveryResponse(BaseModel):
    cpf: str
    status: str               # "completo", "erro", "parcial"
    total_steps: int
    steps_ok: int
    steps: list[RecoveryStepResult]


# ── Helpers ───────────────────────────────────────────────────────

def _load_cert():
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "cnpj": row[0],
                "arquivo_path": row[1],
                "senha": CertificateManager.decrypt_password(row[2]),
            }
    finally:
        conn.close()


def _enviar_e_consultar(xml_bytes, pfx_data, senha, empregador, grupo, is_producao):
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=grupo)
    url = SOAPEnvelopeBuilder.url_envio(producao=is_producao)

    # Retry loop for transient connection errors
    # NOTE: ESocialClient.enviar_lote catches ALL exceptions internally
    # and returns {"sucesso": False, "erro": "..."} — never raises.
    # So retry must check the result dict, not catch exceptions.
    resultado = None
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url)
        if resultado.get("sucesso") or not _is_connection_error(resultado):
            break  # either success or a non-connection error (don't retry)
        erro_msg = resultado.get("erro") or resultado.get("descricao") or "?"
        logger.warning(f"[RETRY] Tentativa {attempt}/{MAX_SEND_RETRIES} falhou (conexão): {erro_msg}")
        if attempt < MAX_SEND_RETRIES:
            time.sleep(SEND_RETRY_DELAY * attempt)  # backoff
        else:
            return {
                "sucesso": False, "protocolo": None, "nr_recibo": None,
                "codigo_resposta": None,
                "descricao": f"Conexão falhou após {MAX_SEND_RETRIES} tentativas: {erro_msg}",
                "eventos": [],
            }

    if not resultado.get("sucesso"):
        return {
            "sucesso": False,
            "protocolo": resultado.get("protocolo"),
            "nr_recibo": None,
            "codigo_resposta": resultado.get("codigo_resposta"),
            "descricao": resultado.get("descricao") or resultado.get("erro"),
            "eventos": [],
        }

    protocolo = resultado.get("protocolo")
    if not protocolo:
        return {
            "sucesso": False, "protocolo": None, "nr_recibo": None,
            "codigo_resposta": None, "descricao": "Sem protocolo no retorno",
            "eventos": [],
        }

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
    nr_recibo = None
    consulta = None

    for attempt in range(MAX_POLL_RETRIES):
        time.sleep(POLL_DELAY_SECS)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

        # Retry on connection errors during polling
        if _is_connection_error(consulta):
            logger.warning(f"[POLL-RETRY] Tentativa {attempt+1}/{MAX_POLL_RETRIES} polling falhou (conexão)")
            continue

        eventos = consulta.get("eventos", [])

        if consulta.get("sucesso") and eventos:
            for ev in eventos:
                if ev.get("nr_recibo"):
                    nr_recibo = ev["nr_recibo"]
                    break
            if nr_recibo:
                break
            # Check for processing errors
            for ev in eventos:
                if ev.get("codigo_resposta") and ev["codigo_resposta"] not in ("201", "202"):
                    desc = ev.get("descricao", "")
                    ocorrencias = ev.get("ocorrencias", [])
                    if ocorrencias:
                        desc += " | " + " | ".join(
                            f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                        )
                    return {
                        "sucesso": False, "protocolo": protocolo, "nr_recibo": None,
                        "codigo_resposta": ev["codigo_resposta"], "descricao": desc,
                        "eventos": eventos,
                    }
        elif consulta.get("codigo_resposta") == "101":
            continue
        elif consulta.get("sucesso") is False:
            break

    return {
        "sucesso": nr_recibo is not None,
        "protocolo": protocolo,
        "nr_recibo": nr_recibo,
        "codigo_resposta": consulta.get("codigo_resposta") if consulta else None,
        "descricao": consulta.get("descricao") if consulta else None,
        "eventos": consulta.get("eventos", []) if consulta else [],
    }


# ── Pipeline Recovery ─────────────────────────────────────────────

@router.post("/recuperar")
async def executar_recuperacao(req: RecoveryRequest):
    """
    Executa o pipeline de recuperação multi-período.

    ⚠ É PRODUÇÃO. Operação longa (~3-5 min). Cada step tem polling.
    """
    if not req.cpf or len(req.cpf) != 11 or not req.cpf.isdigit():
        raise HTTPException(400, "CPF deve ter 11 dígitos numéricos")

    cert = _load_cert()
    if not cert:
        raise HTTPException(400, "Nenhum certificado A1 ativo")

    with open(cert["arquivo_path"], "rb") as f:
        pfx_data = f.read()
    senha = cert["senha"]
    cnpj = cert["cnpj"]
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    is_producao = req.ambiente == "1"
    tp_amb = req.ambiente

    steps: list[RecoveryStepResult] = []
    steps_ok = 0

    def _make_step(step_num, evento, per_apur, result):
        return RecoveryStepResult(
            step=step_num, evento=evento, per_apur=per_apur,
            status="ok" if result["sucesso"] else "erro",
            protocolo=result.get("protocolo"),
            nr_recibo=result.get("nr_recibo"),
            codigo_resposta=result.get("codigo_resposta"),
            descricao=result.get("descricao"),
        )

    def _err_response(msg):
        return RecoveryResponse(
            cpf=req.cpf, status="erro",
            total_steps=len(steps), steps_ok=steps_ok, steps=steps,
        )

    # ══════════════════════════════════════════════════════════════
    # STEP 1: S-1298 — Reabrir período bloqueador (Jan/2025)
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1298XMLGenerator.gerar(empregador, req.per_apur_bloqueador, req.ind_apuracao, tp_amb=tp_amb)
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        # Período já aberto é sucesso (código 202 = já processado ou erro indicando "já aberto")
        already_open = (
            not result["sucesso"]
            and result.get("descricao")
            and ("já se encontra" in result["descricao"].lower()
                 or "já está abert" in result["descricao"].lower()
                 or "[715]" in result["descricao"]
                 or "período já" in result["descricao"].lower())
        )
        if already_open:
            result["sucesso"] = True
            result["descricao"] = f"[JÁ ABERTO] {result['descricao']}"
            logger.info(f"Step 1: Período {req.per_apur_bloqueador} já estava aberto, continuando...")
        step = _make_step(1, "S-1298", req.per_apur_bloqueador, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1298 reabertura bloqueador falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=1, evento="S-1298", per_apur=req.per_apur_bloqueador, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 2: S-1298 — Reabrir período alvo (Dez/2024)
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1298XMLGenerator.gerar(empregador, req.per_apur_alvo, req.ind_apuracao, tp_amb=tp_amb)
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        # Período já aberto é sucesso
        already_open = (
            not result["sucesso"]
            and result.get("descricao")
            and ("já se encontra" in result["descricao"].lower()
                 or "já está abert" in result["descricao"].lower()
                 or "[715]" in result["descricao"]
                 or "período já" in result["descricao"].lower())
        )
        if already_open:
            result["sucesso"] = True
            result["descricao"] = f"[JÁ ABERTO] {result['descricao']}"
            logger.info(f"Step 2: Período {req.per_apur_alvo} já estava aberto, continuando...")
        step = _make_step(2, "S-1298", req.per_apur_alvo, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1298 reabertura alvo falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=2, evento="S-1298", per_apur=req.per_apur_alvo, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 3: S-3000 — Excluir S-1210 Jan/2025 (libera dmDevs)
    #   Remove o evento inteiro → dmDevs não são mais referenciados
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S3000XMLGenerator.gerar(
            empregador=empregador,
            tp_evento="S-1210",
            nr_rec_evt=req.s1210_bloq_nr_recibo,
            cpf_trab=req.cpf,
            per_apur=req.per_apur_bloqueador,
            ind_apuracao=req.ind_apuracao,
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "2", is_producao)
        step = _make_step(3, "S-3000 excluir S-1210", req.per_apur_bloqueador, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-3000 exclusão S-1210 bloqueador falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=3, evento="S-3000 excluir S-1210", per_apur=req.per_apur_bloqueador, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 4: S-1200 retif — Período alvo (Dez/2024)
    #   Agora desbloqueado! Retifica com dados idênticos → S-5001 recalcula
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1200XMLGenerator.gerar(
            empregador=empregador,
            trabalhador={"cpfTrab": req.cpf},
            dm_devs=req.s1200_dm_devs,
            per_apur=req.per_apur_alvo,
            ind_retif="2",
            nr_recibo=req.s1200_nr_recibo,
            ind_apuracao=req.ind_apuracao,
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        step = _make_step(4, "S-1200 retif", req.per_apur_alvo, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1200 retif alvo falhou — PRINCIPAL BLOQUEIO!")
    except Exception as e:
        steps.append(RecoveryStepResult(step=4, evento="S-1200 retif", per_apur=req.per_apur_alvo, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 5: S-1210 retif — Período alvo (Dez/2024)
    #   Retifica para forçar recálculo S-5002
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1210XMLGenerator.gerar(
            empregador=empregador,
            beneficiario={"cpfBenef": req.cpf},
            info_pgtos=req.s1210_alvo_info_pgtos,
            per_apur=req.per_apur_alvo,
            ind_retif="2",
            nr_recibo=req.s1210_alvo_nr_recibo,
            info_ir_complem=req.s1210_alvo_info_ir_complem,
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        step = _make_step(5, "S-1210 retif", req.per_apur_alvo, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1210 retif alvo falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=5, evento="S-1210 retif", per_apur=req.per_apur_alvo, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 6: S-1210 incluir — Re-incluir S-1210 Jan/2025
    #   O evento foi excluído no Step 3, agora re-envia como original
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1210XMLGenerator.gerar(
            empregador=empregador,
            beneficiario={"cpfBenef": req.cpf},
            info_pgtos=req.s1210_bloq_info_pgtos,
            per_apur=req.per_apur_bloqueador,
            ind_retif="1",  # inclusão original (evento foi excluído)
            tp_amb=tp_amb,
        )
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        step = _make_step(6, "S-1210 incluir", req.per_apur_bloqueador, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1210 re-inclusão bloqueador falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=6, evento="S-1210 incluir", per_apur=req.per_apur_bloqueador, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 7: S-1299 — Fechar período alvo (Dez/2024)
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1299XMLGenerator.gerar(empregador, req.per_apur_alvo, req.ind_apuracao, tp_amb=tp_amb)
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        step = _make_step(7, "S-1299", req.per_apur_alvo, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1299 fechamento alvo falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=7, evento="S-1299", per_apur=req.per_apur_alvo, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # STEP 8: S-1299 — Fechar período bloqueador (Jan/2025)
    # ══════════════════════════════════════════════════════════════
    try:
        xml = S1299XMLGenerator.gerar(empregador, req.per_apur_bloqueador, req.ind_apuracao, tp_amb=tp_amb)
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)
        step = _make_step(8, "S-1299", req.per_apur_bloqueador, result)
        steps.append(step)
        if result["sucesso"]:
            steps_ok += 1
        else:
            return _err_response("S-1299 fechamento bloqueador falhou")
    except Exception as e:
        steps.append(RecoveryStepResult(step=8, evento="S-1299", per_apur=req.per_apur_bloqueador, status="erro", descricao=str(e)))
        return _err_response(str(e))

    # ══════════════════════════════════════════════════════════════
    # RESULTADO FINAL
    # ══════════════════════════════════════════════════════════════
    return RecoveryResponse(
        cpf=req.cpf, status="completo",
        total_steps=len(steps), steps_ok=steps_ok, steps=steps,
    )


# ── Endpoint Completo: PRÉ → Recovery → PÓS → Comparação ────────

class CompletoResponse(BaseModel):
    fase: str              # "pre", "recovery", "pos", "comparacao", "completo"
    pre_snapshot_id: int | None = None
    recovery: RecoveryResponse | None = None
    pos_snapshot_id: int | None = None
    comparacao: dict | None = None
    erro: str | None = None


@router.post("/executar-completo")
async def executar_completo(req: RecoveryRequest):
    """
    Executa o fluxo completo em sequência:
    1. Captura snapshot PRÉ
    2. Executa pipeline de recuperação (7 steps com retry)
    3. Captura snapshot PÓS
    4. Gera comparação automática

    Retorna tudo junto para evidência.
    """
    from esocial.pipeline_audit_routes import capturar_snapshot, comparar_snapshots, CapturaSnapshotRequest

    resultado = CompletoResponse(fase="pre")

    # ── FASE 1: Snapshot PRÉ ──
    try:
        pre_req = CapturaSnapshotRequest(
            cpf=req.cpf,
            per_apur=req.per_apur_alvo,
            tipo="pre_pipeline",
            descricao="Snapshot PRÉ — capturado automaticamente pelo executar-completo",
            rubrica_ids=["566", "596"],
        )
        pre_result = await capturar_snapshot(pre_req)
        resultado.pre_snapshot_id = pre_result.get("snapshot_id")
        logger.info(f"[COMPLETO] Snapshot PRÉ capturado: #{resultado.pre_snapshot_id}")
    except Exception as e:
        logger.error(f"[COMPLETO] Erro no snapshot PRÉ: {e}")
        resultado.erro = f"Erro no snapshot PRÉ: {e}"
        return resultado

    # ── FASE 2: Recovery Pipeline ──
    resultado.fase = "recovery"
    try:
        recovery_result = await executar_recuperacao(req)
        resultado.recovery = recovery_result
        if recovery_result.status != "completo":
            resultado.erro = f"Recovery parou: {recovery_result.status} ({recovery_result.steps_ok}/{recovery_result.total_steps} OK)"
            return resultado
        logger.info(f"[COMPLETO] Recovery completo: {recovery_result.steps_ok}/{recovery_result.total_steps} OK")
    except Exception as e:
        logger.error(f"[COMPLETO] Erro no recovery: {e}")
        resultado.erro = f"Erro no recovery: {e}"
        return resultado

    # ── FASE 3: Snapshot PÓS ──
    resultado.fase = "pos"
    try:
        pos_req = CapturaSnapshotRequest(
            cpf=req.cpf,
            per_apur=req.per_apur_alvo,
            tipo="pos_pipeline",
            descricao="Snapshot PÓS — capturado automaticamente pelo executar-completo",
            rubrica_ids=["566", "596"],
        )
        pos_result = await capturar_snapshot(pos_req)
        resultado.pos_snapshot_id = pos_result.get("snapshot_id")
        logger.info(f"[COMPLETO] Snapshot PÓS capturado: #{resultado.pos_snapshot_id}")
    except Exception as e:
        logger.error(f"[COMPLETO] Erro no snapshot PÓS: {e}")
        resultado.erro = f"Erro no snapshot PÓS (recovery JÁ executou): {e}"
        return resultado

    # ── FASE 4: Comparação ──
    resultado.fase = "comparacao"
    try:
        comp_result = await comparar_snapshots(req.cpf)
        resultado.comparacao = comp_result.get("comparacao")
        logger.info(f"[COMPLETO] Comparação gerada com sucesso")
    except Exception as e:
        logger.warning(f"[COMPLETO] Erro na comparação (não crítico): {e}")

    resultado.fase = "completo"
    return resultado


# ── Streaming: Envio com progresso step-a-step ────────────────────

async def _step_stream(step_num, evento, per_apur, xml_bytes, pfx_data, senha, empregador, grupo, is_producao):
    """Async generator: yields progress dicts for a single recovery step."""
    yield {"tipo": "step_inicio", "step": step_num, "evento": evento, "per_apur": per_apur}

    try:
        signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
        soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=grupo)
        url = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
    except Exception as e:
        yield {"tipo": "step_fim", "step": step_num, "evento": evento, "per_apur": per_apur,
               "status": "erro", "resultado": {"sucesso": False, "descricao": f"Erro ao assinar: {e}"}}
        return

    # Send with retry
    # NOTE: enviar_lote catches ALL exceptions internally — never raises.
    # Retry must check the result dict for connection errors.
    resultado = None
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        yield {"tipo": "step_enviando", "step": step_num, "tentativa": attempt}
        resultado = await asyncio.to_thread(ESocialClient.enviar_lote, soap, pfx_data, senha, url=url)
        if resultado.get("sucesso") or not _is_connection_error(resultado):
            break  # success or non-connection error
        erro_msg = resultado.get("erro") or resultado.get("descricao") or "?"
        yield {"tipo": "step_retry", "step": step_num, "tentativa": attempt,
               "max": MAX_SEND_RETRIES, "erro": erro_msg}
        if attempt < MAX_SEND_RETRIES:
            await asyncio.sleep(SEND_RETRY_DELAY * attempt)
        else:
            yield {"tipo": "step_fim", "step": step_num, "evento": evento, "per_apur": per_apur,
                   "status": "erro", "resultado": {"sucesso": False,
                   "descricao": f"Conexão falhou após {MAX_SEND_RETRIES} tentativas: {erro_msg}"}}
            return

    if not resultado.get("sucesso"):
        yield {"tipo": "step_fim", "step": step_num, "evento": evento, "per_apur": per_apur,
               "status": "erro", "resultado": {
                   "sucesso": False, "protocolo": resultado.get("protocolo"),
                   "codigo_resposta": resultado.get("codigo_resposta"),
                   "descricao": resultado.get("descricao") or resultado.get("erro"),
               }}
        return

    protocolo = resultado.get("protocolo")
    if not protocolo:
        yield {"tipo": "step_fim", "step": step_num, "evento": evento, "per_apur": per_apur,
               "status": "erro", "resultado": {"sucesso": False, "descricao": "Sem protocolo no retorno"}}
        return

    yield {"tipo": "step_protocolo", "step": step_num, "protocolo": protocolo}

    # Poll for result
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
    nr_recibo = None
    consulta = None

    for poll_attempt in range(MAX_POLL_RETRIES):
        yield {"tipo": "step_polling", "step": step_num, "tentativa": poll_attempt + 1, "max": MAX_POLL_RETRIES}
        await asyncio.sleep(POLL_DELAY_SECS)
        try:
            consulta = await asyncio.to_thread(
                ESocialClient.consultar_lote, protocolo, pfx_data, senha, url=url_consulta
            )
        except Exception as e:
            yield {"tipo": "step_poll_erro", "step": step_num, "tentativa": poll_attempt + 1, "erro": str(e)}
            continue

        # Retry on connection errors during polling
        if _is_connection_error(consulta):
            yield {"tipo": "step_poll_erro", "step": step_num, "tentativa": poll_attempt + 1,
                   "erro": consulta.get("erro") or "conexão"}
            continue

        eventos = consulta.get("eventos", [])
        if consulta.get("sucesso") and eventos:
            for ev in eventos:
                if ev.get("nr_recibo"):
                    nr_recibo = ev["nr_recibo"]
                    break
            if nr_recibo:
                break
            for ev in eventos:
                if ev.get("codigo_resposta") and ev["codigo_resposta"] not in ("201", "202"):
                    desc = ev.get("descricao", "")
                    ocorrencias = ev.get("ocorrencias", [])
                    if ocorrencias:
                        desc += " | " + " | ".join(
                            f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                        )
                    yield {"tipo": "step_fim", "step": step_num, "evento": evento, "per_apur": per_apur,
                           "status": "erro", "resultado": {
                               "sucesso": False, "protocolo": protocolo,
                               "codigo_resposta": ev["codigo_resposta"], "descricao": desc,
                           }}
                    return
        elif consulta.get("codigo_resposta") == "101":
            continue
        elif consulta.get("sucesso") is False:
            break

    result = {
        "sucesso": nr_recibo is not None,
        "protocolo": protocolo,
        "nr_recibo": nr_recibo,
        "codigo_resposta": consulta.get("codigo_resposta") if consulta else None,
        "descricao": consulta.get("descricao") if consulta else None,
    }

    yield {"tipo": "step_fim", "step": step_num, "evento": evento, "per_apur": per_apur,
           "status": "ok" if result["sucesso"] else "timeout", "resultado": result}


# ── Endpoint Streaming: PRÉ → Recovery → PÓS com progresso ──────

@router.post("/executar-completo-stream")
async def executar_completo_stream(req: RecoveryRequest):
    """
    SSE streaming: executa o fluxo completo com progresso em tempo real.
    Cada evento é enviado via Server-Sent Events conforme avança.
    """
    if not req.cpf or len(req.cpf) != 11 or not req.cpf.isdigit():
        raise HTTPException(400, "CPF deve ter 11 dígitos numéricos")

    async def generate():
        def sse(data):
            return f"data: {json.dumps(data, default=str)}\n\n"

        yield sse({"tipo": "inicio", "msg": "Preparando fluxo completo..."})

        cert = _load_cert()
        if not cert:
            yield sse({"tipo": "erro", "msg": "Nenhum certificado A1 ativo"})
            return

        with open(cert["arquivo_path"], "rb") as f:
            pfx_data = f.read()
        senha = cert["senha"]
        cnpj = cert["cnpj"]
        empregador = {"tpInsc": 1, "nrInsc": cnpj}
        is_producao = req.ambiente == "1"
        tp_amb = req.ambiente

        # ── FASE 1: Snapshot PRÉ ──
        yield sse({"tipo": "fase", "fase": "pre", "msg": "Capturando snapshot PRÉ..."})
        try:
            from esocial.pipeline_audit_routes import capturar_snapshot, comparar_snapshots, CapturaSnapshotRequest
            pre_req = CapturaSnapshotRequest(
                cpf=req.cpf, per_apur=req.per_apur_alvo, tipo="pre_pipeline",
                descricao="PRÉ — captura automática (stream)", rubrica_ids=["566", "596"],
            )
            pre_result = await capturar_snapshot(pre_req)
            pre_id = pre_result.get("snapshot_id")
            yield sse({"tipo": "fase_ok", "fase": "pre", "snapshot_id": pre_id,
                       "msg": f"Snapshot PRÉ capturado (#{pre_id})"})
        except Exception as e:
            yield sse({"tipo": "erro", "msg": f"Erro no snapshot PRÉ: {e}"})
            return

        # ── FASE 2: Recovery (8 steps) ──
        yield sse({"tipo": "fase", "fase": "recovery", "msg": "Iniciando pipeline recovery (8 steps)..."})

        steps_ok = 0
        s1210_bloq_recibo = req.s1210_bloq_nr_recibo
        recovery_failed = False

        step_definitions = [
            (1, "S-1298", req.per_apur_bloqueador, "reabertura"),
            (2, "S-1298", req.per_apur_alvo, "reabertura"),
            (3, "S-3000 excluir S-1210", req.per_apur_bloqueador, "excluir_bloq"),
            (4, "S-1200 retif", req.per_apur_alvo, "retif_alvo_1200"),
            (5, "S-1210 retif", req.per_apur_alvo, "retif_alvo_1210"),
            (6, "S-1210 incluir", req.per_apur_bloqueador, "incluir_bloq"),
            (7, "S-1299", req.per_apur_alvo, "fechamento"),
            (8, "S-1299", req.per_apur_bloqueador, "fechamento"),
        ]

        for (snum, sevento, sper, stipo) in step_definitions:
            # Generate XML
            try:
                if stipo == "reabertura":
                    xml = S1298XMLGenerator.gerar(empregador, sper, req.ind_apuracao, tp_amb=tp_amb)
                elif stipo == "excluir_bloq":
                    xml = S3000XMLGenerator.gerar(
                        empregador=empregador, tp_evento="S-1210",
                        nr_rec_evt=s1210_bloq_recibo, cpf_trab=req.cpf,
                        per_apur=sper, ind_apuracao=req.ind_apuracao, tp_amb=tp_amb,
                    )
                elif stipo == "retif_alvo_1200":
                    xml = S1200XMLGenerator.gerar(
                        empregador=empregador, trabalhador={"cpfTrab": req.cpf},
                        dm_devs=req.s1200_dm_devs, per_apur=sper,
                        ind_retif="2", nr_recibo=req.s1200_nr_recibo,
                        ind_apuracao=req.ind_apuracao, tp_amb=tp_amb,
                    )
                elif stipo == "retif_alvo_1210":
                    xml = S1210XMLGenerator.gerar(
                        empregador=empregador, beneficiario={"cpfBenef": req.cpf},
                        info_pgtos=req.s1210_alvo_info_pgtos, per_apur=sper,
                        ind_retif="2", nr_recibo=req.s1210_alvo_nr_recibo,
                        info_ir_complem=req.s1210_alvo_info_ir_complem, tp_amb=tp_amb,
                    )
                elif stipo == "incluir_bloq":
                    xml = S1210XMLGenerator.gerar(
                        empregador=empregador, beneficiario={"cpfBenef": req.cpf},
                        info_pgtos=req.s1210_bloq_info_pgtos, per_apur=sper,
                        ind_retif="1", tp_amb=tp_amb,  # inclusão original
                    )
                elif stipo == "fechamento":
                    xml = S1299XMLGenerator.gerar(empregador, sper, req.ind_apuracao, tp_amb=tp_amb)
            except Exception as e:
                yield sse({"tipo": "step_fim", "step": snum, "evento": sevento, "per_apur": sper,
                           "status": "erro", "resultado": {"sucesso": False, "descricao": f"Erro ao gerar XML: {e}"}})
                recovery_failed = True
                break

            # Execute step with streaming progress
            last_result = None
            step_grupo = "2" if stipo == "excluir_bloq" else "3"
            async for event in _step_stream(snum, sevento, sper, xml, pfx_data, senha, empregador, step_grupo, is_producao):
                yield sse(event)
                if event["tipo"] == "step_fim":
                    last_result = event.get("resultado", {})

            # Handle "already open" for S-1298 steps
            if stipo == "reabertura" and last_result and not last_result.get("sucesso"):
                desc = (last_result.get("descricao") or "")
                desc_lower = desc.lower()
                if "já se encontra" in desc_lower or "já está abert" in desc_lower or "[715]" in desc or "período já" in desc_lower:
                    last_result["sucesso"] = True
                    yield sse({"tipo": "step_override", "step": snum, "status": "ok",
                              "msg": f"Período {sper} já estava aberto — continuando"})

            if last_result and last_result.get("sucesso"):
                steps_ok += 1
            else:
                yield sse({"tipo": "recovery_erro", "step": snum,
                           "msg": f"Recovery parou no step {snum} ({sevento})", "steps_ok": steps_ok})
                recovery_failed = True
                break

        if recovery_failed:
            yield sse({"tipo": "fase_erro", "fase": "recovery", "steps_ok": steps_ok,
                       "msg": f"Recovery incompleto ({steps_ok}/8)"})
        else:
            yield sse({"tipo": "fase_ok", "fase": "recovery", "steps_ok": steps_ok,
                       "msg": f"Recovery completo ({steps_ok}/8 OK)"})

        # ── FASE 3: Snapshot PÓS ──
        if not recovery_failed:
            yield sse({"tipo": "fase", "fase": "pos", "msg": "Capturando snapshot PÓS..."})
            try:
                pos_req = CapturaSnapshotRequest(
                    cpf=req.cpf, per_apur=req.per_apur_alvo, tipo="pos_pipeline",
                    descricao="PÓS — captura automática (stream)", rubrica_ids=["566", "596"],
                )
                pos_result = await capturar_snapshot(pos_req)
                pos_id = pos_result.get("snapshot_id")
                yield sse({"tipo": "fase_ok", "fase": "pos", "snapshot_id": pos_id,
                           "msg": f"Snapshot PÓS capturado (#{pos_id})"})
            except Exception as e:
                yield sse({"tipo": "fase_erro", "fase": "pos", "msg": f"Erro no snapshot PÓS: {e}"})

            # ── FASE 4: Comparação ──
            yield sse({"tipo": "fase", "fase": "comparacao", "msg": "Gerando comparação..."})
            try:
                comp_result = await comparar_snapshots(req.cpf)
                comparacao_data = comp_result.get("comparacao")
                yield sse({"tipo": "fase_ok", "fase": "comparacao", "comparacao": comparacao_data,
                           "msg": "Comparação gerada com sucesso"})
            except Exception as e:
                yield sse({"tipo": "fase_erro", "fase": "comparacao", "msg": f"Erro na comparação: {e}"})

        # ── FIM ──
        yield sse({"tipo": "completo", "steps_ok": steps_ok, "recovery_ok": not recovery_failed,
                   "msg": f"Fluxo {'completo' if not recovery_failed else 'parcial'} — {steps_ok}/8 steps OK"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
