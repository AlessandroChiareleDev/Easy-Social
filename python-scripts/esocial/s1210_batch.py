"""
S-1210 Missão APPA — Motor de processamento em LOTE.

Pensado pro frontend controlar via play/pause/resume/stop e acompanhar ao vivo.

Fluxo por CPF:
1) Extrai S-1210 do ZIP (recibo ORIGINAL, perApur, pgtos, IRCR)
2) Busca no Supabase (pipeline_cpf_results) a cadeia de retificações desse CPF
   e caminha até o recibo ATIVO mais recente (matching por sorted(ideDmDev))
3) Envia retif em PRODUÇÃO com o recibo ativo
4) Pollar consulta até ter recibo_novo ou erro
5) Persiste em pipeline_cpf_results (run_id do batch atual)

O estado fica em memória global (_STATE) + log circular (_LOG) acessível via
endpoints REST com polling. Thread única pra não ter concorrência no eSocial.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Optional

log = logging.getLogger("s1210-batch")


# ── Estado global do batch ──────────────────────────────────────────
# Status possíveis: "idle" | "running" | "paused" | "stopping" | "finished" | "error"
_STATE_LOCK = threading.Lock()
_STATE: dict[str, Any] = {
    "status": "idle",
    "run_id": None,
    "mes": None,
    "lote": None,
    "total": 0,
    "processados": 0,
    "sucessos": 0,
    "erros": 0,
    "pulados_sem_s1210": 0,
    "started_at": None,
    "updated_at": None,
    "cpf_atual": None,
    "indice_atual": None,
    "ultimo_resultado": None,
    "erros_recentes": [],   # últimos 50
    "finalizado_em": None,
    "motivo_parada": None,
}

# Log circular (visível no terminal do front)
_LOG: deque[dict] = deque(maxlen=500)
_LOG_SEQ = 0
_LOG_LOCK = threading.Lock()

# Controles do worker
_PAUSE_EVENT = threading.Event()   # set = PODE rodar; clear = PAUSADO
_PAUSE_EVENT.set()
_STOP_EVENT = threading.Event()    # set = STOP solicitado
_WORKER_THREAD: Optional[threading.Thread] = None


def _emit_log(msg: str, level: str = "info", cpf: Optional[str] = None) -> None:
    global _LOG_SEQ
    with _LOG_LOCK:
        _LOG_SEQ += 1
        entry = {
            "seq": _LOG_SEQ,
            "ts": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "msg": msg,
        }
        if cpf:
            entry["cpf"] = cpf
        _LOG.append(entry)
    # também emite no log do servidor
    lvl_map = {"info": log.info, "ok": log.info, "warn": log.warning, "err": log.error}
    lvl_map.get(level, log.info)(f"[batch] {msg}")


def _update_state(**kwargs) -> None:
    with _STATE_LOCK:
        _STATE.update(kwargs)
        _STATE["updated_at"] = datetime.now().isoformat()


def _snapshot_state() -> dict:
    with _STATE_LOCK:
        return dict(_STATE)


def _logs_since(seq: int, limit: int = 200) -> list[dict]:
    with _LOG_LOCK:
        # retorna até 'limit' entradas com seq > seq informado
        out = [e for e in _LOG if e["seq"] > seq]
        return out[-limit:]


# ── Auto recibo: busca cadeia no Supabase ───────────────────────────

def _buscar_recibo_ativo(cpf: str, s1210: dict) -> tuple[str, str, int]:
    """
    Dado S-1210 extraído do ZIP, acha o recibo ATIVO percorrendo cadeia
    de retificações em pipeline_cpf_results.

    Retorna: (recibo_ativo, fonte, candidatos)
      fonte: "zip" (nenhuma cadeia encontrada, usa o do ZIP)
             "cadeia" (achou cadeia, retornou último recibo novo)
    """
    import sys as _sys
    import os as _os
    base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if base not in _sys.path:
        _sys.path.insert(0, base)
    from db_config import DB_CONFIG
    import psycopg2
    import psycopg2.extras

    recibo_zip = s1210["nr_recibo"]
    zip_ides = sorted(p["ideDmDev"] for p in s1210["info_pgtos"])

    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        _emit_log(f"DB erro: {e}", "warn", cpf=cpf)
        return recibo_zip, "zip", 0

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT nr_recibo_original, nr_recibo_novo, pagamentos, processed_at
              FROM pipeline_cpf_results
             WHERE cpf = %s AND status = 'ok'
             ORDER BY processed_at DESC
            """,
            (cpf,),
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    candidatos = []
    for row in rows:
        pag = row["pagamentos"]
        if isinstance(pag, str):
            try:
                pag = json.loads(pag)
            except Exception:
                continue
        if not pag:
            continue
        row_ides = sorted(p.get("ideDmDev", "") for p in pag)
        if row_ides == zip_ides:
            candidatos.append(row)

    if not candidatos:
        return recibo_zip, "zip", 0

    mapa = {c["nr_recibo_original"]: c["nr_recibo_novo"] for c in candidatos}
    atual = recibo_zip
    visitado: set[str] = set()
    while atual in mapa and atual not in visitado:
        visitado.add(atual)
        atual = mapa[atual]

    if atual == recibo_zip:
        return recibo_zip, "zip", len(candidatos)
    return atual, "cadeia", len(candidatos)


