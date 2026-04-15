"""
Pipeline Batch TURBO -- Retificacao S-1210 em massa (PARALELO).
================================================================
Versao otimizada do pipeline_batch.py.
Usa ThreadPoolExecutor para enviar multiplos lotes ao eSocial simultaneamente.

Ganho: ~5x mais rapido que a versao sequencial.

Uso:
  python pipeline_batch_turbo.py --periodo 2025-01
  python pipeline_batch_turbo.py --periodo 2025-01 --workers 5

Resume automaticamente do run existente (mesmo run_id, mesma tabela).
Nao toca nos CPFs ja processados (ok ou erro).
"""

import sys, os, json, time, logging, re, argparse, tempfile, requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -- Config ---------------------------------------------------------------
AMBIENTE = "1"        # PRODUCAO
IND_APURACAO = "1"    # mensal
GRUPO = "3"           # eventos periodicos

LOTE_SIZE = 50        # max 50 eventos por lote SOAP
PARALLEL_WORKERS = 5  # lotes simultaneos
POLL_DELAY = 5        # seconds between polls
MAX_POLL_RETRIES = 24 # 24 x 5s = 120s max wait
MAX_SEND_RETRIES = 3
SEND_RETRY_DELAY = 5

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
    "name resolution", "temporary failure", "could not translate host name",
]

DB_RETRY_MAX = 5
DB_RETRY_DELAY = 3

# -- Global PEM cache (thread-safe, set once before threads start) --------
_cert_pem_path = None
_key_pem_path = None
_pfx_data = None
_pfx_senha = None


def _setup_pem_cache(pfx_data, senha):
    """Extract PEM files ONCE for reuse across all threads."""
    global _cert_pem_path, _key_pem_path, _pfx_data, _pfx_senha
    _pfx_data = pfx_data
    _pfx_senha = senha

    cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, senha)

    cert_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_turbo_cert.pem")
    cert_file.write(cert_pem)
    cert_file.close()
    _cert_pem_path = cert_file.name

    key_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_turbo_key.pem")
    key_file.write(key_pem)
    key_file.close()
    _key_pem_path = key_file.name


def _cleanup_pem_cache():
    for p in (_cert_pem_path, _key_pem_path):
        if p:
            try:
                os.unlink(p)
            except OSError:
                pass


# -- Direct SOAP calls using cached PEM (no temp file overhead) -----------

def _soap_enviar(soap_envelope, url):
    """Send SOAP using pre-extracted PEM files. No temp file creation."""
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


def _soap_consultar(protocolo, url):
    """Consult using pre-extracted PEM files."""
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


# -- DB helpers -----------------------------------------------------------

def _get_supabase_conn():
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


def _load_s1210_data(per_apur):
    conn = _get_supabase_conn()
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
                ORDER BY e.cpf, e.dt_processamento DESC
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
                    "nr_recibo": row["nr_recibo"],
                    "pagamentos": pagamentos,
                    "infoIRCR": info_ir_cr,
                }
            return list(cpf_map.values())
    finally:
        conn.close()


# -- Batch DB update (single query for N CPFs) ----------------------------

def _batch_update_cpfs(run_id, results_list):
    """
    Update multiple CPFs in a SINGLE query using VALUES + UPDATE FROM.
    results_list: [ (cpf, status, nr_recibo_novo, erro, lote_num), ... ]
    """
    if not results_list:
        return
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            # Build values for batch update
            values = []
            for cpf, status, nr_recibo_novo, erro, lote_num in results_list:
                values.append((run_id, cpf, status, nr_recibo_novo, erro, lote_num))

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


def _db_update_run(run_id, **kwargs):
    conn = _get_supabase_conn()
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


# -- Worker function (runs in thread) -------------------------------------

