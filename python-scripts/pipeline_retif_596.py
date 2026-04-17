"""
Pipeline Retificação S-1210 — Rubrica 596 (Desconto INSS 13º)
═══════════════════════════════════════════════════════════════
Reenvia S-1210 IDÊNTICO com indRetif=2 para todos os CPFs que têm rubrica 596.
O eSocial recalcula com a natureza corrigida (codIncIRRF 41→42).

NÃO abre/fecha período (S-1298/S-1299) — janeiro 2025 já está aberto.
NÃO altera planSaude — usa exatamente o que já estava.

Lotes de 50, 5 workers paralelos.

Uso:
  python pipeline_retif_596.py                   # roda tudo
  python pipeline_retif_596.py --dry-run          # só conta, não envia
  python pipeline_retif_596.py --workers 3        # menos workers
  python pipeline_retif_596.py --limit 100        # testa com 100 CPFs
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
import zipfile
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
import psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════

PER_APUR = "2025-01"
AMBIENTE = "1"        # PRODUÇÃO
GRUPO = "3"           # eventos periódicos

LOTE_SIZE = 50        # max eventos por lote SOAP
PARALLEL_WORKERS = 5  # lotes simultâneos
POLL_DELAY = 5        # seconds entre polls
MAX_POLL_RETRIES = 24 # 24 × 5s = 120s max wait
MAX_SEND_RETRIES = 3  # retries por lote (conexão)
SEND_RETRY_DELAY = 5  # seconds entre retries

DB_RETRY_MAX = 5
DB_RETRY_DELAY = 3

CPF_LIST_FILE = "c:/tmp/cpfs_596_TODOS.txt"
ZIP_PATH = os.path.expanduser("~/Downloads/29429360 jan2025.zip")
MAP_FILE = "plansaude_map_v2_jan2025.json"

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
    "name resolution", "temporary failure", "could not translate host name",
]

LOG_FILE = "/tmp/pipeline_retif_596.log"
PROGRESS_FILE = "/tmp/pipeline_retif_596_progress.json"

# PEM cache global
_cert_pem_path = None
_key_pem_path = None
_pfx_data = None
_pfx_senha = None


# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

def setup_logging():
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )
    return logging.getLogger("retif_596")


# ═══════════════════════════════════════════════════════════════
# DB HELPERS
# ═══════════════════════════════════════════════════════════════

def get_conn():
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
# PEM CACHE
# ═══════════════════════════════════════════════════════════════

def setup_pem_cache(pfx_data, senha):
    global _cert_pem_path, _key_pem_path, _pfx_data, _pfx_senha
    _pfx_data = pfx_data
    _pfx_senha = senha
    cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, senha)

    cf = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_596_cert.pem")
    cf.write(cert_pem); cf.close(); _cert_pem_path = cf.name
    kf = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_596_key.pem")
    kf.write(key_pem); kf.close(); _key_pem_path = kf.name


def cleanup_pem():
    for p in (_cert_pem_path, _key_pem_path):
        if p:
            try: os.unlink(p)
            except: pass


# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

def load_cpf_list() -> list[str]:
    """Carrega lista de CPFs com rubrica 596."""
    with open(CPF_LIST_FILE) as f:
        cpfs = [l.strip() for l in f if l.strip()]
    return cpfs


def load_s1210_from_db(cpfs_596: set) -> dict:
    """
    Carrega dados S-1210 do explorador_eventos para os CPFs 596.
    Retorna: {cpf: {pagamentos, infoIRCR, nr_recibo_original}}
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT e.cpf, e.nr_recibo, e.dados_json
                FROM explorador_eventos e
                WHERE e.tipo_evento = 'S-1210'
                  AND e.per_apur = %s
                  AND e.cpf = ANY(%s)
                  AND e.nr_recibo IS NOT NULL
                  AND COALESCE(e.dados_json->>'indRetif', '1') != '2'
                ORDER BY e.cpf, e.id ASC
            """, (PER_APUR, list(cpfs_596)))
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
                "pagamentos": pagamentos,
                "infoIRCR": info_ir_cr,
                "nr_recibo_original": row["nr_recibo"],
            }
        return cpf_map
    finally:
        conn.close()


def load_s1210_from_zip(cpfs_missing: set) -> dict:
    """
    Extrai S-1210 do zip para CPFs que não estão no explorador.
    Retorna: {cpf: {pagamentos, infoIRCR, nr_recibo_original}}
    """
    if not cpfs_missing or not os.path.exists(ZIP_PATH):
        return {}

    zf = zipfile.ZipFile(ZIP_PATH, "r")
    s1210_files = [n for n in zf.namelist() if "S-1210" in n and n.endswith(".xml")]

    results = {}
    for name in s1210_files:
        text = zf.read(name).decode("utf-8", errors="replace")
        # Check if any missing CPF is in this file
        found_cpf = None
        for cpf in cpfs_missing:
            if cpf in text:
                found_cpf = cpf
                break
        if not found_cpf or found_cpf in results:
            continue

        # Extract nrRecibo
        nr_rec = re.findall(r"<nrRecibo>([^<]+)</nrRecibo>", text)

        # Extract pagamentos
        pgtos = []
        for p in re.findall(r"<infoPgto>(.*?)</infoPgto>", text, re.DOTALL):
            dt = re.search(r"<dtPgto>([^<]+)", p)
            tp = re.search(r"<tpPgto>([^<]+)", p)
            pr = re.search(r"<perRef>([^<]+)", p)
            dm = re.search(r"<ideDmDev>([^<]+)", p)
            vr = re.search(r"<vrLiq>([^<]+)", p)
            pgtos.append({
                "dtPgto": dt.group(1) if dt else "",
                "tpPgto": tp.group(1) if tp else "1",
                "perRef": pr.group(1) if pr else "",
                "ideDmDev": dm.group(1) if dm else "",
                "vrLiq": vr.group(1) if vr else "0",
            })

        # Extract infoIRCR
        info_ir_crs = []
        irc_match = re.search(r"<infoIRComplem>(.*?)</infoIRComplem>", text, re.DOTALL)
        if irc_match:
            for cr in re.findall(r"<infoIRCR>(.*?)</infoIRCR>", irc_match.group(1), re.DOTALL):
                tpcr = re.search(r"<tpCR>([^<]+)", cr)
                vrcr = re.search(r"<vrCR>([^<]+)", cr)
                cr_data = {"tpCR": tpcr.group(1) if tpcr else ""}
                if vrcr:
                    cr_data["vrCR"] = vrcr.group(1)
                # dedDepen
                ded_deps = []
                for dd in re.findall(r"<dedDepen>(.*?)</dedDepen>", cr, re.DOTALL):
                    tr = re.search(r"<tpRend>([^<]+)", dd)
                    cd = re.search(r"<cpfDep>([^<]+)", dd)
                    vd = re.search(r"<vlrDedDep>([^<]+)", dd)
                    ded_deps.append({
                        "tpRend": tr.group(1) if tr else "",
                        "cpfDep": cd.group(1) if cd else "",
                        "vlrDedDep": vd.group(1) if vd else "",
                    })
                if ded_deps:
                    cr_data["dedDepen"] = ded_deps
                # penAlim
                pen_alims = []
                for pa in re.findall(r"<penAlim>(.*?)</penAlim>", cr, re.DOTALL):
                    tr = re.search(r"<tpRend>([^<]+)", pa)
                    cd = re.search(r"<cpfDep>([^<]+)", pa)
                    vp = re.search(r"<vlrDedPenAlim>([^<]+)", pa)
                    pen_alims.append({
                        "tpRend": tr.group(1) if tr else "",
                        "cpfDep": cd.group(1) if cd else "",
                        "vlrDedPenAlim": vp.group(1) if vp else "",
                    })
                if pen_alims:
                    cr_data["penAlim"] = pen_alims
                info_ir_crs.append(cr_data)

        if pgtos:
            results[found_cpf] = {
                "pagamentos": pgtos,
                "infoIRCR": info_ir_crs,
                "nr_recibo_original": nr_rec[-1] if nr_rec else None,
            }

        if len(results) >= len(cpfs_missing):
            break

    zf.close()
    return results


def load_latest_recibos() -> dict:
    """Busca recibo MAIS RECENTE de cada CPF (retificação em cadeia)."""
    conn = get_conn()
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
            """, (PER_APUR,))
            return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        conn.close()


