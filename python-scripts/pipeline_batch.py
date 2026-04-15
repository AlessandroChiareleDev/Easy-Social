"""
Pipeline Batch GENÉRICO — Retificação S-1210 em massa.
═══════════════════════════════════════════════════════
Versão parametrizada do pipeline_batch_set2025.py.
Aceita --periodo como argumento de linha de comando.

Uso:
  python pipeline_batch.py --periodo 2025-01
  python pipeline_batch.py --periodo 2025-02 --dry-run

Fluxo:
  1. S-1298   — Reabrir período (1x, empregador)
  2. S-1210   — Retificar TODOS os CPFs (lotes de 50)
  3. S-1299   — Fechar período (1x, empregador)

Lê dados do explorador_eventos (Supabase) e certificado do PG local.
Grava progresso em pipeline_runs / pipeline_cpf_results (Supabase).
Roda na VPS: python3 pipeline_batch.py --periodo 2025-01
"""

import sys, os, json, time, logging, re, argparse
from datetime import datetime, timezone

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

# ── Config ────────────────────────────────────────────────────
AMBIENTE = "1"        # PRODUÇÃO
IND_APURACAO = "1"    # mensal
GRUPO = "3"           # eventos periódicos

LOTE_SIZE = 50        # max 50 eventos por lote SOAP
MAX_POLL_RETRIES = 24
POLL_DELAY = 5        # seconds (reduced from 15 for speed)
MAX_SEND_RETRIES = 5
SEND_RETRY_DELAY = 10 # seconds

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
    "name resolution", "temporary failure", "could not translate host name",
]

DB_RETRY_MAX = 5
DB_RETRY_DELAY = 5  # seconds


def _setup_paths(per_apur: str):
    """Define caminhos de arquivos baseado no período."""
    per_key = per_apur.replace("-", "")
    return {
        "progress": f"/tmp/pipeline_batch_{per_key}_progress.json",
        "result": f"/tmp/pipeline_batch_{per_key}_result.json",
        "log": f"/tmp/pipeline_batch_{per_key}.log",
    }


def _setup_logging(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return logging.getLogger("batch_pipeline")


# ── DB helpers ────────────────────────────────────────────────

def _get_supabase_conn():
    for attempt in range(1, DB_RETRY_MAX + 1):
        try:
            return psycopg2.connect(
                **DB_CONFIG,
                keepalives=1, keepalives_idle=30,
                keepalives_interval=10, keepalives_count=3,
            )
        except psycopg2.OperationalError as e:
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


def _load_s1210_data(per_apur: str) -> list[dict]:
    """
    Carrega todos os S-1210 originais (indRetif != '2') do período.
    Retorna lista de dicts: cpf, nr_recibo, pagamentos[], infoIRCR[].
    """
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


def _load_plansaude_map(per_apur: str) -> dict:
    """
    Carrega mapa CPF → vlrSaudeTit de arquivo JSON pré-extraído.
    Arquivo esperado: plansaude_map_{per_apur}.json (ex: plansaude_map_jan2025.json)
    Fallback: tenta DB (explorador_rubricas).
    Retorna dict: {cpf: vlrSaudeTit (str)}
    """
    # Tentar carregar de JSON primeiro
    per_label = {
        "2025-01": "jan2025", "2025-02": "fev2025", "2025-03": "mar2025",
        "2025-09": "set2025", "2025-10": "out2025",
    }.get(per_apur, per_apur.replace("-", ""))
    json_path = os.path.join(os.path.dirname(__file__), f"plansaude_map_{per_label}.json")

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            raw = json.load(f)
        # Valores vêm como float no JSON, converter para str
        return {cpf: str(vlr) for cpf, vlr in raw.items()}

    # Fallback: DB
    conn = _get_supabase_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT e.cpf, r.cod_rubr, r.vr_rubr
                FROM explorador_eventos e
                JOIN explorador_rubricas r ON r.evento_id = e.id
                WHERE e.tipo_evento = 'S-1200'
                  AND e.per_apur = %s
                  AND r.cod_rubr IN ('607', '774', '775')
                ORDER BY e.cpf
            """, (per_apur,))
            rows = cur.fetchall()

        PRIORITY = {'607': 0, '774': 1, '775': 2}
        cpf_best = {}
        for row in rows:
            cpf = row["cpf"]
            rubr = str(row["cod_rubr"]).strip()
            vlr = str(row["vr_rubr"]).strip()
            prio = PRIORITY.get(rubr, 99)
            if cpf not in cpf_best or prio < cpf_best[cpf][0]:
                cpf_best[cpf] = (prio, vlr)

        return {cpf: vlr for cpf, (_, vlr) in cpf_best.items()}
    finally:
        conn.close()


def _load_error_cpfs(per_apur: str) -> tuple:
    """
    Retorna (set de CPFs cujo resultado mais recente é 'erro', dict cpf→erro_descricao).
    Olha TODOS os runs do período e pega o status mais recente de cada CPF.
    """
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sub.cpf, sub.erro_descricao FROM (
                    SELECT DISTINCT ON (r.cpf) r.cpf, r.status, r.erro_descricao
                    FROM pipeline_cpf_results r
                    JOIN pipeline_runs p ON p.id = r.run_id
                    WHERE p.per_apur = %s
                    ORDER BY r.cpf, p.id DESC
                ) sub
                WHERE sub.status = 'erro'
            """, (per_apur,))
            rows = cur.fetchall()
            cpf_set = {row[0] for row in rows}
            cpf_errors = {row[0]: (row[1] or "") for row in rows}
            return cpf_set, cpf_errors
    finally:
        conn.close()


