"""
Pipeline V2 — Retificação S-1210 Janeiro 2025
═══════════════════════════════════════════════
Pipeline novo, otimizado e correto.

DIFERENÇAS do pipeline antigo:
  - planSaude CORRETO: multi-operadora, mapa V2 da tabela da Ana
  - SEM coleta de S-5002 (já temos snapshots do run 3)
  - Resume automático via DB + progress file
  - Workers paralelos (configurable)
  - Log completo em arquivo
  - Usa recibo MAIS RECENTE (retificação em cadeia)

REGRA DE planSaude (confirmada por Ana na call 3, 15/04/2026):
  - CPF COM operadora na tabela → S-1210 COM planSaude (cnpjOper+regANS+vlrSaudeTit)
  - CPF SEM operadora (sindicato) → S-1210 SEM planSaude
  - CPF sem saúde nenhuma → S-1210 SEM planSaude (remove planSaude errado)

Uso:
  python pipeline_v2_jan2025.py                      # roda tudo
  python pipeline_v2_jan2025.py --dry-run             # só conta, não envia
  python pipeline_v2_jan2025.py --no-close            # não fecha período
  python pipeline_v2_jan2025.py --workers 3           # configura workers
  python pipeline_v2_jan2025.py --only-errors         # só CPFs com erro do último run

Roda na VPS: python3 pipeline_v2_jan2025.py
"""

import sys
import os
import json
import time
import logging
import re
import argparse
import tempfile
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
import psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════

PER_APUR = "2025-01"
AMBIENTE = "1"        # PRODUÇÃO
IND_APURACAO = "1"    # mensal
GRUPO = "3"           # eventos periódicos

LOTE_SIZE = 50        # max eventos por lote SOAP
PARALLEL_WORKERS = 5  # lotes simultâneos
POLL_DELAY = 5        # seconds entre polls
MAX_POLL_RETRIES = 24 # 24 × 5s = 120s max wait
MAX_SEND_RETRIES = 3  # retries por lote (conexão)
SEND_RETRY_DELAY = 5  # seconds entre retries

DB_RETRY_MAX = 5
DB_RETRY_DELAY = 3

MAP_FILE = "plansaude_map_v2_jan2025.json"

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
    "name resolution", "temporary failure", "could not translate host name",
]

# Caminhos de progresso/log
PROGRESS_FILE = "/tmp/pipeline_v2_202501_progress.json"
RESULT_FILE = "/tmp/pipeline_v2_202501_result.json"
LOG_FILE = "/tmp/pipeline_v2_202501.log"

# PEM cache global (thread-safe, set uma vez antes dos threads)
_cert_pem_path = None
_key_pem_path = None
_pfx_data = None
_pfx_senha = None


# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )
    return logging.getLogger("pipeline_v2")


# ═══════════════════════════════════════════════════════════════
# DB HELPERS
# ═══════════════════════════════════════════════════════════════

def get_supabase_conn():
    for attempt in range(1, DB_RETRY_MAX + 1):
        try:
            return psycopg2.connect(
                **DB_CONFIG,
                keepalives=1, keepalives_idle=30,
                keepalives_interval=10, keepalives_count=3,
            )
        except psycopg2.OperationalError:
            if attempt < DB_RETRY_MAX:
                time.sleep(DB_RETRY_DELAY)
            else:
                raise


def load_cert():
    """Carrega certificado A1 do PostgreSQL local."""
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


# ═══════════════════════════════════════════════════════════════
# PEM CACHE (extrair uma vez, reusar em todas as threads)
# ═══════════════════════════════════════════════════════════════

def setup_pem_cache(pfx_data, senha):
    global _cert_pem_path, _key_pem_path, _pfx_data, _pfx_senha
    _pfx_data = pfx_data
    _pfx_senha = senha

    cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, senha)

    cert_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_v2_cert.pem")
    cert_file.write(cert_pem)
    cert_file.close()
    _cert_pem_path = cert_file.name

    key_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_v2_key.pem")
    key_file.write(key_pem)
    key_file.close()
    _key_pem_path = key_file.name


def cleanup_pem_cache():
    for p in (_cert_pem_path, _key_pem_path):
        if p:
            try:
                os.unlink(p)
            except OSError:
                pass


# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