# ── Persistência em pipeline_cpf_results ────────────────────────────

def _persistir_resultado(mes: str, lote_num: int, resultado: dict) -> None:
    """Salva resultado via helper central (pipeline_runs + pipeline_cpf_results)."""
    from esocial.s1210_missao_routes import _persistir_cpf_result
    try:
        _persistir_cpf_result(mes, lote_num, resultado)
    except Exception as e:
        _emit_log(f"⚠️  falha persist: {e}", "warn", cpf=resultado.get("cpf"))


# ── Worker principal ────────────────────────────────────────────────

def _processar_um_cpf(mes: str, lote_key: str, cpf: str) -> dict:
    """
    Executa o pipeline completo para 1 CPF:
      ZIP → banco → envio PROD → poll → retorno.
    Reaproveita helpers do módulo de rotas.
    """
    # imports tardios pra evitar ciclo de import
    from esocial.s1210_missao_routes import (
        _buscar_s1210_unico, _load_cert_ativo,
    )
    from esocial.xml_s1210 import S1210XMLGenerator
    from esocial.xml_signer import S1010XMLSigner as XMLSigner
    from esocial.soap_builder import SOAPEnvelopeBuilder
    from esocial.esocial_client import ESocialClient

    # 1) extrai do ZIP
    s1210 = _buscar_s1210_unico(mes, cpf)
    if not s1210:
        return {
            "sucesso": False,
            "etapa": "buscar_recibo",
            "cpf": cpf,
            "mes": mes,
            "lote": lote_key,
            "erro": f"Nenhum S-1210 no ZIP",
            "pulado": True,
        }

    recibo_zip = s1210["nr_recibo"]

    # 2) descobre recibo ativo
    recibo_ativo, fonte_recibo, n_cand = _buscar_recibo_ativo(cpf, s1210)
    if fonte_recibo == "cadeia":
        _emit_log(
            f"🔗 cadeia: {recibo_zip} → {recibo_ativo} ({n_cand} rets)",
            "info", cpf=cpf,
        )

    # 3) carrega cert
    cnpj, pfx_data, senha = _load_cert_ativo()
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    info_ir_complem = None
    if s1210["info_ir_cr"]:
        info_ir_complem = {"infoIRCR": s1210["info_ir_cr"]}

    # 4) monta XML retif
    try:
        xml_bytes = S1210XMLGenerator.gerar(
            empregador=empregador,
            beneficiario={"cpfBenef": cpf},
            info_pgtos=s1210["info_pgtos"],
            per_apur=s1210["per_apur"],
            ind_retif="2",
            nr_recibo=recibo_ativo,
            info_ir_complem=info_ir_complem,
            plan_saude=None,
            tp_amb="1",
        )
    except Exception as e:
        return {
            "sucesso": False, "etapa": "gerar_xml", "cpf": cpf,
            "mes": mes, "lote": lote_key, "erro": str(e),
            "nr_recibo_zip": recibo_zip, "nr_recibo_usado": recibo_ativo,
        }

    # 5) assina
    try:
        xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    except Exception as e:
        return {
            "sucesso": False, "etapa": "assinar_xml", "cpf": cpf,
            "mes": mes, "lote": lote_key, "erro": str(e),
            "nr_recibo_zip": recibo_zip, "nr_recibo_usado": recibo_ativo,
        }

    # 6) envia
    try:
        soap = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], empregador, empregador.copy(), grupo="3"
        )
        url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    except Exception as e:
        return {
            "sucesso": False, "etapa": "enviar_soap", "cpf": cpf,
            "mes": mes, "lote": lote_key, "erro": str(e),
            "nr_recibo_zip": recibo_zip, "nr_recibo_usado": recibo_ativo,
        }

    if not resultado.get("sucesso"):
        return {
            "sucesso": False, "etapa": "envio_rejeitado", "cpf": cpf,
            "mes": mes, "lote": lote_key,
            "codigo_resposta_envio": resultado.get("codigo_resposta"),
            "descricao_envio": resultado.get("descricao"),
            "erro": resultado.get("erro") or resultado.get("descricao"),
            "nr_recibo_zip": recibo_zip, "nr_recibo_usado": recibo_ativo,
        }

    protocolo = resultado.get("protocolo")

    # 7) polla consulta
    try:
        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
        for _attempt in range(15):
            # durante o poll, respeita pausa (não interrompe um envio em andamento)
            time.sleep(5)
            consulta = ESocialClient.consultar_lote(
                protocolo, pfx_data, senha, url=url_consulta
            )
            if consulta.get("eventos"):
                evt = consulta["eventos"][0]
                nr_novo = evt.get("nr_recibo")
                codigo = evt.get("codigo_resposta", "?")
                descricao = evt.get("descricao", "")
                ocorr = evt.get("ocorrencias", []) or []

                base = {
                    "cpf": cpf, "mes": mes, "lote": lote_key,
                    "protocolo": protocolo,
                    "nr_recibo_zip": recibo_zip,
                    "nr_recibo_usado": recibo_ativo,
                    "nr_recibo_original": recibo_ativo,
                    "codigo_resposta": codigo,
                    "descricao": descricao,
                    "ocorrencias": ocorr,
                    "pagamentos_snapshot": s1210["info_pgtos"],
                    "info_ir_snapshot": s1210["info_ir_cr"],
                }
                if nr_novo:
                    return {**base, "sucesso": True, "etapa": "processado", "nr_recibo_novo": nr_novo}
                return {
                    **base,
                    "sucesso": False,
                    "etapa": "processamento_rejeitado",
                    "erro": f"Código {codigo}: {descricao}",
                }
            if consulta.get("codigo_resposta") == "101":
                continue
    except Exception as e:
        return {
            "sucesso": False, "etapa": "consulta", "cpf": cpf,
            "mes": mes, "lote": lote_key, "protocolo": protocolo,
            "nr_recibo_zip": recibo_zip, "nr_recibo_usado": recibo_ativo,
            "erro": str(e),
        }

    return {
        "sucesso": False, "etapa": "timeout", "cpf": cpf,
        "mes": mes, "lote": lote_key, "protocolo": protocolo,
        "nr_recibo_zip": recibo_zip, "nr_recibo_usado": recibo_ativo,
        "erro": "Timeout após 15 tentativas",
    }