CNPJ_OPERADORA = "63554067000198"
REG_ANS = "368253"


# ── SOAP helpers ──────────────────────────────────────────────

def _is_connection_error(resultado):
    if resultado.get("sucesso"):
        return False
    erro = (resultado.get("erro") or resultado.get("descricao") or "").lower()
    return any(kw in erro for kw in CONNECTION_ERRORS)


def _enviar_e_consultar(soap_envelope, pfx_data, senha, is_producao, log):
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
    resultado = None

    for attempt in range(1, MAX_SEND_RETRIES + 1):
        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha, url=url_envio)
        if resultado.get("sucesso") or not _is_connection_error(resultado):
            break
        log.warning(f"  [RETRY] Tentativa {attempt}/{MAX_SEND_RETRIES} falhou (conexão)")
        if attempt < MAX_SEND_RETRIES:
            time.sleep(SEND_RETRY_DELAY * attempt)
        else:
            return {"sucesso": False, "protocolo": None, "eventos": [],
                    "descricao": f"Conexão falhou após {MAX_SEND_RETRIES} tentativas"}

    if not resultado.get("sucesso"):
        return {
            "sucesso": False,
            "protocolo": resultado.get("protocolo"),
            "eventos": [],
            "codigo_resposta": resultado.get("codigo_resposta"),
            "descricao": resultado.get("descricao") or resultado.get("erro"),
        }

    protocolo = resultado.get("protocolo")
    if not protocolo:
        return {"sucesso": False, "protocolo": None, "eventos": [],
                "descricao": "Sem protocolo no retorno"}

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
    consulta = None

    for attempt in range(MAX_POLL_RETRIES):
        time.sleep(POLL_DELAY)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

        if _is_connection_error(consulta):
            log.warning(f"  [POLL-RETRY] Tentativa {attempt+1}/{MAX_POLL_RETRIES}")
            continue

        if consulta.get("sucesso") and consulta.get("eventos"):
            return {
                "sucesso": True,
                "protocolo": protocolo,
                "eventos": consulta["eventos"],
                "codigo_resposta": consulta.get("codigo_resposta"),
                "descricao": consulta.get("descricao"),
            }
        elif consulta.get("codigo_resposta") == "101":
            continue
        elif "em processamento" in (consulta.get("descricao") or "").lower():
            continue
        elif consulta.get("sucesso") is False:
            break

    return {
        "sucesso": False,
        "protocolo": protocolo,
        "eventos": consulta.get("eventos", []) if consulta else [],
        "codigo_resposta": consulta.get("codigo_resposta") if consulta else None,
        "descricao": consulta.get("descricao") if consulta else None,
    }


def _enviar_evento_unico(xml_bytes, pfx_data, senha, empregador, is_producao, log):
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)
    return _enviar_e_consultar(soap, pfx_data, senha, is_producao, log)


# ── Progress tracking ─────────────────────────────────────────