def load_s1210_data(per_apur: str) -> list[dict]:
    """
    Carrega S-1210 ORIGINAIS do explorador_eventos.
    Retorna: [{cpf, nr_recibo, pagamentos[], infoIRCR[]}]
    Usa o recibo MAIS ANTIGO (menor id) para cada CPF — é o ativo no eSocial
    para os 161 CPFs que nunca tiveram retificação aceita.
    """
    conn = get_supabase_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT e.cpf, e.nr_recibo, e.dados_json, e.dt_processamento
                FROM explorador_eventos e
                WHERE e.tipo_evento = 'S-1210'
                  AND e.per_apur = %s
                  AND e.cpf IS NOT NULL
                  AND e.nr_recibo IS NOT NULL
                  AND COALESCE(e.dados_json->>'indRetif', '1') != '2'
                ORDER BY e.cpf, e.id ASC
            """, (per_apur,))
            rows = cur.fetchall()

        cpf_map = {}
        for row in rows:
            cpf = row["cpf"]
            if cpf in cpf_map:
                continue

            dados = row["dados_json"] if isinstance(row["dados_json"], dict) else json.loads(row["dados_json"] or "{}")

            pagamentos = dados.get("pagamentos", [])
            if not pagamentos and dados.get("dtPgto"):
                pagamentos = [{
                    "dtPgto": dados.get("dtPgto", ""),
                    "tpPgto": dados.get("tpPgto", "1"),
                    "perRef": dados.get("perRef", ""),
                    "ideDmDev": dados.get("ideDmDev", ""),
                    "vrLiq": dados.get("vrLiq", "0"),
                }]

            info_ir_cr = dados.get("infoIRCR", [])
            if not info_ir_cr and dados.get("tpCR"):
                info_ir_cr = [{"tpCR": dados["tpCR"]}]

            cpf_map[cpf] = {
                "cpf": cpf,
                "nr_recibo_original": row["nr_recibo"],
                "pagamentos": pagamentos,
                "infoIRCR": info_ir_cr,
            }
        return list(cpf_map.values())
    finally:
        conn.close()


def load_latest_recibos(per_apur: str) -> dict:
    """
    Busca o recibo MAIS RECENTE de cada CPF dos runs anteriores.
    Retorna: {cpf: nr_recibo_novo}
    Para retificar de novo, usamos o recibo da última retificação bem-sucedida.
    """
    conn = get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (r.cpf) r.cpf, r.nr_recibo_novo
                FROM pipeline_cpf_results r
                JOIN pipeline_runs p ON p.id = r.run_id
                WHERE p.per_apur = %s
                  AND r.status = 'ok'
                  AND r.nr_recibo_novo IS NOT NULL
                ORDER BY r.cpf, r.processed_at DESC NULLS LAST
            """, (per_apur,))
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()


def load_plansaude_map(map_file: str) -> dict:
    """
    Carrega mapa planSaude V2.
    Formato: {cpf_digits: [{cnpjOper, regANS, vlrSaudeTit}]}
    """
    if not os.path.exists(map_file):
        raise FileNotFoundError(f"Mapa planSaude não encontrado: {map_file}")
    with open(map_file) as f:
        return json.load(f)