def load_plansaude_map() -> dict:
    """Carrega mapa planSaude (reusar o existente)."""
    map_path = os.path.join(os.path.dirname(__file__), MAP_FILE)
    if os.path.exists(map_path):
        with open(map_path) as f:
            return json.load(f)
    return {}


# ═══════════════════════════════════════════════════════════════
# SOAP (thread-safe)
# ═══════════════════════════════════════════════════════════════

def soap_enviar(soap_envelope):
    url = SOAPEnvelopeBuilder.url_envio(producao=True)
    resp = requests.post(
        url=url, data=soap_envelope.encode("utf-8"),
        headers=SOAPEnvelopeBuilder.headers(),
        cert=(_cert_pem_path, _key_pem_path), verify=False, timeout=60,
    )
    resp.raise_for_status()
    return ESocialClient._parsear_resposta_envio(resp.text)


def soap_consultar(protocolo):
    url = SOAPEnvelopeBuilder.url_consulta(producao=True)
    soap_xml = SOAPEnvelopeBuilder.montar_consulta(protocolo)
    resp = requests.post(
        url=url, data=soap_xml.encode("utf-8"),
        headers=SOAPEnvelopeBuilder.headers_consulta(),
        cert=(_cert_pem_path, _key_pem_path), verify=False, timeout=60,
    )
    resp.raise_for_status()
    return ESocialClient._parsear_resposta_consulta(resp.text)