def _process_one_lote(batch, lote_num, empregador, per_apur, log):
    """
    Process a single lote of 50 CPFs. Thread-safe. Does NOT touch DB.
    Returns: (lote_num, cpf_results_list)
    cpf_results_list: [ (cpf, 'ok'|'erro', nr_recibo_novo, erro_desc, lote_num), ... ]
    """
    thread_name = threading.current_thread().name
    results = []

    try:
        # -- Generate + sign XMLs --
        xmls_assinados = []
        cpf_map = {}  # event_id -> cpf

        for seq_idx, cpf_info in enumerate(batch, start=1):
            info_ir = None
            if cpf_info["infoIRCR"]:
                info_ir = {"infoIRCR": cpf_info["infoIRCR"]}

            xml_bytes = S1210XMLGenerator.gerar(
                empregador=empregador,
                beneficiario={"cpfBenef": cpf_info["cpf"]},
                info_pgtos=cpf_info["pagamentos"],
                per_apur=per_apur,
                ind_retif="2",
                nr_recibo=cpf_info["nr_recibo"],
                info_ir_complem=info_ir,
                seq=seq_idx,
                tp_amb=AMBIENTE,
            )
            signed = XMLSigner.assinar(xml_bytes, _pfx_data, _pfx_senha)
            xmls_assinados.append(signed)

            xml_str = signed.decode("utf-8") if isinstance(signed, bytes) else signed
            id_match = re.search(r'Id="(ID[^"]+)"', xml_str)
            if id_match:
                cpf_map[id_match.group(1)] = cpf_info["cpf"]

        # -- Build and send SOAP --
        soap = SOAPEnvelopeBuilder.montar_envio(
            xmls_assinados, empregador, empregador, grupo=GRUPO
        )

        url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
        resultado = None

        for attempt in range(1, MAX_SEND_RETRIES + 1):
            try:
                resultado = _soap_enviar(soap, url_envio)
                if resultado.get("sucesso"):
                    break
                erro = (resultado.get("descricao") or "").lower()
                is_conn_err = any(kw in erro for kw in CONNECTION_ERRORS)
                if not is_conn_err:
                    break
            except Exception as e:
                resultado = {"sucesso": False, "descricao": str(e), "protocolo": None}
            if attempt < MAX_SEND_RETRIES:
                time.sleep(SEND_RETRY_DELAY * attempt)

        if not resultado or not resultado.get("sucesso"):
            desc = (resultado or {}).get("descricao", "Envio falhou")
            log.error(f"  [W{thread_name}] Lote {lote_num} envio FALHOU: {desc}")
            for ci in batch:
                results.append((ci["cpf"], "erro", None, desc, lote_num))
            return lote_num, results

        protocolo = resultado.get("protocolo")
        if not protocolo:
            for ci in batch:
                results.append((ci["cpf"], "erro", None, "Sem protocolo", lote_num))
            return lote_num, results

        # -- Poll for results --
        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
        consulta = None

        for attempt in range(MAX_POLL_RETRIES):
            time.sleep(POLL_DELAY)
            try:
                consulta = _soap_consultar(protocolo, url_consulta)
            except Exception as e:
                log.warning(f"  [W{thread_name}] Lote {lote_num} poll erro: {e}")
                continue

            if consulta.get("sucesso") and consulta.get("eventos"):
                break
            if consulta.get("codigo_resposta") == "101":
                continue
            if "em processamento" in (consulta.get("descricao") or "").lower():
                continue
            if consulta.get("sucesso") is False:
                break

        # -- Process events --
        if consulta and consulta.get("sucesso") and consulta.get("eventos"):
            eventos = consulta["eventos"]
            matched_cpfs = set()

            for evt in eventos:
                evt_id = evt.get("id", "")
                cpf_matched = cpf_map.get(evt_id)
                nr_recibo = evt.get("nr_recibo")
                cod = evt.get("codigo_resposta", "")

                if nr_recibo and cpf_matched:
                    results.append((cpf_matched, "ok", nr_recibo, None, lote_num))
                    matched_cpfs.add(cpf_matched)
                elif cod and cod not in ("201", "202") and cpf_matched:
                    desc = evt.get("descricao", "")
                    ocorrencias = evt.get("ocorrencias", [])
                    if ocorrencias:
                        desc += " | " + " | ".join(
                            f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                        )
                    results.append((cpf_matched, "erro", None, desc, lote_num))
                    matched_cpfs.add(cpf_matched)

            # Fallback: positional matching for unmatched
            if len(matched_cpfs) < len(batch) and len(eventos) == len(batch):
                for evt, cpf_info in zip(eventos, batch):
                    if cpf_info["cpf"] not in matched_cpfs:
                        nr_recibo = evt.get("nr_recibo")
                        if nr_recibo:
                            results.append((cpf_info["cpf"], "ok", nr_recibo, None, lote_num))
                        else:
                            desc = evt.get("descricao", "sem recibo")
                            results.append((cpf_info["cpf"], "erro", None, desc, lote_num))
                        matched_cpfs.add(cpf_info["cpf"])

            # Any still unmatched = error
            for ci in batch:
                if ci["cpf"] not in matched_cpfs:
                    results.append((ci["cpf"], "erro", None, "Sem resposta no retorno", lote_num))

        else:
            desc = (consulta or {}).get("descricao", "Timeout polling")
            log.error(f"  [W{thread_name}] Lote {lote_num} poll FALHOU: {desc}")

            # Check for partial successes in failed response
            partial_ok = set()
            if consulta and consulta.get("eventos"):
                for evt in consulta["eventos"]:
                    evt_id = evt.get("id", "")
                    cpf_m = cpf_map.get(evt_id)
                    if cpf_m and evt.get("nr_recibo"):
                        results.append((cpf_m, "ok", evt["nr_recibo"], None, lote_num))
                        partial_ok.add(cpf_m)

            for ci in batch:
                if ci["cpf"] not in partial_ok and not any(r[0] == ci["cpf"] for r in results):
                    results.append((ci["cpf"], "erro", None, desc, lote_num))

    except Exception as e:
        log.error(f"  [W{thread_name}] Lote {lote_num} EXCEPTION: {e}")
        already = {r[0] for r in results}
        for ci in batch:
            if ci["cpf"] not in already:
                results.append((ci["cpf"], "erro", None, str(e), lote_num))

    return lote_num, results