def _load_progress(progress_file) -> dict:
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            return json.load(f)
    return {"cpfs_ok": [], "cpfs_erro": {}, "s1298_done": False, "s1299_done": False, "run_id": None}


def _save_progress(progress, progress_file):
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2, default=str)


def _db_create_run(per_apur, total_cpfs, total_lotes):
    conn = _get_supabase_conn()
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


def _db_insert_cpfs(run_id, cpf_data):
    conn = _get_supabase_conn()
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


# Shared connection for batch updates (avoids creating new connection per CPF)
_shared_conn = None

def _get_shared_conn():
    global _shared_conn
    if _shared_conn is None or _shared_conn.closed:
        _shared_conn = _get_supabase_conn()
    return _shared_conn


def _db_update_cpf(run_id, cpf, status, nr_recibo_novo=None, erro=None, lote_num=None):
    for attempt in range(1, DB_RETRY_MAX + 1):
        try:
            conn = _get_shared_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pipeline_cpf_results
                    SET status = %s, nr_recibo_novo = %s, erro_descricao = %s,
                        lote_num = %s, processed_at = NOW()
                    WHERE run_id = %s AND cpf = %s
                """, (status, nr_recibo_novo, erro, lote_num, run_id, cpf))
            conn.commit()
            return
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            global _shared_conn
            _shared_conn = None
            if attempt < DB_RETRY_MAX:
                time.sleep(DB_RETRY_DELAY)
            else:
                raise


def _db_update_run(run_id, **kwargs):
    for attempt in range(1, DB_RETRY_MAX + 1):
        try:
            conn = _get_shared_conn()
            sets = []
            vals = []
            for k, v in kwargs.items():
                sets.append(f"{k} = %s")
                vals.append(v)
            vals.append(run_id)
            with conn.cursor() as cur:
                cur.execute(f"UPDATE pipeline_runs SET {', '.join(sets)} WHERE id = %s", vals)
            conn.commit()
            return
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            global _shared_conn
            _shared_conn = None
            if attempt < DB_RETRY_MAX:
                time.sleep(DB_RETRY_DELAY)
            else:
                raise


# ── Snapshot S-5002 ───────────────────────────────────────────

def capturar_snapshot_s5002(per_apur: str, run_id: int, tipo: str, log):
    """
    Captura estado S-5002 (Totalizador IRRF) de TODOS os CPFs de um período.
    tipo: 'antes' ou 'depois'
    Salva em pipeline_snapshots.
    """
    log.info(f"  Capturando snapshot S-5002 ({tipo}) para {per_apur}...")
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            # Criar tabela se não existe
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
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_run_tipo
                ON pipeline_snapshots(run_id, tipo)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_cpf_per
                ON pipeline_snapshots(cpf, per_apur, tipo)
            """)
            conn.commit()

        # Buscar S-5002 mais recente por CPF para o período
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT ON (cpf)
                    cpf, nr_recibo, dados_json
                FROM explorador_eventos
                WHERE tipo_evento = 'S-5002'
                  AND per_apur = %s
                  AND cpf IS NOT NULL
                ORDER BY cpf, dt_processamento DESC NULLS LAST, id DESC
            """, (per_apur,))
            s5002_rows = cur.fetchall()

        log.info(f"    Encontrados {len(s5002_rows)} CPFs com S-5002 em {per_apur}")

        # Inserir em lote
        with conn.cursor() as cur:
            batch = []
            for row in s5002_rows:
                dados = row["dados_json"] if isinstance(row["dados_json"], dict) else json.loads(row["dados_json"] or "{}")
                batch.append((
                    run_id, per_apur, tipo, row["cpf"],
                    json.dumps(dados), row["nr_recibo"]
                ))

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

        log.info(f"    ✓ Snapshot '{tipo}' salvo: {len(s5002_rows)} registros")
        return len(s5002_rows)

    finally:
        conn.close()


# ── Main Pipeline ─────────────────────────────────────────────

def run_pipeline(per_apur: str, dry_run: bool = False, no_close: bool = False,
                 fix_errors: bool = False, no_snapshot: bool = False,
                 send_original: bool = False):
    paths = _setup_paths(per_apur)
    log = _setup_logging(paths["log"])

    mode_tags = []
    if dry_run: mode_tags.append("DRY RUN")
    if fix_errors: mode_tags.append("FIX-ERRORS")
    if no_close: mode_tags.append("SEM FECHAR")
    if no_snapshot: mode_tags.append("SEM SNAPSHOT")
    if send_original: mode_tags.append("SEND-ORIGINAL")
    mode_str = " | ".join(mode_tags) if mode_tags else "PRODUÇÃO"

    s1210_label = "S-1210 ORIGINAL" if send_original else "S-1210 retif"
    fluxo = f"S-1298 -> {s1210_label} (lotes de {LOTE_SIZE})"
    if not no_close:
        fluxo += " -> S-1299"

    log.info("=" * 70)
    log.info(f"  PIPELINE BATCH {per_apur} — {mode_str}")
    log.info(f"  Fluxo: {fluxo}")
    log.info("=" * 70)

    # ── Carregar certificado ──
    cert = _load_cert()
    if not cert:
        log.error("ERRO: Nenhum certificado A1 ativo!")
        sys.exit(1)

    with open(cert["arquivo_path"], "rb") as f:
        pfx_data = f.read()
    senha = cert["senha"]
    cnpj = cert["cnpj"]
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    is_producao = (AMBIENTE == "1") and not dry_run

    # ── Carregar dados S-1210 do explorador ──
    log.info("Carregando dados S-1210 do explorador...")
    cpf_data = _load_s1210_data(per_apur)
    log.info(f"  {len(cpf_data)} CPFs com S-1210 original em {per_apur}")

    if not cpf_data:
        log.error("Nenhum S-1210 encontrado! Verifique se os XMLs foram importados.")
        sys.exit(1)

    sem_pgto = [d for d in cpf_data if not d["pagamentos"]]
    if sem_pgto:
        log.warning(f"  {len(sem_pgto)} CPFs sem pagamentos — serão IGNORADOS")
        cpf_data = [d for d in cpf_data if d["pagamentos"]]
        log.info(f"  {len(cpf_data)} CPFs válidos para retificação")

    # ── --send-original: filtrar apenas CPFs com erro de recibo (S-1210 excluído) ──
    if send_original:
        error_cpfs, cpf_error_msgs = _load_error_cpfs(per_apur)
        recibo_cpfs = {cpf for cpf, msg in cpf_error_msgs.items()
                       if "recibo" in msg.lower() or "duplicidade" in msg.lower()}
        log.info(f"  [SEND-ORIGINAL] {len(recibo_cpfs)} CPFs com erro de recibo/duplicidade (S-1210 excluído)")
        cpf_data = [d for d in cpf_data if d["cpf"] in recibo_cpfs]
        log.info(f"  [SEND-ORIGINAL] {len(cpf_data)} CPFs encontrados no explorador")
        # Clear progress file to start fresh
        if os.path.exists(paths["progress"]):
            os.remove(paths["progress"])

    # ── --fix-errors: filtrar apenas CPFs com erro do último run ──
    elif fix_errors:
        error_cpfs, cpf_error_msgs = _load_error_cpfs(per_apur)
        log.info(f"  [FIX-ERRORS] {len(error_cpfs)} CPFs com erro (último status de cada CPF)")
        cpf_data = [d for d in cpf_data if d["cpf"] in error_cpfs]
        log.info(f"  [FIX-ERRORS] {len(cpf_data)} CPFs encontrados no explorador para fix")
        # Clear progress file to start fresh
        if os.path.exists(paths["progress"]):
            os.remove(paths["progress"])

    # ── Carregar mapa planSaude (vlrSaudeTit por CPF) ──
    log.info("Carregando mapa planSaude do explorador...")
    plansaude_map = _load_plansaude_map(per_apur)
    log.info(f"  {len(plansaude_map)} CPFs com dados de planSaude")

    # Se fix_errors, filtrar CPFs: pular apenas os que tiveram erro de planSaude E não têm dados
    # CPFs com outros erros (recibo, timeout) passam mesmo sem planSaude
    if fix_errors and plansaude_map:
        before = len(cpf_data)
        filtered = []
        skipped_ps = 0
        for d in cpf_data:
            err_msg = cpf_error_msgs.get(d["cpf"], "").lower()
            is_plansaude_err = "plano" in err_msg
            has_plansaude = d["cpf"] in plansaude_map
            if is_plansaude_err and not has_plansaude:
                skipped_ps += 1
            else:
                filtered.append(d)
        cpf_data = filtered
        if skipped_ps:
            log.info(f"  [FIX-ERRORS] Filtrando: {len(cpf_data)} CPFs para processar, {skipped_ps} com erro planSaude sem dados (pulados)")

    if dry_run:
        plan_com = sum(1 for d in cpf_data if d["cpf"] in plansaude_map)
        log.info(f"\n  [DRY RUN] {len(cpf_data)} CPFs seriam retificados ({plan_com} com planSaude). Nenhum evento enviado.")
        return {"per_apur": per_apur, "total_cpfs": len(cpf_data), "with_plansaude": plan_com, "dry_run": True}

    total_lotes = (len(cpf_data) + LOTE_SIZE - 1) // LOTE_SIZE

    # ── Load progress (resume) ──
    progress = _load_progress(paths["progress"])
    already_done = set(progress["cpfs_ok"])

    run_id = progress.get("run_id")

    if not run_id:
        run_id = _db_create_run(per_apur, len(cpf_data), total_lotes)
        progress["run_id"] = run_id
        _save_progress(progress, paths["progress"])
        log.info(f"  DB run criado: id={run_id}")
        _db_insert_cpfs(run_id, cpf_data)
        log.info(f"  {len(cpf_data)} CPFs inseridos como pendente")

        # ── SNAPSHOT ANTES ──
        if not no_snapshot:
            capturar_snapshot_s5002(per_apur, run_id, "antes", log)
        else:
            log.info("  [SEM SNAPSHOT] Pulando snapshot ANTES")
    else:
        try:
            conn = _get_supabase_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT cpf FROM pipeline_cpf_results WHERE run_id=%s AND status IN ('ok','erro')",
                        (run_id,)
                    )
                    db_done = {row[0] for row in cur.fetchall()}
                    already_done |= db_done
                    log.info(f"  DB: {len(db_done)} CPFs já processados")
            finally:
                conn.close()
        except Exception as e:
            log.warning(f"  Não foi possível checar DB para resume: {e}")
        log.info(f"  Resumindo run_id={run_id}: {len(already_done)} já processados, {len(cpf_data) - len(already_done)} restantes")
        _db_update_run(run_id, status="rodando")

    remaining = [d for d in cpf_data if d["cpf"] not in already_done]

    # ════════════════════════════════════════════════════════════
    # STEP 1: S-1298 — Reabrir período
    # ════════════════════════════════════════════════════════════
    if not progress["s1298_done"]:
        log.info(f"\n{'─'*60}")
        log.info(f"  STEP 1: S-1298 Reabrir {per_apur}")
        log.info(f"{'─'*60}")
        try:
            xml = S1298XMLGenerator.gerar(empregador, per_apur, IND_APURACAO, tp_amb=AMBIENTE)
            result = _enviar_evento_unico(xml, pfx_data, senha, empregador, is_producao, log)

            already_open = (
                not result["sucesso"]
                and result.get("descricao")
                and any(kw in result["descricao"].lower() for kw in [
                    "já se encontra", "já está abert", "[715]", "período já"
                ])
            )
            if already_open:
                result["sucesso"] = True
                result["descricao"] = f"[JÁ ABERTO] {result['descricao']}"

            if result["sucesso"]:
                log.info(f"  ✓ S-1298: {result.get('descricao', 'OK')}")
                progress["s1298_done"] = True
                _save_progress(progress, paths["progress"])
                recibo_1298 = None
                for e in result.get("eventos", []):
                    if e.get("nr_recibo"):
                        recibo_1298 = e["nr_recibo"]
                        break
                _db_update_run(run_id, s1298_done=True, s1298_recibo=recibo_1298)
            else:
                log.error(f"  ✗ S-1298 FALHOU: {result.get('descricao')}")
                _db_update_run(run_id, status="erro", erro_fatal=f"S-1298 falhou: {result.get('descricao')}")
                sys.exit(1)
        except Exception as e:
            log.error(f"  ✗ S-1298 ERRO: {e}")
            _db_update_run(run_id, status="erro", erro_fatal=f"S-1298 exception: {e}")
            sys.exit(1)
    else:
        log.info("  STEP 1: S-1298 já executado (resumindo)")

    # ════════════════════════════════════════════════════════════
    # STEP 2: S-1210 — Enviar para todos os CPFs em lotes
    # ════════════════════════════════════════════════════════════
    log.info(f"\n{'─'*60}")
    log.info(f"  STEP 2: {s1210_label} — {len(remaining)} CPFs em lotes de {LOTE_SIZE}")
    log.info(f"{'─'*60}")

    total_lotes_remaining = (len(remaining) + LOTE_SIZE - 1) // LOTE_SIZE
    cpfs_ok = 0
    cpfs_erro = 0

    for lote_idx in range(0, len(remaining), LOTE_SIZE):
        batch = remaining[lote_idx:lote_idx + LOTE_SIZE]
        lote_num = (lote_idx // LOTE_SIZE) + 1
        log.info(f"\n  Lote {lote_num}/{total_lotes_remaining} — {len(batch)} CPFs")

        _db_update_run(run_id, lote_atual=lote_num, cpfs_ok=len(progress["cpfs_ok"]),
                       cpfs_erro=len(progress["cpfs_erro"]))

        xmls_assinados = []
        batch_cpf_map = {}
        try:
            for seq_idx, cpf_info in enumerate(batch, start=1):
                info_ir_complem = None
                if cpf_info["infoIRCR"]:
                    info_ir_complem = {"infoIRCR": cpf_info["infoIRCR"]}

                # planSaude injection
                plan_saude = None
                vlr = plansaude_map.get(cpf_info["cpf"])
                if vlr:
                    plan_saude = {
                        "cnpjOper": CNPJ_OPERADORA,
                        "regANS": REG_ANS,
                        "vlrSaudeTit": vlr,
                    }

                # send-original: envia como original (indRetif=1), sem nrRecibo
                _ind_retif = "1" if send_original else "2"
                _nr_recibo = None if send_original else cpf_info["nr_recibo"]

                xml_bytes = S1210XMLGenerator.gerar(
                    empregador=empregador,
                    beneficiario={"cpfBenef": cpf_info["cpf"]},
                    info_pgtos=cpf_info["pagamentos"],
                    per_apur=per_apur,
                    ind_retif=_ind_retif,
                    nr_recibo=_nr_recibo,
                    info_ir_complem=info_ir_complem,
                    plan_saude=plan_saude,
                    seq=seq_idx,
                    tp_amb=AMBIENTE,
                )
                signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
                xmls_assinados.append(signed)

                xml_str = signed.decode("utf-8") if isinstance(signed, bytes) else signed
                id_match = re.search(r'Id="(ID[^"]+)"', xml_str)
                if id_match:
                    batch_cpf_map[id_match.group(1)] = cpf_info["cpf"]

        except Exception as e:
            log.error(f"  ✗ Erro ao gerar XMLs do lote {lote_num}: {e}")
            for ci in batch:
                progress["cpfs_erro"][ci["cpf"]] = str(e)
                cpfs_erro += 1
                _db_update_cpf(run_id, ci["cpf"], "erro", erro=str(e), lote_num=lote_num)
            _save_progress(progress, paths["progress"])
            continue

        soap = SOAPEnvelopeBuilder.montar_envio(
            xmls_assinados, empregador, empregador, grupo=GRUPO
        )

        result = _enviar_e_consultar(soap, pfx_data, senha, is_producao, log)

        if result["sucesso"] and result["eventos"]:
            eventos = result["eventos"]
            for evt in eventos:
                evt_id = evt.get("id", "")
                cpf_matched = batch_cpf_map.get(evt_id)
                nr_recibo = evt.get("nr_recibo")
                cod = evt.get("codigo_resposta", "")

                if nr_recibo:
                    if cpf_matched:
                        progress["cpfs_ok"].append(cpf_matched)
                        cpfs_ok += 1
                        log.info(f"    ✓ CPF {cpf_matched}: recibo={nr_recibo}")
                        _db_update_cpf(run_id, cpf_matched, "ok", nr_recibo_novo=nr_recibo, lote_num=lote_num)
                elif cod and cod not in ("201", "202"):
                    desc = evt.get("descricao", "")
                    ocorrencias = evt.get("ocorrencias", [])
                    if ocorrencias:
                        desc += " | " + " | ".join(
                            f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                        )
                    if cpf_matched:
                        progress["cpfs_erro"][cpf_matched] = desc
                        cpfs_erro += 1
                        log.warning(f"    ✗ CPF {cpf_matched}: [{cod}] {desc}")
                        _db_update_cpf(run_id, cpf_matched, "erro", erro=desc, lote_num=lote_num)

            matched_cpfs = set()
            for evt in eventos:
                evt_id = evt.get("id", "")
                m = batch_cpf_map.get(evt_id)
                if m:
                    matched_cpfs.add(m)

            if len(matched_cpfs) < len(batch) and len(eventos) == len(batch):
                for i, (evt, cpf_info) in enumerate(zip(eventos, batch)):
                    if cpf_info["cpf"] not in matched_cpfs:
                        nr_recibo = evt.get("nr_recibo")
                        if nr_recibo:
                            progress["cpfs_ok"].append(cpf_info["cpf"])
                            cpfs_ok += 1
                            log.info(f"    ✓ CPF {cpf_info['cpf']} (pos): recibo={nr_recibo}")
                            _db_update_cpf(run_id, cpf_info["cpf"], "ok", nr_recibo_novo=nr_recibo, lote_num=lote_num)
                        else:
                            desc = evt.get("descricao", "sem recibo")
                            progress["cpfs_erro"][cpf_info["cpf"]] = desc
                            cpfs_erro += 1
                            log.warning(f"    ✗ CPF {cpf_info['cpf']} (pos): {desc}")
                            _db_update_cpf(run_id, cpf_info["cpf"], "erro", erro=desc, lote_num=lote_num)
        else:
            desc = result.get("descricao", "Erro desconhecido")
            log.error(f"  ✗ Lote {lote_num} FALHOU: {desc}")

            for evt in result.get("eventos", []):
                evt_id = evt.get("id", "")
                cpf_matched = batch_cpf_map.get(evt_id)
                nr_recibo = evt.get("nr_recibo")
                if nr_recibo and cpf_matched:
                    progress["cpfs_ok"].append(cpf_matched)
                    cpfs_ok += 1
                    log.info(f"    ✓ CPF {cpf_matched} (partial): recibo={nr_recibo}")
                    _db_update_cpf(run_id, cpf_matched, "ok", nr_recibo_novo=nr_recibo, lote_num=lote_num)

            ok_cpfs = set(progress["cpfs_ok"])
            for ci in batch:
                if ci["cpf"] not in ok_cpfs and ci["cpf"] not in progress["cpfs_erro"]:
                    progress["cpfs_erro"][ci["cpf"]] = desc
                    cpfs_erro += 1
                    _db_update_cpf(run_id, ci["cpf"], "erro", erro=desc, lote_num=lote_num)

        _save_progress(progress, paths["progress"])
        _db_update_run(run_id, cpfs_ok=len(progress["cpfs_ok"]), cpfs_erro=len(progress["cpfs_erro"]),
                       lote_atual=lote_num)
        log.info(f"  Lote {lote_num} concluído: OK={cpfs_ok}, Erro={cpfs_erro}, "
                 f"Total processado={cpfs_ok + cpfs_erro}/{len(cpf_data)}")

    log.info(f"\n  S-1210 retif concluído: {cpfs_ok} OK, {cpfs_erro} erros")

    # ════════════════════════════════════════════════════════════
    # STEP 3: S-1299 — Fechar período
    # ════════════════════════════════════════════════════════════
    if no_close:
        log.info(f"\n{'─'*60}")
        log.info(f"  STEP 3: S-1299 PULADO (--no-close)")
        log.info(f"{'─'*60}")
    elif not progress["s1299_done"]:
        log.info(f"\n{'─'*60}")
        log.info(f"  STEP 3: S-1299 Fechar {per_apur}")
        log.info(f"{'─'*60}")

        if cpfs_erro > 0:
            log.warning(f"  ATENÇÃO: {cpfs_erro} CPFs com erro. Fechando assim mesmo.")

        try:
            xml = S1299XMLGenerator.gerar(empregador, per_apur, IND_APURACAO, tp_amb=AMBIENTE)
            result = _enviar_evento_unico(xml, pfx_data, senha, empregador, is_producao, log)

            if result["sucesso"]:
                log.info(f"  ✓ S-1299: {result.get('descricao', 'OK')}")
                recibo_1299 = None
                for e in result.get("eventos", []):
                    if e.get("nr_recibo"):
                        recibo_1299 = e["nr_recibo"]
                        log.info(f"    Recibo: {recibo_1299}")
                        break
                progress["s1299_done"] = True
                _db_update_run(run_id, s1299_done=True, s1299_recibo=recibo_1299)
            else:
                log.error(f"  ✗ S-1299 FALHOU: {result.get('descricao')}")
        except Exception as e:
            log.error(f"  ✗ S-1299 ERRO: {e}")
    else:
        log.info("  STEP 3: S-1299 já executado")

    _save_progress(progress, paths["progress"])

    # ── SNAPSHOT DEPOIS ──
    if not no_snapshot:
        capturar_snapshot_s5002(per_apur, run_id, "depois", log)
    else:
        log.info("  [SEM SNAPSHOT] Pulando snapshot DEPOIS")

    # ═══════════════ RESUMO FINAL ═══════════════
    final_status = "completo" if (
        progress["s1298_done"]
        and progress["s1299_done"]
        and len(progress["cpfs_erro"]) == 0
    ) else "parcial"

    _db_update_run(
        run_id,
        status=final_status,
        cpfs_ok=len(progress["cpfs_ok"]),
        cpfs_erro=len(progress["cpfs_erro"]),
        finished_at=datetime.now(timezone.utc).isoformat(),
    )

    log.info(f"\n{'='*70}")
    log.info("  RESUMO FINAL")
    log.info(f"{'='*70}")
    log.info(f"  Período: {per_apur}")
    log.info(f"  Run ID: {run_id}")
    log.info(f"  Total CPFs: {len(cpf_data)}")
    log.info(f"  S-1210 retificados: {len(progress['cpfs_ok'])}")
    log.info(f"  S-1210 com erro: {len(progress['cpfs_erro'])}")
    log.info(f"  S-1298 (reabrir): {'✓' if progress['s1298_done'] else '✗'}")
    log.info(f"  S-1299 (fechar):  {'✓' if progress['s1299_done'] else '✗'}")
    log.info(f"  STATUS: {final_status.upper()}")
    log.info(f"{'='*70}")

    final_result = {
        "run_id": run_id,
        "per_apur": per_apur,
        "status": final_status,
        "total_cpfs": len(cpf_data),
        "cpfs_ok": len(progress["cpfs_ok"]),
        "cpfs_erro": len(progress["cpfs_erro"]),
        "s1298_done": progress["s1298_done"],
        "s1299_done": progress["s1299_done"],
        "erros_detalhe": progress["cpfs_erro"],
        "timestamp": datetime.now().isoformat(),
    }
    with open(paths["result"], "w") as f:
        json.dump(final_result, f, indent=2, default=str)
    log.info(f"\nResultado salvo em {paths['result']}")

    return final_result


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pipeline Batch S-1210 — Retificação em massa")
    parser.add_argument("--periodo", required=True, help="Período (AAAA-MM), ex: 2025-01")
    parser.add_argument("--dry-run", action="store_true", help="Só conta CPFs, não envia nada")
    parser.add_argument("--no-close", action="store_true", help="NÃO envia S-1299 (não fecha o período)")
    parser.add_argument("--fix-errors", action="store_true", help="Reprocessar APENAS CPFs com erro do último run")
    parser.add_argument("--no-snapshot", action="store_true", help="Pular snapshots S-5002 (mais rápido)")
    parser.add_argument("--send-original", action="store_true", help="Enviar S-1210 como ORIGINAL (indRetif=1) para CPFs cujo S-1210 foi excluído (S-3000)")
    args = parser.parse_args()

    # Validar formato
    if not re.match(r"^\d{4}-\d{2}$", args.periodo):
        print(f"ERRO: Período inválido: {args.periodo}. Use formato AAAA-MM")
        sys.exit(1)

    run_pipeline(
        args.periodo,
        dry_run=args.dry_run,
        no_close=args.no_close,
        fix_errors=args.fix_errors,
        no_snapshot=args.no_snapshot,
        send_original=args.send_original,
    )


if __name__ == "__main__":
    main()