def _worker(mes: str, lote_key: str, cpfs: list[str], offset: int, limit: Optional[int]) -> None:
    """Thread worker — processa CPFs sequencialmente respeitando pause/stop."""
    run_id = _STATE["run_id"]
    lote_num = int(lote_key[0]) if lote_key and lote_key[0].isdigit() else 0
    end = len(cpfs) if limit is None else min(len(cpfs), offset + limit)
    _emit_log(f"▶️  início: {mes} / {lote_key} — {end - offset} CPFs (offset={offset})", "info")

    try:
        for i in range(offset, end):
            # check STOP
            if _STOP_EVENT.is_set():
                _emit_log("⏹️  stop solicitado — parando", "warn")
                _update_state(status="finished", motivo_parada="stop_manual",
                              finalizado_em=datetime.now().isoformat())
                return

            # check PAUSE — trava aqui até _PAUSE_EVENT voltar a ser set
            if not _PAUSE_EVENT.is_set():
                _emit_log("⏸️  pausado", "warn")
                _update_state(status="paused")
                _PAUSE_EVENT.wait()
                if _STOP_EVENT.is_set():
                    _emit_log("⏹️  stop após pausa", "warn")
                    _update_state(status="finished", motivo_parada="stop_manual",
                                  finalizado_em=datetime.now().isoformat())
                    return
                _emit_log("▶️  retomado", "info")
                _update_state(status="running")

            cpf = cpfs[i]
            _update_state(cpf_atual=cpf, indice_atual=i, status="running")
            _emit_log(f"→ [{i+1}/{end}] processando CPF {cpf}", "info", cpf=cpf)

            t0 = time.time()
            try:
                resultado = _processar_um_cpf(mes, lote_key, cpf)
            except Exception as e:
                resultado = {
                    "sucesso": False, "etapa": "excecao_inesperada",
                    "cpf": cpf, "mes": mes, "lote": lote_key,
                    "erro": f"{type(e).__name__}: {e}",
                }
            dt = time.time() - t0

            # atualiza contadores
            with _STATE_LOCK:
                _STATE["processados"] += 1
                _STATE["ultimo_resultado"] = resultado
                if resultado.get("pulado"):
                    _STATE["pulados_sem_s1210"] += 1
                    _emit_log(f"⏭️  {cpf} sem S-1210 no ZIP — pulado ({dt:.1f}s)", "warn", cpf=cpf)
                elif resultado.get("sucesso"):
                    _STATE["sucessos"] += 1
                    _emit_log(
                        f"✅ {cpf} OK — recibo novo {resultado.get('nr_recibo_novo')} ({dt:.1f}s)",
                        "ok", cpf=cpf,
                    )
                else:
                    _STATE["erros"] += 1
                    err = resultado.get("erro") or resultado.get("descricao") or "?"
                    etapa = resultado.get("etapa") or "?"
                    _emit_log(f"❌ {cpf} FAIL etapa={etapa} → {err} ({dt:.1f}s)", "err", cpf=cpf)
                    _STATE["erros_recentes"].append({
                        "cpf": cpf,
                        "etapa": etapa,
                        "erro": err,
                        "codigo": resultado.get("codigo_resposta"),
                        "ts": datetime.now().isoformat(),
                    })
                    _STATE["erros_recentes"] = _STATE["erros_recentes"][-50:]
                _STATE["updated_at"] = datetime.now().isoformat()

            # persiste no banco (best-effort)
            if not resultado.get("pulado"):
                try:
                    _persistir_resultado(mes, lote_num, resultado)
                except Exception as e:
                    _emit_log(f"⚠️  persist falhou: {e}", "warn", cpf=cpf)

        _emit_log(f"🏁 lote concluído: {_STATE['sucessos']} OK, {_STATE['erros']} erros, "
                  f"{_STATE['pulados_sem_s1210']} pulados", "ok")
        _update_state(
            status="finished",
            motivo_parada="concluido",
            finalizado_em=datetime.now().isoformat(),
            cpf_atual=None,
        )
    except Exception as e:
        _emit_log(f"💥 erro fatal no worker: {type(e).__name__}: {e}", "err")
        _update_state(status="error", motivo_parada=f"erro_fatal: {e}",
                      finalizado_em=datetime.now().isoformat())