# -- Progress tracking ----------------------------------------------------

def _load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            return json.load(f)
    return {"cpfs_ok": [], "cpfs_erro": {}, "s1298_done": False, "s1299_done": False, "run_id": None}


def _save_progress(progress, progress_file):
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2, default=str)


# -- Snapshot S-5002 (reused from pipeline_batch.py) ----------------------

def capturar_snapshot_s5002(per_apur, run_id, tipo, log):
    log.info(f"  Capturando snapshot S-5002 ({tipo}) para {per_apur}...")
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_snapshots (
                    id              SERIAL PRIMARY KEY,
                    run_id          INT,
                    per_apur        VARCHAR(7) NOT NULL,
                    tipo            VARCHAR(10) NOT NULL,
                    cpf             VARCHAR(11) NOT NULL,
                    dados_s5002     JSONB,
                    nr_recibo_s5002 VARCHAR(40),
                    captured_at     TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_run_tipo ON pipeline_snapshots(run_id, tipo)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_cpf_per ON pipeline_snapshots(cpf, per_apur, tipo)")
            conn.commit()

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT ON (cpf) cpf, nr_recibo, dados_json
                FROM explorador_eventos
                WHERE tipo_evento = 'S-5002' AND per_apur = %s AND cpf IS NOT NULL
                ORDER BY cpf, dt_processamento DESC NULLS LAST, id DESC
            """, (per_apur,))
            s5002_rows = cur.fetchall()

        log.info(f"    Encontrados {len(s5002_rows)} CPFs com S-5002")

        with conn.cursor() as cur:
            batch = []
            for row in s5002_rows:
                dados = row["dados_json"] if isinstance(row["dados_json"], dict) else json.loads(row["dados_json"] or "{}")
                batch.append((run_id, per_apur, tipo, row["cpf"], json.dumps(dados), row["nr_recibo"]))
            if batch:
                psycopg2.extras.execute_values(
                    cur,
                    """INSERT INTO pipeline_snapshots
                        (run_id, per_apur, tipo, cpf, dados_s5002, nr_recibo_s5002)
                    VALUES %s""",
                    batch,
                    template="(%s, %s, %s, %s, %s, %s)",
                    page_size=500,
                )
                conn.commit()
        log.info(f"    [OK] Snapshot '{tipo}' salvo: {len(s5002_rows)} registros")
        return len(s5002_rows)
    finally:
        conn.close()


# -- Main Pipeline --------------------------------------------------------

def run_pipeline_turbo(per_apur, workers=PARALLEL_WORKERS):
    per_key = per_apur.replace("-", "")
    progress_file = f"/tmp/pipeline_batch_{per_key}_progress.json"
    result_file = f"/tmp/pipeline_batch_{per_key}_result.json"
    log_file = f"/tmp/pipeline_batch_{per_key}_turbo.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    log = logging.getLogger("turbo_pipeline")

    log.info("=" * 70)
    log.info(f"  PIPELINE BATCH TURBO {per_apur}")
    log.info(f"  {workers} workers paralelos, lotes de {LOTE_SIZE}")
    log.info("=" * 70)

    # -- Load cert --
    cert = _load_cert()
    if not cert:
        log.error("ERRO: Nenhum certificado A1 ativo!")
        sys.exit(1)

    with open(cert["arquivo_path"], "rb") as f:
        pfx_data = f.read()
    senha = cert["senha"]
    cnpj = cert["cnpj"]
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    # -- Setup PEM cache (once, before any threads) --
    _setup_pem_cache(pfx_data, senha)
    log.info("  PEM cache criado (1 extracao para todas as threads)")

    # -- Load S-1210 data --
    log.info("  Carregando dados S-1210...")
    cpf_data = _load_s1210_data(per_apur)
    log.info(f"  {len(cpf_data)} CPFs com S-1210 original")

    if not cpf_data:
        log.error("Nenhum S-1210 encontrado!")
        _cleanup_pem_cache()
        sys.exit(1)

    sem_pgto = [d for d in cpf_data if not d["pagamentos"]]
    if sem_pgto:
        log.warning(f"  {len(sem_pgto)} CPFs sem pagamentos (ignorados)")
        cpf_data = [d for d in cpf_data if d["pagamentos"]]

    # -- Load progress (resume) --
    progress = _load_progress(progress_file)
    run_id = progress.get("run_id")

    if not run_id:
        log.error("ERRO: Nenhum run_id encontrado. Execute pipeline_batch.py primeiro para criar o run.")
        _cleanup_pem_cache()
        sys.exit(1)

    # Get already-processed CPFs from DB
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cpf, status FROM pipeline_cpf_results WHERE run_id=%s AND status IN ('ok','erro')",
                (run_id,)
            )
            rows = cur.fetchall()
            already_done = {row[0] for row in rows}
            prev_ok = sum(1 for row in rows if row[1] == "ok")
            prev_erro = sum(1 for row in rows if row[1] == "erro")
    finally:
        conn.close()

    remaining = [d for d in cpf_data if d["cpf"] not in already_done]
    log.info(f"  Run ID: {run_id}")
    log.info(f"  Ja processados: {len(already_done)} ({prev_ok} ok, {prev_erro} erro)")
    log.info(f"  Restantes: {len(remaining)}")

    if not remaining:
        log.info("  Todos os CPFs ja foram processados!")
        # Check if we need S-1299
        if not progress.get("s1299_done"):
            log.info("  Enviando S-1299 para fechar periodo...")
            # Will do below
        else:
            _cleanup_pem_cache()
            return

    _db_update_run(run_id, status="rodando")

    # -- S-1298 check (should already be done) --
    if not progress.get("s1298_done"):
        log.info("  S-1298 nao foi feito. Execute pipeline_batch.py primeiro.")
        _cleanup_pem_cache()
        sys.exit(1)

    # -- STEP 2: S-1210 retif in parallel waves --
    log.info(f"\n  STEP 2: S-1210 Retificar {len(remaining)} CPFs")
    log.info(f"  {workers} workers paralelos = {workers * LOTE_SIZE} CPFs por wave")
    log.info(f"  Estimativa: {len(remaining) // (workers * LOTE_SIZE) + 1} waves")

    # Split into lotes
    lotes = []
    for i in range(0, len(remaining), LOTE_SIZE):
        lotes.append(remaining[i:i + LOTE_SIZE])

    total_lotes = len(lotes)
    total_ok = 0
    total_erro = 0
    lote_offset = len(already_done) // LOTE_SIZE  # approximate lote numbering

    start_time = time.time()

    # Process in waves of N parallel lotes
    for wave_start in range(0, total_lotes, workers):
        wave_lotes = lotes[wave_start:wave_start + workers]
        wave_num = wave_start // workers + 1
        total_waves = (total_lotes + workers - 1) // workers
        wave_cpf_count = sum(len(l) for l in wave_lotes)

        log.info(f"\n  --- Wave {wave_num}/{total_waves}: {len(wave_lotes)} lotes, {wave_cpf_count} CPFs ---")

        wave_results = []

        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="W") as executor:
            futures = {}
            for idx, batch in enumerate(wave_lotes):
                lote_num = wave_start + idx + 1 + lote_offset
                future = executor.submit(
                    _process_one_lote, batch, lote_num, empregador, per_apur, log
                )
                futures[future] = lote_num

            for future in as_completed(futures):
                try:
                    lote_num_done, cpf_results = future.result(timeout=180)
                    wave_results.extend(cpf_results)

                    ok_count = sum(1 for r in cpf_results if r[1] == "ok")
                    err_count = sum(1 for r in cpf_results if r[1] == "erro")
                    log.info(f"    Lote {lote_num_done}: {ok_count} ok, {err_count} erro")

                except Exception as e:
                    lote_n = futures[future]
                    log.error(f"    Lote {lote_n} EXCEPTION: {e}")
                    # Mark all CPFs in this lote as error
                    batch_for_error = wave_lotes[lote_n - wave_start - 1 - lote_offset] if (lote_n - wave_start - 1 - lote_offset) < len(wave_lotes) else []
                    for ci in batch_for_error:
                        wave_results.append((ci["cpf"], "erro", None, str(e), lote_n))

        # -- Batch DB update for entire wave --
        if wave_results:
            try:
                _batch_update_cpfs(run_id, wave_results)
            except Exception as e:
                log.error(f"    DB batch update falhou: {e}. Tentando individual...")
                # Fallback to individual updates
                conn = _get_supabase_conn()
                try:
                    with conn.cursor() as cur:
                        for cpf, status, recibo, erro, ln in wave_results:
                            cur.execute("""
                                UPDATE pipeline_cpf_results
                                SET status=%s, nr_recibo_novo=%s, erro_descricao=%s,
                                    lote_num=%s, processed_at=NOW()
                                WHERE run_id=%s AND cpf=%s
                            """, (status, recibo, erro, ln, run_id, cpf))
                    conn.commit()
                finally:
                    conn.close()

        # Update progress
        wave_ok = sum(1 for r in wave_results if r[1] == "ok")
        wave_erro = sum(1 for r in wave_results if r[1] == "erro")
        total_ok += wave_ok
        total_erro += wave_erro

        for cpf, status, recibo, erro, ln in wave_results:
            if status == "ok":
                progress["cpfs_ok"].append(cpf)
            else:
                progress["cpfs_erro"][cpf] = erro or "erro"
        _save_progress(progress, progress_file)

        elapsed = time.time() - start_time
        processed = (wave_start + len(wave_lotes)) * LOTE_SIZE
        processed = min(processed, len(remaining))
        speed = processed / elapsed if elapsed > 0 else 0
        eta = (len(remaining) - processed) / speed if speed > 0 else 0

        _db_update_run(run_id, cpfs_ok=prev_ok + total_ok,
                       cpfs_erro=prev_erro + total_erro,
                       lote_atual=wave_start + len(wave_lotes) + lote_offset)

        log.info(f"  Wave {wave_num} pronto: +{wave_ok} ok, +{wave_erro} erro | "
                 f"Total: {total_ok}/{len(remaining)} ok | "
                 f"{speed:.0f} CPFs/s | ETA: {eta/60:.1f} min")

    elapsed_total = time.time() - start_time
    log.info(f"\n  S-1210 retif concluido em {elapsed_total/60:.1f} min: {total_ok} ok, {total_erro} erros")

    # -- STEP 3: S-1299 fechar --
    if not progress.get("s1299_done"):
        log.info(f"\n  STEP 3: S-1299 Fechar {per_apur}")

        if total_erro > 0:
            log.warning(f"  ATENCAO: {total_erro} CPFs com erro. Fechando assim mesmo.")

        try:
            xml = S1299XMLGenerator.gerar(empregador, per_apur, IND_APURACAO, tp_amb=AMBIENTE)
            signed = XMLSigner.assinar(xml, pfx_data, senha)
            soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)

            url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
            resultado = _soap_enviar(soap, url_envio)

            if resultado.get("sucesso"):
                protocolo = resultado.get("protocolo")
                url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
                for _ in range(MAX_POLL_RETRIES):
                    time.sleep(POLL_DELAY)
                    consulta = _soap_consultar(protocolo, url_consulta)
                    if consulta.get("sucesso") and consulta.get("eventos"):
                        recibo = None
                        for e in consulta["eventos"]:
                            if e.get("nr_recibo"):
                                recibo = e["nr_recibo"]
                                break
                        log.info(f"  [OK] S-1299: recibo={recibo}")
                        progress["s1299_done"] = True
                        _db_update_run(run_id, s1299_done=True, s1299_recibo=recibo)
                        break
                    if consulta.get("codigo_resposta") == "101":
                        continue
                    if "em processamento" in (consulta.get("descricao") or "").lower():
                        continue
                    break
                if not progress["s1299_done"]:
                    log.error(f"  S-1299 poll falhou: {consulta.get('descricao')}")
            else:
                log.error(f"  S-1299 envio falhou: {resultado.get('descricao')}")
        except Exception as e:
            log.error(f"  S-1299 ERRO: {e}")

    _save_progress(progress, progress_file)

    # -- Snapshot DEPOIS --
    capturar_snapshot_s5002(per_apur, run_id, "depois", log)

    # -- Final --
    final_ok = prev_ok + total_ok
    final_erro = prev_erro + total_erro
    final_status = "completo" if progress["s1298_done"] and progress["s1299_done"] and final_erro == 0 else "parcial"

    _db_update_run(
        run_id,
        status=final_status,
        cpfs_ok=final_ok,
        cpfs_erro=final_erro,
        finished_at=datetime.now(timezone.utc).isoformat(),
    )

    log.info(f"\n{'=' * 70}")
    log.info("  RESUMO FINAL (TURBO)")
    log.info(f"{'=' * 70}")
    log.info(f"  Periodo: {per_apur}")
    log.info(f"  Run ID: {run_id}")
    log.info(f"  S-1210 retificados: {final_ok}")
    log.info(f"  S-1210 com erro: {final_erro}")
    log.info(f"  S-1298 (reabrir): {'OK' if progress['s1298_done'] else 'FALHOU'}")
    log.info(f"  S-1299 (fechar):  {'OK' if progress['s1299_done'] else 'FALHOU'}")
    log.info(f"  STATUS: {final_status.upper()}")
    log.info(f"  Tempo total TURBO: {elapsed_total/60:.1f} min")
    log.info(f"{'=' * 70}")

    final_result = {
        "run_id": run_id,
        "per_apur": per_apur,
        "status": final_status,
        "total_cpfs": len(cpf_data),
        "cpfs_ok": final_ok,
        "cpfs_erro": final_erro,
        "s1298_done": progress["s1298_done"],
        "s1299_done": progress["s1299_done"],
        "timestamp": datetime.now().isoformat(),
    }
    with open(result_file, "w") as f:
        json.dump(final_result, f, indent=2, default=str)

    _cleanup_pem_cache()
    return final_result


# -- CLI ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pipeline Batch TURBO - S-1210 Retificacao Paralela")
    parser.add_argument("--periodo", required=True, help="Periodo (AAAA-MM)")
    parser.add_argument("--workers", type=int, default=PARALLEL_WORKERS, help="Workers paralelos (default: 5)")
    args = parser.parse_args()

    if not re.match(r"^\d{4}-\d{2}$", args.periodo):
        print(f"ERRO: Periodo invalido: {args.periodo}")
        sys.exit(1)

    run_pipeline_turbo(args.periodo, workers=args.workers)


if __name__ == "__main__":
    main()