# ═══════════════════════════════════════════════════════════════
# WORKER — processa 1 lote de até 50 CPFs (thread-safe)
# ═══════════════════════════════════════════════════════════════

def process_lote(batch, lote_num, empregador, plansaude_map, log):
    """
    Processa 1 lote. Thread-safe.
    Retorna: (lote_num, [(cpf, status, nr_recibo_novo, erro, lote_num)])
    """
    thread = threading.current_thread().name
    results = []

    try:
        # 1. Gerar + assinar XMLs
        xmls_assinados = []
        cpf_id_map = {}

        for seq_idx, cpf_info in enumerate(batch, start=1):
            info_ir = None
            if cpf_info["infoIRCR"]:
                info_ir = {"infoIRCR": cpf_info["infoIRCR"]}

            plan_saude = plansaude_map.get(cpf_info["cpf"])
            global_seq = (lote_num - 1) * LOTE_SIZE + seq_idx

            xml_bytes = S1210XMLGenerator.gerar(
                empregador=empregador,
                beneficiario={"cpfBenef": cpf_info["cpf"]},
                info_pgtos=cpf_info["pagamentos"],
                per_apur=PER_APUR,
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

        # 2. Montar SOAP e enviar
        soap = SOAPEnvelopeBuilder.montar_envio(
            xmls_assinados, empregador, empregador, grupo=GRUPO
        )

        resultado = None
        for attempt in range(1, MAX_SEND_RETRIES + 1):
            try:
                resultado = soap_enviar(soap)
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

        log.info(f"  [{thread}] Lote {lote_num}: protocolo {protocolo}")

        # 3. Poll resultado
        consulta = None
        for _ in range(MAX_POLL_RETRIES):
            time.sleep(POLL_DELAY)
            try:
                consulta = soap_consultar(protocolo)
            except Exception as e:
                continue
            if consulta.get("sucesso") and consulta.get("eventos"):
                break
            if consulta.get("codigo_resposta") == "101":
                continue
            if "em processamento" in (consulta.get("descricao") or "").lower():
                continue
            if consulta.get("sucesso") is False:
                break

        # 4. Processar eventos retornados
        if consulta and consulta.get("sucesso") and consulta.get("eventos"):
            eventos = consulta["eventos"]
            matched = set()

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

            # Fallback posicional
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

            for ci in batch:
                if ci["cpf"] not in matched:
                    results.append((ci["cpf"], "erro", None, "Sem resposta", lote_num))
        else:
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

def db_create_run(total_cpfs, total_lotes):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pipeline_runs (per_apur, status, total_cpfs, total_lotes)
                VALUES (%s, 'rodando', %s, %s)
                RETURNING id
            """, (PER_APUR, total_cpfs, total_lotes))
            run_id = cur.fetchone()[0]
            conn.commit()
            return run_id
    finally:
        conn.close()


def db_insert_cpfs(run_id, cpf_data):
    conn = get_conn()
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


def db_batch_update_cpfs(run_id, results_list):
    if not results_list:
        return
    conn = get_conn()
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


def db_update_run(run_id, **kwargs):
    conn = get_conn()
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
# PROGRESS
# ═══════════════════════════════════════════════════════════════

_progress_lock = threading.Lock()

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"cpfs_ok": [], "lotes_done": [], "run_id": None}


def save_progress(progress):
    with _progress_lock:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(progress, f, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def run_pipeline(dry_run=False, workers=PARALLEL_WORKERS, limit=None):
    log = setup_logging()

    log.info("=" * 70)
    log.info("  PIPELINE RETIFICAÇÃO S-1210 — RUBRICA 596")
    log.info(f"  Período: {PER_APUR} | Ambiente: PRODUÇÃO")
    log.info(f"  Workers: {workers} | Lote: {LOTE_SIZE}")
    if dry_run:
        log.info("  MODO: DRY-RUN (nenhum envio)")
    log.info("=" * 70)

    # ══ STEP 0: Carregar dados ═════════════════════════════════
    log.info("\n[STEP 0] Carregando dados...")

    # 0.1 Certificado
    cert = load_cert()
    if not cert:
        log.error("Nenhum certificado A1 ativo!"); return
    with open(cert["arquivo_path"], "rb") as f:
        pfx_data = f.read()
    setup_pem_cache(pfx_data, cert["senha"])
    cnpj = cert["cnpj"]
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    log.info(f"  Certificado: CNPJ {cnpj}")

    # 0.2 Lista de CPFs com 596
    cpfs_596 = load_cpf_list()
    log.info(f"  CPFs com rubrica 596: {len(cpfs_596)}")

    # 0.3 Dados S-1210 do explorador
    cpfs_set = set(cpfs_596)
    log.info("  Carregando S-1210 do explorador...")
    db_data = load_s1210_from_db(cpfs_set)
    log.info(f"  {len(db_data)} CPFs com S-1210 no explorador")

    # 0.4 CPFs faltando — buscar do zip
    missing_cpfs = cpfs_set - set(db_data.keys())
    if missing_cpfs:
        log.info(f"  {len(missing_cpfs)} CPFs faltando — buscando no zip...")
        zip_data = load_s1210_from_zip(missing_cpfs)
        log.info(f"  {len(zip_data)} encontrados no zip")
        db_data.update(zip_data)
        still_missing = missing_cpfs - set(zip_data.keys())
        if still_missing:
            log.warning(f"  {len(still_missing)} CPFs sem S-1210 em nenhuma fonte: {list(still_missing)[:10]}")

    # 0.5 Recibos mais recentes
    log.info("  Carregando recibos mais recentes do pipeline...")
    latest_recibos = load_latest_recibos()
    log.info(f"  {len(latest_recibos)} CPFs com retificação anterior")

    # 0.6 planSaude map
    plansaude_map = load_plansaude_map()
    log.info(f"  {len(plansaude_map)} CPFs no mapa planSaude")

    # 0.7 Montar lista final
    cpf_data = []
    skipped_no_data = 0
    skipped_no_recibo = 0
    skipped_no_pgto = 0

    for cpf in cpfs_596:
        data = db_data.get(cpf)
        if not data:
            skipped_no_data += 1
            continue
        if not data["pagamentos"]:
            skipped_no_pgto += 1
            continue

        # Recibo: pipeline > explorador > zip
        nr_recibo = latest_recibos.get(cpf) or data.get("nr_recibo_original")
        if not nr_recibo:
            skipped_no_recibo += 1
            continue

        cpf_data.append({
            "cpf": cpf,
            "nr_recibo": nr_recibo,
            "pagamentos": data["pagamentos"],
            "infoIRCR": data.get("infoIRCR", []),
        })

    log.info(f"\n  RESUMO:")
    log.info(f"    CPFs prontos para envio: {len(cpf_data)}")
    log.info(f"    Skipped sem dados S-1210: {skipped_no_data}")
    log.info(f"    Skipped sem pagamentos: {skipped_no_pgto}")
    log.info(f"    Skipped sem recibo: {skipped_no_recibo}")

    if limit:
        cpf_data = cpf_data[:limit]
        log.info(f"    LIMITADO a {limit} CPFs")

    if not cpf_data:
        log.info("  Nenhum CPF para processar!")
        cleanup_pem()
        return

    # ══ STEP 1: Montar lotes ══════════════════════════════════
    total_lotes = (len(cpf_data) + LOTE_SIZE - 1) // LOTE_SIZE
    lotes = [cpf_data[i:i + LOTE_SIZE] for i in range(0, len(cpf_data), LOTE_SIZE)]
    log.info(f"\n[STEP 1] {len(cpf_data)} CPFs em {total_lotes} lotes de {LOTE_SIZE}")

    # Resume: pular lotes já processados
    progress = load_progress()
    cpfs_already_ok = set(progress.get("cpfs_ok", []))
    if cpfs_already_ok:
        log.info(f"  Resumindo: {len(cpfs_already_ok)} CPFs já OK")
        lotes_filtered = []
        for lote in lotes:
            remaining = [c for c in lote if c["cpf"] not in cpfs_already_ok]
            if remaining:
                lotes_filtered.append(remaining)
        lotes = lotes_filtered
        total_lotes = len(lotes)
        log.info(f"  Lotes restantes: {total_lotes}")

    if not lotes:
        log.info("  Todos os CPFs já processados!")
        cleanup_pem()
        return

    # Dry run
    if dry_run:
        log.info(f"\n  [DRY-RUN] {len(cpf_data)} CPFs em {total_lotes} lotes")
        for i, lote in enumerate(lotes[:3], 1):
            log.info(f"    Lote {i}: {len(lote)} CPFs — ex: {lote[0]['cpf']}")
        cleanup_pem()
        return

    # ══ STEP 2: DB tracking ═══════════════════════════════════
    run_id = progress.get("run_id")
    if not run_id:
        run_id = db_create_run(len(cpf_data), total_lotes)
        progress["run_id"] = run_id
        save_progress(progress)
        log.info(f"\n[STEP 2] Run criado: id={run_id}")
        db_insert_cpfs(run_id, cpf_data)
        log.info(f"  {len(cpf_data)} CPFs inseridos como pendente")
    else:
        log.info(f"\n[STEP 2] Resumindo run_id={run_id}")

    # ══ STEP 3: Enviar lotes em paralelo ══════════════════════
    log.info(f"\n[STEP 3] Enviando {total_lotes} lotes com {workers} workers...")
    t_start = time.time()

    total_ok = 0
    total_erro = 0
    all_results = []

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="w") as pool:
        futures = {}
        for i, lote in enumerate(lotes, 1):
            f = pool.submit(process_lote, lote, i, empregador, plansaude_map, log)
            futures[f] = i

        for future in as_completed(futures):
            lote_num = futures[future]
            try:
                ln, results = future.result()
            except Exception as e:
                log.error(f"  Lote {lote_num} EXCEPTION FATAL: {e}")
                continue

            ok_count = sum(1 for r in results if r[1] == "ok")
            err_count = sum(1 for r in results if r[1] == "erro")
            total_ok += ok_count
            total_erro += err_count
            all_results.extend(results)

            log.info(f"  Lote {lote_num}/{total_lotes}: {ok_count} OK, {err_count} ERRO")

            # Update DB
            try:
                db_batch_update_cpfs(run_id, results)
            except Exception as e:
                log.warning(f"  DB update lote {lote_num} falhou: {e}")

            # Update progress
            for cpf, status, nr_rec, erro, ln in results:
                if status == "ok":
                    progress.setdefault("cpfs_ok", []).append(cpf)
            save_progress(progress)

    elapsed = time.time() - t_start

    # ══ RESULTADO FINAL ═══════════════════════════════════════
    log.info("\n" + "=" * 70)
    log.info(f"  PIPELINE RETIF 596 — RESULTADO FINAL")
    log.info(f"  Total: {len(cpf_data)} CPFs")
    log.info(f"  OK: {total_ok}")
    log.info(f"  ERRO: {total_erro}")
    log.info(f"  Tempo: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    log.info("=" * 70)

    # Update run status
    try:
        db_update_run(run_id,
                      status="finalizado",
                      total_ok=total_ok,
                      total_erro=total_erro)
    except Exception as e:
        log.warning(f"  DB run update falhou: {e}")

    # Salvar resultado
    result_file = "/tmp/pipeline_retif_596_result.json"
    result = {
        "run_id": run_id,
        "total_cpfs": len(cpf_data),
        "total_ok": total_ok,
        "total_erro": total_erro,
        "elapsed_seconds": round(elapsed, 1),
        "errors": [
            {"cpf": r[0], "erro": r[3]}
            for r in all_results if r[1] == "erro"
        ],
    }
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    log.info(f"  Resultado salvo em {result_file}")

    cleanup_pem()
    return result


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline retificação S-1210 rubrica 596")
    parser.add_argument("--dry-run", action="store_true", help="Só conta, não envia")
    parser.add_argument("--workers", type=int, default=PARALLEL_WORKERS, help=f"Workers paralelos (default: {PARALLEL_WORKERS})")
    parser.add_argument("--limit", type=int, default=None, help="Limitar a N CPFs (teste)")
    args = parser.parse_args()

    run_pipeline(
        dry_run=args.dry_run,
        workers=args.workers,
        limit=args.limit,
    )