# ── API pública (chamada pelas rotas FastAPI) ────────────────────────

def start_batch(mes: str, lote_key: str, cpfs: list[str], offset: int = 0,
                limit: Optional[int] = None) -> dict:
    """Inicia processamento. Erro se já tem um rodando."""
    global _WORKER_THREAD

    with _STATE_LOCK:
        if _STATE["status"] in ("running", "paused"):
            raise RuntimeError(f"Já existe um batch {_STATE['status']} — faça stop primeiro")

        run_id = str(uuid.uuid4())
        end = len(cpfs) if limit is None else min(len(cpfs), offset + limit)
        total = end - offset
        _STATE.update({
            "status": "running",
            "run_id": run_id,
            "mes": mes,
            "lote": lote_key,
            "total": total,
            "processados": 0,
            "sucessos": 0,
            "erros": 0,
            "pulados_sem_s1210": 0,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "cpf_atual": None,
            "indice_atual": offset,
            "ultimo_resultado": None,
            "erros_recentes": [],
            "finalizado_em": None,
            "motivo_parada": None,
        })

    # limpa events
    _PAUSE_EVENT.set()
    _STOP_EVENT.clear()
    # NÃO limpa _LOG: queremos histórico entre runs; mas marca boundary
    _emit_log(f"🆕 novo run_id={_STATE['run_id'][:8]}… mes={mes} lote={lote_key} total={total}", "info")

    _WORKER_THREAD = threading.Thread(
        target=_worker, args=(mes, lote_key, cpfs, offset, limit),
        name=f"s1210-batch-{mes}-{lote_key}",
        daemon=True,
    )
    _WORKER_THREAD.start()

    return _snapshot_state()


def pause_batch() -> dict:
    with _STATE_LOCK:
        if _STATE["status"] != "running":
            raise RuntimeError(f"status atual é {_STATE['status']}, não dá pra pausar")
    _PAUSE_EVENT.clear()
    _emit_log("⏸️  pausa solicitada", "warn")
    # status só vira "paused" quando o worker chegar no check
    return _snapshot_state()


def resume_batch() -> dict:
    with _STATE_LOCK:
        if _STATE["status"] not in ("paused", "running"):
            raise RuntimeError(f"status atual é {_STATE['status']}, não dá pra resumir")
    _PAUSE_EVENT.set()
    _emit_log("▶️  resume solicitado", "info")
    return _snapshot_state()


def stop_batch() -> dict:
    with _STATE_LOCK:
        if _STATE["status"] in ("idle", "finished", "error"):
            raise RuntimeError(f"status atual é {_STATE['status']}, não há o que parar")
    _STOP_EVENT.set()
    # destrava uma possível pausa pra thread sair
    _PAUSE_EVENT.set()
    _update_state(status="stopping")
    _emit_log("⏹️  stop solicitado — aguardando worker finalizar CPF atual", "warn")
    return _snapshot_state()


def get_status(since_seq: int = 0, log_limit: int = 200) -> dict:
    snap = _snapshot_state()
    snap["logs"] = _logs_since(since_seq, limit=log_limit)
    snap["ultimo_log_seq"] = _LOG_SEQ
    return snap