def load_error_cpfs(per_apur: str) -> set:
    """Retorna CPFs cujo resultado MAIS RECENTE é 'erro'."""
    conn = get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sub.cpf FROM (
                    SELECT DISTINCT ON (r.cpf) r.cpf, r.status
                    FROM pipeline_cpf_results r
                    JOIN pipeline_runs p ON p.id = r.run_id
                    WHERE p.per_apur = %s
                    ORDER BY r.cpf, p.id DESC
                ) sub
                WHERE sub.status = 'erro'
            """, (per_apur,))
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# SOAP (thread-safe, usa PEM cache)
# ═══════════════════════════════════════════════════════════════

def soap_enviar(soap_envelope: str, url: str):
    """Envia SOAP usando PEM files pré-extraídos."""
    resp = requests.post(
        url=url,
        data=soap_envelope.encode("utf-8"),
        headers=SOAPEnvelopeBuilder.headers(),
        cert=(_cert_pem_path, _key_pem_path),
        verify=False,
        timeout=60,
    )
    resp.raise_for_status()
    return ESocialClient._parsear_resposta_envio(resp.text)


def soap_consultar(protocolo: str, url: str):
    """Consulta lote usando PEM files pré-extraídos."""
    soap_xml = SOAPEnvelopeBuilder.montar_consulta(protocolo)
    resp = requests.post(
        url=url,
        data=soap_xml.encode("utf-8"),
        headers=SOAPEnvelopeBuilder.headers_consulta(),
        cert=(_cert_pem_path, _key_pem_path),
        verify=False,
        timeout=60,
    )
    resp.raise_for_status()
    return ESocialClient._parsear_resposta_consulta(resp.text)


def enviar_evento_unico(xml_bytes: bytes, empregador: dict):
    """Assina, envelopa e envia um evento unitário (S-1298/S-1299)."""
    signed = XMLSigner.assinar(xml_bytes, _pfx_data, _pfx_senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)

    # Enviar
    resultado = None
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        try:
            resultado = soap_enviar(soap, url_envio)
            if resultado.get("sucesso"):
                break
            erro = (resultado.get("descricao") or "").lower()
            if not any(kw in erro for kw in CONNECTION_ERRORS):
                break
        except Exception as e:
            resultado = {"sucesso": False, "descricao": str(e), "protocolo": None}
        if attempt < MAX_SEND_RETRIES:
            time.sleep(SEND_RETRY_DELAY * attempt)

    if not resultado or not resultado.get("sucesso"):
        return resultado or {"sucesso": False, "descricao": "Envio falhou"}

    protocolo = resultado.get("protocolo")
    if not protocolo:
        return {"sucesso": False, "descricao": "Sem protocolo"}

    # Poll
    for _ in range(MAX_POLL_RETRIES):
        time.sleep(POLL_DELAY)
        try:
            consulta = soap_consultar(protocolo, url_consulta)
        except Exception:
            continue
        if consulta.get("sucesso") and consulta.get("eventos"):
            return consulta
        if consulta.get("codigo_resposta") == "101":
            continue
        if "em processamento" in (consulta.get("descricao") or "").lower():
            continue
        if consulta.get("sucesso") is False:
            return consulta

    return {"sucesso": False, "descricao": "Timeout polling"}


# ═══════════════════════════════════════════════════════════════
# WORKER — processa 1 lote de 50 CPFs (thread-safe)
# ═══════════════════════════════════════════════════════════════

def process_lote(batch: list[dict], lote_num: int, empregador: dict,
                 per_apur: str, plansaude_map: dict, log) -> tuple:
    """
    Processa 1 lote. Thread-safe. NÃO toca no DB.
    Retorna: (lote_num, [(cpf, status, nr_recibo_novo, erro, lote_num)])
    """
    thread = threading.current_thread().name
    results = []

    try:
        # ── 1. Gerar + assinar XMLs ──
        xmls_assinados = []
        cpf_id_map = {}  # event_id → cpf

        for seq_idx, cpf_info in enumerate(batch, start=1):
            info_ir = None
            if cpf_info["infoIRCR"]:
                info_ir = {"infoIRCR": cpf_info["infoIRCR"]}

            # planSaude: lista de operadoras OU None
            plan_saude = plansaude_map.get(cpf_info["cpf"])

            # seq global único: (lote-1)*50 + seq_within_lote
            global_seq = (lote_num - 1) * LOTE_SIZE + seq_idx

            xml_bytes = S1210XMLGenerator.gerar(
                empregador=empregador,
                beneficiario={"cpfBenef": cpf_info["cpf"]},
                info_pgtos=cpf_info["pagamentos"],
                per_apur=per_apur,
                ind_retif="2",
                nr_recibo=cpf_info["nr_recibo"],
                info_ir_complem=info_ir,
                plan_saude=plan_saude,
                seq=global_seq,
                tp_amb=AMBIENTE,
            )
            signed = XMLSigner.assinar(xml_bytes, _pfx_data, _pfx_senha)
            xmls_assinados.append(signed)

            xml_str = signed.decode("utf-8") if isinstance(signed, bytes) else signed
            id_match = re.search(r'Id="(ID[^"]+)"', xml_str)
            if id_match:
                cpf_id_map[id_match.group(1)] = cpf_info["cpf"]

        # ── 2. Montar SOAP e enviar ──
        soap = SOAPEnvelopeBuilder.montar_envio(
            xmls_assinados, empregador, empregador, grupo=GRUPO
        )

        url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
        resultado = None

        for attempt in range(1, MAX_SEND_RETRIES + 1):
            try:
                resultado = soap_enviar(soap, url_envio)
                if resultado.get("sucesso"):
                    break
                erro = (resultado.get("descricao") or "").lower()
                if not any(kw in erro for kw in CONNECTION_ERRORS):
                    break
            except Exception as e:
                resultado = {"sucesso": False, "descricao": str(e), "protocolo": None}
            if attempt < MAX_SEND_RETRIES:
                time.sleep(SEND_RETRY_DELAY * attempt)

        if not resultado or not resultado.get("sucesso"):
            desc = (resultado or {}).get("descricao", "Envio falhou")
            log.error(f"  [{thread}] Lote {lote_num} envio FALHOU: {desc}")
            for ci in batch:
                results.append((ci["cpf"], "erro", None, desc, lote_num))
            return lote_num, results

        protocolo = resultado.get("protocolo")
        if not protocolo:
            for ci in batch:
                results.append((ci["cpf"], "erro", None, "Sem protocolo", lote_num))
            return lote_num, results

        # ── 3. Poll resultado ──
        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
        consulta = None

        for _ in range(MAX_POLL_RETRIES):
            time.sleep(POLL_DELAY)
            try:
                consulta = soap_consultar(protocolo, url_consulta)
            except Exception as e:
                log.warning(f"  [{thread}] Lote {lote_num} poll erro: {e}")
                continue
            if consulta.get("sucesso") and consulta.get("eventos"):
                break
            if consulta.get("codigo_resposta") == "101":
                continue
            if "em processamento" in (consulta.get("descricao") or "").lower():
                continue
            if consulta.get("sucesso") is False:
                break

        # ── 4. Processar eventos retornados ──
        if consulta and consulta.get("sucesso") and consulta.get("eventos"):
            eventos = consulta["eventos"]
            matched = set()

            # Match por ID do evento
            for evt in eventos:
                evt_id = evt.get("id", "")
                cpf_m = cpf_id_map.get(evt_id)
                nr_recibo = evt.get("nr_recibo")
                cod = evt.get("codigo_resposta", "")

                if cpf_m and nr_recibo:
                    results.append((cpf_m, "ok", nr_recibo, None, lote_num))
                    matched.add(cpf_m)
                elif cpf_m and cod and cod not in ("201", "202"):
                    desc = evt.get("descricao", "")
                    ocorrencias = evt.get("ocorrencias", [])
                    if ocorrencias:
                        desc += " | " + " | ".join(
                            f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                        )
                    results.append((cpf_m, "erro", None, desc, lote_num))
                    matched.add(cpf_m)

            # Fallback: match posicional
            if len(matched) < len(batch) and len(eventos) == len(batch):
                for evt, ci in zip(eventos, batch):
                    if ci["cpf"] not in matched:
                        nr_recibo = evt.get("nr_recibo")
                        if nr_recibo:
                            results.append((ci["cpf"], "ok", nr_recibo, None, lote_num))
                        else:
                            results.append((ci["cpf"], "erro", None,
                                          evt.get("descricao", "sem recibo"), lote_num))
                        matched.add(ci["cpf"])

            # Qualquer CPF sem resposta = erro
            for ci in batch:
                if ci["cpf"] not in matched:
                    results.append((ci["cpf"], "erro", None, "Sem resposta", lote_num))
        else:
            # Poll falhou — checar respostas parciais
            desc = (consulta or {}).get("descricao", "Timeout polling")
            log.error(f"  [{thread}] Lote {lote_num} poll FALHOU: {desc}")

            partial = set()
            if consulta and consulta.get("eventos"):
                for evt in consulta["eventos"]:
                    cpf_m = cpf_id_map.get(evt.get("id", ""))
                    if cpf_m and evt.get("nr_recibo"):
                        results.append((cpf_m, "ok", evt["nr_recibo"], None, lote_num))
                        partial.add(cpf_m)

            for ci in batch:
                if ci["cpf"] not in partial and not any(r[0] == ci["cpf"] for r in results):
                    results.append((ci["cpf"], "erro", None, desc, lote_num))

    except Exception as e:
        log.error(f"  [{thread}] Lote {lote_num} EXCEPTION: {e}")
        already = {r[0] for r in results}
        for ci in batch:
            if ci["cpf"] not in already:
                results.append((ci["cpf"], "erro", None, str(e), lote_num))

    return lote_num, results


# ═══════════════════════════════════════════════════════════════
# DB TRACKING
# ═══════════════════════════════════════════════════════════════

def db_create_run(per_apur: str, total_cpfs: int, total_lotes: int) -> int:
    conn = get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pipeline_runs (per_apur, status, total_cpfs, total_lotes)
                VALUES (%s, 'rodando', %s, %s)
                RETURNING id
            """, (per_apur, total_cpfs, total_lotes))
            run_id = cur.fetchone()[0]
            conn.commit()
            return run_id
    finally:
        conn.close()


def db_insert_cpfs(run_id: int, cpf_data: list[dict]):
    conn = get_supabase_conn()
    try:
        with conn.cursor() as cur:
            batch = [
                (run_id, d["cpf"], "pendente", d["nr_recibo"],
                 json.dumps(d["pagamentos"]), json.dumps(d.get("infoIRCR", [])))
                for d in cpf_data
            ]
            psycopg2.extras.execute_values(
                cur,
                """INSERT INTO pipeline_cpf_results
                    (run_id, cpf, status, nr_recibo_original, pagamentos, info_ir_cr)
                VALUES %s""",
                batch,
                template="(%s, %s, %s, %s, %s, %s)",
                page_size=500,
            )
            conn.commit()
    finally:
        conn.close()


def db_batch_update_cpfs(run_id: int, results_list: list):
    """Update múltiplos CPFs em UMA query."""
    if not results_list:
        return
    conn = get_supabase_conn()
    try:
        with conn.cursor() as cur:
            values = [
                (run_id, cpf, status, nr_recibo_novo, erro, lote_num)
                for cpf, status, nr_recibo_novo, erro, lote_num in results_list
            ]
            psycopg2.extras.execute_values(
                cur,
                """
                UPDATE pipeline_cpf_results AS t
                SET status = v.status,
                    nr_recibo_novo = v.nr_recibo_novo,
                    erro_descricao = v.erro_descricao,
                    lote_num = v.lote_num::int,
                    processed_at = NOW()
                FROM (VALUES %s) AS v(run_id_v, cpf_v, status, nr_recibo_novo, erro_descricao, lote_num)
                WHERE t.run_id = v.run_id_v::int AND t.cpf = v.cpf_v
                """,
                values,
                template="(%s, %s, %s, %s, %s, %s)",
                page_size=500,
            )
            conn.commit()
    finally:
        conn.close()


def db_update_run(run_id: int, **kwargs):
    conn = get_supabase_conn()
    try:
        sets = []
        vals = []
        for k, v in kwargs.items():
            sets.append(f"{k} = %s")
            vals.append(v)
        vals.append(run_id)
        with conn.cursor() as cur:
            cur.execute(f"UPDATE pipeline_runs SET {', '.join(sets)} WHERE id = %s", vals)
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# PROGRESS (resume)
# ═══════════════════════════════════════════════════════════════

def load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"cpfs_ok": [], "cpfs_erro": {}, "s1298_done": False, "s1299_done": False, "run_id": None}


def save_progress(progress: dict):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def run_pipeline(dry_run=False, no_close=False, only_errors=False, workers=PARALLEL_WORKERS, recibo_override_file=None):
    log = setup_logging()
    per_apur = PER_APUR

    mode_tags = []
    if dry_run: mode_tags.append("DRY-RUN")
    if no_close: mode_tags.append("SEM-FECHAR")
    if only_errors: mode_tags.append("SÓ-ERROS")
    mode_str = " | ".join(mode_tags) if mode_tags else "PRODUÇÃO"

    log.info("=" * 70)
    log.info(f"  PIPELINE V2 — {per_apur} — {mode_str}")
    log.info(f"  {workers} workers, lotes de {LOTE_SIZE}, SEM S-5002")
    log.info("=" * 70)

    # ══ STEP 0: Carregar tudo ══════════════════════════════════
    log.info("\n[STEP 0] Carregando dados...")

    # 0.1 Certificado
    cert = load_cert()
    if not cert:
        log.error("ERRO: Nenhum certificado A1 ativo!")
        sys.exit(1)
    with open(cert["arquivo_path"], "rb") as f:
        pfx_data = f.read()
    senha = cert["senha"]
    cnpj = cert["cnpj"]
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    setup_pem_cache(pfx_data, senha)
    log.info(f"  Certificado: CNPJ {cnpj}")

    # 0.2 Dados S-1210 originais
    log.info("  Carregando S-1210 do explorador...")
    cpf_data = load_s1210_data(per_apur)
    log.info(f"  {len(cpf_data)} CPFs com S-1210 original")

    if not cpf_data:
        log.error("Nenhum S-1210 encontrado!")
        cleanup_pem_cache()
        sys.exit(1)

    # Filtrar sem pagamentos
    sem_pgto = [d for d in cpf_data if not d["pagamentos"]]
    if sem_pgto:
        log.warning(f"  {len(sem_pgto)} CPFs sem pagamentos (ignorados)")
        cpf_data = [d for d in cpf_data if d["pagamentos"]]

    # 0.3 Recibos mais recentes (retificação em cadeia)
    log.info("  Carregando recibos mais recentes...")
    latest_recibos = load_latest_recibos(per_apur)
    log.info(f"  {len(latest_recibos)} CPFs com retificação anterior")

    # Aplicar recibo mais recente (override)
    updated_count = 0
    for d in cpf_data:
        latest = latest_recibos.get(d["cpf"])
        if latest:
            d["nr_recibo"] = latest
            updated_count += 1
        else:
            d["nr_recibo"] = d["nr_recibo_original"]
    log.info(f"  {updated_count} recibos atualizados para versão mais recente")

    # 0.3b Override manual de recibos (p/ CPFs [459])
    if recibo_override_file:
        with open(recibo_override_file) as f:
            overrides = json.load(f)
        override_count = 0
        for d in cpf_data:
            if d["cpf"] in overrides:
                d["nr_recibo"] = overrides[d["cpf"]]
                override_count += 1
        log.info(f"  {override_count} recibos com override manual ({recibo_override_file})")


    # 0.4 Mapa planSaude V2
    map_path = os.path.join(os.path.dirname(__file__), MAP_FILE)
    log.info(f"  Carregando mapa planSaude: {MAP_FILE}")
    plansaude_map = load_plansaude_map(map_path)
    log.info(f"  {len(plansaude_map)} CPFs com planSaude no mapa")

    # Contar quantos CPFs do pipeline tem/não tem planSaude
    cpf_set = {d["cpf"] for d in cpf_data}
    com_plan = sum(1 for cpf in cpf_set if cpf in plansaude_map)
    sem_plan = len(cpf_set) - com_plan
    log.info(f"  No pipeline: {com_plan} COM planSaude, {sem_plan} SEM planSaude")

    # 0.5 Filtrar se --only-errors
    if only_errors:
        error_cpfs = load_error_cpfs(per_apur)
        log.info(f"  [SÓ-ERROS] {len(error_cpfs)} CPFs com erro no último run")
        cpf_data = [d for d in cpf_data if d["cpf"] in error_cpfs]
        log.info(f"  [SÓ-ERROS] {len(cpf_data)} CPFs para reprocessar")

    if not cpf_data:
        log.info("  Nenhum CPF para processar!")
        cleanup_pem_cache()
        return

    total_lotes = (len(cpf_data) + LOTE_SIZE - 1) // LOTE_SIZE

    # ── DRY RUN ──
    if dry_run:
        log.info(f"\n  [DRY-RUN] {len(cpf_data)} CPFs seriam retificados em {total_lotes} lotes")
        log.info(f"  [DRY-RUN] {com_plan} COM planSaude, {sem_plan} SEM planSaude")
        log.info(f"  [DRY-RUN] Nenhum evento enviado.")

        # Mostrar sample
        sample = cpf_data[:3]
        for d in sample:
            ps = plansaude_map.get(d["cpf"])
            ps_str = json.dumps(ps, ensure_ascii=False) if ps else "None"
            log.info(f"    CPF {d['cpf']}: recibo={d['nr_recibo'][:20]}... planSaude={ps_str}")

        cleanup_pem_cache()
        return {"per_apur": per_apur, "total_cpfs": len(cpf_data), "dry_run": True}

    # ══ SETUP DB RUN ══════════════════════════════════════════
    progress = load_progress()
    run_id = progress.get("run_id")

    if not run_id:
        run_id = db_create_run(per_apur, len(cpf_data), total_lotes)
        progress["run_id"] = run_id
        save_progress(progress)
        log.info(f"\n  Run criado: id={run_id}")

        db_insert_cpfs(run_id, cpf_data)
        log.info(f"  {len(cpf_data)} CPFs inseridos como pendente")
    else:
        # Resume: checar já processados
        conn = get_supabase_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT cpf FROM pipeline_cpf_results WHERE run_id=%s AND status IN ('ok','erro')",
                    (run_id,)
                )
                db_done = {row[0] for row in cur.fetchall()}
        finally:
            conn.close()
        log.info(f"  Resumindo run_id={run_id}: {len(db_done)} já processados")
        db_update_run(run_id, status="rodando")

    # CPFs restantes
    already_done = set(progress.get("cpfs_ok", []))
    if run_id and not progress.get("just_created"):
        conn = get_supabase_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT cpf FROM pipeline_cpf_results WHERE run_id=%s AND status IN ('ok','erro')",
                    (run_id,)
                )
                already_done |= {row[0] for row in cur.fetchall()}
        finally:
            conn.close()

    remaining = [d for d in cpf_data if d["cpf"] not in already_done]
    log.info(f"  Restantes: {len(remaining)} CPFs")

    if not remaining:
        log.info("  Todos os CPFs já processados!")
        # Pular para S-1299 se necessário
    else:
        # ══ STEP 1: S-1298 Reabrir ═══════════════════════════
        if not progress.get("s1298_done"):
            log.info(f"\n{'─'*60}")
            log.info(f"  [STEP 1] S-1298 — Reabrir {per_apur}")
            log.info(f"{'─'*60}")

            xml = S1298XMLGenerator.gerar(empregador, per_apur, IND_APURACAO, tp_amb=AMBIENTE)
            result = enviar_evento_unico(xml, empregador)

            # "Já aberto" conta como sucesso
            if not result.get("sucesso") and result.get("descricao"):
                desc_lower = result["descricao"].lower()
                if any(kw in desc_lower for kw in ["já se encontra", "já está abert", "[715]", "período já"]):
                    result["sucesso"] = True
                    result["descricao"] = f"[JÁ ABERTO] {result['descricao']}"

            if result.get("sucesso"):
                log.info(f"  ✓ S-1298: {result.get('descricao', 'OK')}")
                progress["s1298_done"] = True
                save_progress(progress)
                recibo = None
                for e in result.get("eventos", []):
                    if e.get("nr_recibo"):
                        recibo = e["nr_recibo"]
                        break
                db_update_run(run_id, s1298_done=True, s1298_recibo=recibo)
            else:
                log.error(f"  ✗ S-1298 FALHOU: {result.get('descricao')}")
                db_update_run(run_id, status="erro", erro_fatal=f"S-1298: {result.get('descricao')}")
                cleanup_pem_cache()
                sys.exit(1)
        else:
            log.info("  [STEP 1] S-1298 já executado (resumindo)")

        # ══ STEP 2: S-1210 Retificar (paralelo) ══════════════
        log.info(f"\n{'─'*60}")
        log.info(f"  [STEP 2] S-1210 Retificar — {len(remaining)} CPFs, {workers} workers")
        log.info(f"{'─'*60}")

        # Dividir em lotes
        lotes = [remaining[i:i + LOTE_SIZE] for i in range(0, len(remaining), LOTE_SIZE)]
        total_lotes_now = len(lotes)
        total_ok = 0
        total_erro = 0
        t_start = time.time()

        # Processar em waves de N workers
        for wave_start in range(0, total_lotes_now, workers):
            wave_lotes = lotes[wave_start:wave_start + workers]
            wave_num = wave_start // workers + 1
            total_waves = (total_lotes_now + workers - 1) // workers
            wave_cpfs = sum(len(l) for l in wave_lotes)

            log.info(f"\n  Wave {wave_num}/{total_waves}: {len(wave_lotes)} lotes, {wave_cpfs} CPFs")

            wave_results = []

            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="W") as executor:
                futures = {}
                for idx, batch in enumerate(wave_lotes):
                    lote_num = wave_start + idx + 1
                    future = executor.submit(
                        process_lote, batch, lote_num, empregador,
                        per_apur, plansaude_map, log
                    )
                    futures[future] = lote_num

                for future in as_completed(futures):
                    try:
                        lote_done, cpf_results = future.result(timeout=180)
                        wave_results.extend(cpf_results)

                        ok_n = sum(1 for r in cpf_results if r[1] == "ok")
                        err_n = sum(1 for r in cpf_results if r[1] == "erro")
                        log.info(f"    Lote {lote_done}: {ok_n} ok, {err_n} erro")
                    except Exception as e:
                        lote_n = futures[future]
                        log.error(f"    Lote {lote_n} EXCEPTION: {e}")
                        # Marcar CPFs do lote como erro
                        if (lote_n - wave_start - 1) < len(wave_lotes):
                            for ci in wave_lotes[lote_n - wave_start - 1]:
                                wave_results.append((ci["cpf"], "erro", None, str(e), lote_n))

            # DB batch update da wave inteira
            if wave_results:
                db_batch_update_cpfs(run_id, wave_results)

                for cpf, status, recibo, erro, _ in wave_results:
                    if status == "ok":
                        progress["cpfs_ok"].append(cpf)
                        total_ok += 1
                    else:
                        progress["cpfs_erro"][cpf] = erro or ""
                        total_erro += 1

                save_progress(progress)
                db_update_run(run_id, cpfs_ok=len(progress["cpfs_ok"]),
                             cpfs_erro=len(progress["cpfs_erro"]))

            elapsed = time.time() - t_start
            processed = total_ok + total_erro
            rate = processed / elapsed if elapsed > 0 else 0
            remaining_n = len(remaining) - processed
            eta = remaining_n / rate if rate > 0 else 0
            log.info(f"  Progresso: {processed}/{len(remaining)} ({rate:.1f} CPFs/s, ETA {eta/60:.1f}min)")

        log.info(f"\n  S-1210 retif concluído: {total_ok} OK, {total_erro} erros ({time.time()-t_start:.0f}s)")

    # ══ STEP 3: S-1299 Fechar ═════════════════════════════════
    if no_close:
        log.info(f"\n  [STEP 3] S-1299 PULADO (--no-close)")
    elif not progress.get("s1299_done"):
        log.info(f"\n{'─'*60}")
        log.info(f"  [STEP 3] S-1299 — Fechar {per_apur}")
        log.info(f"{'─'*60}")

        total_erros_final = len(progress.get("cpfs_erro", {}))
        if total_erros_final > 0:
            log.warning(f"  ATENÇÃO: {total_erros_final} CPFs com erro. Fechando assim mesmo.")

        xml = S1299XMLGenerator.gerar(empregador, per_apur, IND_APURACAO, tp_amb=AMBIENTE)
        result = enviar_evento_unico(xml, empregador)

        if result.get("sucesso"):
            recibo = None
            for e in result.get("eventos", []):
                if e.get("nr_recibo"):
                    recibo = e["nr_recibo"]
                    break
            log.info(f"  ✓ S-1299: OK (recibo: {recibo})")
            progress["s1299_done"] = True
            save_progress(progress)
            db_update_run(run_id, s1299_done=True, s1299_recibo=recibo)
        else:
            log.error(f"  ✗ S-1299 FALHOU: {result.get('descricao')}")
    else:
        log.info("  [STEP 3] S-1299 já executado")

    # ══ RESUMO FINAL ══════════════════════════════════════════
    final_ok = len(progress.get("cpfs_ok", []))
    final_erro = len(progress.get("cpfs_erro", {}))
    final_status = "completo" if (
        progress.get("s1298_done") and progress.get("s1299_done") and final_erro == 0
    ) else "parcial"

    db_update_run(
        run_id,
        status=final_status,
        cpfs_ok=final_ok,
        cpfs_erro=final_erro,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )

    log.info(f"\n{'='*70}")
    log.info(f"  RESUMO FINAL — PIPELINE V2")
    log.info(f"{'='*70}")
    log.info(f"  Período:  {per_apur}")
    log.info(f"  Run ID:   {run_id}")
    log.info(f"  Total:    {len(cpf_data)} CPFs")
    log.info(f"  OK:       {final_ok}")
    log.info(f"  Erros:    {final_erro}")
    log.info(f"  S-1298:   {'✓' if progress.get('s1298_done') else '✗'}")
    log.info(f"  S-1299:   {'✓' if progress.get('s1299_done') else '✗'}")
    log.info(f"  STATUS:   {final_status.upper()}")
    log.info(f"{'='*70}")

    # Salvar resultado final
    final_result = {
        "run_id": run_id,
        "per_apur": per_apur,
        "status": final_status,
        "total_cpfs": len(cpf_data),
        "cpfs_ok": final_ok,
        "cpfs_erro": final_erro,
        "s1298_done": progress.get("s1298_done"),
        "s1299_done": progress.get("s1299_done"),
        "plansaude_map_version": "v2",
        "plansaude_cpfs": com_plan,
        "sem_plansaude_cpfs": sem_plan,
        "erros_detalhe": progress.get("cpfs_erro", {}),
        "timestamp": datetime.now().isoformat(),
    }
    with open(RESULT_FILE, "w") as f:
        json.dump(final_result, f, indent=2, default=str, ensure_ascii=False)
    log.info(f"  Resultado: {RESULT_FILE}")
    log.info(f"  Log:       {LOG_FILE}")

    cleanup_pem_cache()
    return final_result


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Pipeline V2 — Retificação S-1210 Janeiro 2025")
    parser.add_argument("--dry-run", action="store_true", help="Só conta CPFs, não envia nada")
    parser.add_argument("--no-close", action="store_true", help="NÃO envia S-1299 (não fecha período)")
    parser.add_argument("--only-errors", action="store_true", help="Só reprocessa CPFs com erro do último run")
    parser.add_argument("--workers", type=int, default=PARALLEL_WORKERS, help=f"Workers paralelos (default: {PARALLEL_WORKERS})")
    parser.add_argument("--recibo-override", type=str, help="JSON file com {cpf: recibo_correto} p/ override")
    args = parser.parse_args()

    run_pipeline(
        dry_run=args.dry_run,
        no_close=args.no_close,
        only_errors=args.only_errors,
        workers=args.workers,
        recibo_override_file=args.recibo_override,
    )


if __name__ == "__main__":
    main()
