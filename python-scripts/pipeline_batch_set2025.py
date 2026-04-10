"""
Pipeline Batch Setembro 2025 — Retificação S-1210 em massa.

Fluxo:
  1. S-1298   — Reabrir período 2025-09 (1x, empregador)
  2. S-1210   — Retificar TODOS os CPFs (lotes de 50)
  3. S-1299   — Fechar período 2025-09 (1x, empregador)

Lê dados do explorador_eventos (Supabase) e certificado do PG local.
Grava progresso em pipeline_runs / pipeline_cpf_results (Supabase).
Roda na VPS: python3 pipeline_batch_set2025.py
"""

import sys, os, json, time, logging, re
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
PER_APUR = "2025-09"
AMBIENTE = "1"        # PRODUÇÃO
IND_APURACAO = "1"    # mensal
GRUPO = "3"           # eventos periódicos

LOTE_SIZE = 50        # max 50 eventos por lote SOAP
MAX_POLL_RETRIES = 8
POLL_DELAY = 15       # seconds
MAX_SEND_RETRIES = 5
SEND_RETRY_DELAY = 10 # seconds

# Resume: skip CPFs already processed (saved in progress file)
PROGRESS_FILE = f"/tmp/pipeline_batch_{PER_APUR.replace('-','')}_progress.json"
RESULT_FILE = f"/tmp/pipeline_batch_{PER_APUR.replace('-','')}_result.json"

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
]

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"/tmp/pipeline_batch_{PER_APUR.replace('-','')}.log"),
    ],
)
log = logging.getLogger("batch_pipeline")


# ── DB helpers ────────────────────────────────────────────────

def _get_supabase_conn():
    return psycopg2.connect(
        **DB_CONFIG,
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3,
    )


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
    Se um CPF tiver múltiplos S-1210 originais, prioriza o mais recente.
    """
    conn = _get_supabase_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    e.cpf,
                    e.nr_recibo,
                    e.dados_json,
                    e.dt_processamento
                FROM explorador_eventos e
                WHERE e.tipo_evento = 'S-1210'
                  AND e.per_apur = %s
                  AND e.cpf IS NOT NULL
                  AND e.nr_recibo IS NOT NULL
                  AND COALESCE(e.dados_json->>'indRetif', '1') != '2'
                ORDER BY e.cpf, e.dt_processamento DESC
            """, (per_apur,))
            rows = cur.fetchall()

            # Group by CPF — keep most recent per CPF
            cpf_map = {}
            for row in rows:
                cpf = row["cpf"]
                if cpf in cpf_map:
                    continue  # already have the most recent (ORDER BY DESC)
                dados = row["dados_json"] if isinstance(row["dados_json"], dict) else json.loads(row["dados_json"] or "{}")

                pagamentos = dados.get("pagamentos", [])
                if not pagamentos:
                    # Backwards compat: reconstruct from flat fields
                    if dados.get("dtPgto"):
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


# ── SOAP helpers ──────────────────────────────────────────────

def _is_connection_error(resultado):
    if resultado.get("sucesso"):
        return False
    erro = (resultado.get("erro") or resultado.get("descricao") or "").lower()
    return any(kw in erro for kw in CONNECTION_ERRORS)


def _enviar_e_consultar(soap_envelope, pfx_data, senha, is_producao):
    """Envia SOAP envelope (já montado) e faz polling do resultado."""
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
            # Em processamento, continuar polling
            continue
        elif consulta.get("sucesso") is False:
            # Erro definitivo
            break

    return {
        "sucesso": False,
        "protocolo": protocolo,
        "eventos": consulta.get("eventos", []) if consulta else [],
        "codigo_resposta": consulta.get("codigo_resposta") if consulta else None,
        "descricao": consulta.get("descricao") if consulta else None,
    }


def _enviar_evento_unico(xml_bytes, pfx_data, senha, empregador, is_producao):
    """Assina, monta SOAP e envia um único evento."""
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)
    return _enviar_e_consultar(soap, pfx_data, senha, is_producao)


# ── Progress tracking (DB + JSON backup) ──────────────────────

def _load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"cpfs_ok": [], "cpfs_erro": {}, "s1298_done": False, "s1299_done": False, "run_id": None}


def _save_progress(progress: dict):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2, default=str)


def _db_create_run(per_apur: str, total_cpfs: int, total_lotes: int) -> int:
    """Cria registro pipeline_runs e retorna o ID."""
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


def _db_insert_cpfs(run_id: int, cpf_data: list[dict]):
    """Insere todos os CPFs como 'pendente' na pipeline_cpf_results."""
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            for d in cpf_data:
                cur.execute("""
                    INSERT INTO pipeline_cpf_results
                        (run_id, cpf, status, nr_recibo_original, pagamentos, info_ir_cr)
                    VALUES (%s, %s, 'pendente', %s, %s, %s)
                """, (
                    run_id,
                    d["cpf"],
                    d["nr_recibo"],
                    json.dumps(d["pagamentos"]),
                    json.dumps(d.get("infoIRCR", [])),
                ))
            conn.commit()
    finally:
        conn.close()


def _db_update_cpf(run_id: int, cpf: str, status: str, nr_recibo_novo: str = None,
                    erro: str = None, lote_num: int = None):
    """Atualiza resultado de um CPF."""
    conn = _get_supabase_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE pipeline_cpf_results
                SET status = %s, nr_recibo_novo = %s, erro_descricao = %s,
                    lote_num = %s, processed_at = NOW()
                WHERE run_id = %s AND cpf = %s
            """, (status, nr_recibo_novo, erro, lote_num, run_id, cpf))
            conn.commit()
    finally:
        conn.close()


def _db_update_run(run_id: int, **kwargs):
    """Atualiza campos do pipeline_runs."""
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


# ── Main Pipeline ─────────────────────────────────────────────

def main():
    log.info("=" * 70)
    log.info(f"  PIPELINE BATCH {PER_APUR} — PRODUÇÃO")
    log.info(f"  Fluxo: S-1298 → S-1210 retif (lotes de {LOTE_SIZE}) → S-1299")
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
    is_producao = (AMBIENTE == "1")

    # ── Carregar dados S-1210 do explorador ──
    log.info("Carregando dados S-1210 do explorador...")
    cpf_data = _load_s1210_data(PER_APUR)
    log.info(f"  {len(cpf_data)} CPFs com S-1210 original em {PER_APUR}")

    if not cpf_data:
        log.error("Nenhum S-1210 encontrado! Verifique se os XMLs foram importados.")
        sys.exit(1)

    # Validação: verificar se todos têm pagamentos
    sem_pgto = [d for d in cpf_data if not d["pagamentos"]]
    if sem_pgto:
        log.warning(f"  {len(sem_pgto)} CPFs sem pagamentos — serão IGNORADOS")
        cpf_data = [d for d in cpf_data if d["pagamentos"]]
        log.info(f"  {len(cpf_data)} CPFs válidos para retificação")

    total_lotes = (len(cpf_data) + LOTE_SIZE - 1) // LOTE_SIZE

    # ── Load progress (resume) ──
    progress = _load_progress()
    already_done = set(progress["cpfs_ok"])
    remaining = [d for d in cpf_data if d["cpf"] not in already_done]

    run_id = progress.get("run_id")

    # Create DB run if not resuming
    if not run_id:
        run_id = _db_create_run(PER_APUR, len(cpf_data), total_lotes)
        progress["run_id"] = run_id
        _save_progress(progress)
        log.info(f"  DB run criado: id={run_id}")
        # Insert all CPFs as pendente
        _db_insert_cpfs(run_id, cpf_data)
        log.info(f"  {len(cpf_data)} CPFs inseridos como pendente")
    else:
        log.info(f"  Resumindo run_id={run_id}: {len(already_done)} já processados, {len(remaining)} restantes")
        _db_update_run(run_id, status="rodando")

    # ════════════════════════════════════════════════════════════
    # STEP 1: S-1298 — Reabrir período
    # ════════════════════════════════════════════════════════════
    if not progress["s1298_done"]:
        log.info(f"\n{'─'*60}")
        log.info(f"  STEP 1: S-1298 Reabrir {PER_APUR}")
        log.info(f"{'─'*60}")
        try:
            xml = S1298XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
            result = _enviar_evento_unico(xml, pfx_data, senha, empregador, is_producao)

            # "Já aberto" é sucesso
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
                _save_progress(progress)
                recibo_1298 = None
                for e in result.get("eventos", []):
                    if e.get("nr_recibo"):
                        recibo_1298 = e["nr_recibo"]
                        break
                _db_update_run(run_id, s1298_done=True, s1298_recibo=recibo_1298)
            else:
                log.error(f"  ✗ S-1298 FALHOU: {result.get('descricao')}")
                log.error("  ABORTANDO — período não pôde ser reaberto!")
                _db_update_run(run_id, status="erro", erro_fatal=f"S-1298 falhou: {result.get('descricao')}")
                sys.exit(1)
        except Exception as e:
            log.error(f"  ✗ S-1298 ERRO: {e}")
            _db_update_run(run_id, status="erro", erro_fatal=f"S-1298 exception: {e}")
            sys.exit(1)
    else:
        log.info("  STEP 1: S-1298 já executado (resumindo)")

    # ════════════════════════════════════════════════════════════
    # STEP 2: S-1210 retif — Retificar todos os CPFs em lotes
    # ════════════════════════════════════════════════════════════
    log.info(f"\n{'─'*60}")
    log.info(f"  STEP 2: S-1210 Retificar {len(remaining)} CPFs em lotes de {LOTE_SIZE}")
    log.info(f"{'─'*60}")

    total_lotes_remaining = (len(remaining) + LOTE_SIZE - 1) // LOTE_SIZE
    cpfs_ok = 0
    cpfs_erro = 0

    for lote_idx in range(0, len(remaining), LOTE_SIZE):
        batch = remaining[lote_idx:lote_idx + LOTE_SIZE]
        lote_num = (lote_idx // LOTE_SIZE) + 1
        log.info(f"\n  Lote {lote_num}/{total_lotes_remaining} — {len(batch)} CPFs")

        # Update run progress
        _db_update_run(run_id, lote_atual=lote_num, cpfs_ok=len(progress["cpfs_ok"]),
                       cpfs_erro=len(progress["cpfs_erro"]))

        # Gerar e assinar XMLs do lote
        xmls_assinados = []
        batch_cpf_map = {}  # event_id → cpf_data
        try:
            for seq_idx, cpf_info in enumerate(batch, start=1):
                info_ir_complem = None
                if cpf_info["infoIRCR"]:
                    info_ir_complem = {"infoIRCR": cpf_info["infoIRCR"]}

                xml_bytes = S1210XMLGenerator.gerar(
                    empregador=empregador,
                    beneficiario={"cpfBenef": cpf_info["cpf"]},
                    info_pgtos=cpf_info["pagamentos"],
                    per_apur=PER_APUR,
                    ind_retif="2",
                    nr_recibo=cpf_info["nr_recibo"],
                    info_ir_complem=info_ir_complem,
                    seq=seq_idx,
                    tp_amb=AMBIENTE,
                )
                signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
                xmls_assinados.append(signed)

                # Map event ID to CPF for result matching
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
            _save_progress(progress)
            continue

        # Montar SOAP com todos os eventos do lote
        soap = SOAPEnvelopeBuilder.montar_envio(
            xmls_assinados, empregador, empregador, grupo=GRUPO
        )

        # Enviar e consultar
        result = _enviar_e_consultar(soap, pfx_data, senha, is_producao)

        if result["sucesso"] and result["eventos"]:
            # Processar resultados individuais
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

            # Match unmatched CPFs by position
            matched_cpfs = set()
            for evt in eventos:
                evt_id = evt.get("id", "")
                cpf_matched = batch_cpf_map.get(evt_id)
                if cpf_matched:
                    matched_cpfs.add(cpf_matched)

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
            # Lote inteiro falhou
            desc = result.get("descricao", "Erro desconhecido")
            log.error(f"  ✗ Lote {lote_num} FALHOU: {desc}")

            # Check individual events for partial results
            for evt in result.get("eventos", []):
                evt_id = evt.get("id", "")
                cpf_matched = batch_cpf_map.get(evt_id)
                nr_recibo = evt.get("nr_recibo")
                if nr_recibo and cpf_matched:
                    progress["cpfs_ok"].append(cpf_matched)
                    cpfs_ok += 1
                    log.info(f"    ✓ CPF {cpf_matched} (partial): recibo={nr_recibo}")
                    _db_update_cpf(run_id, cpf_matched, "ok", nr_recibo_novo=nr_recibo, lote_num=lote_num)

            # Mark remaining as error
            ok_cpfs = set(progress["cpfs_ok"])
            for ci in batch:
                if ci["cpf"] not in ok_cpfs and ci["cpf"] not in progress["cpfs_erro"]:
                    progress["cpfs_erro"][ci["cpf"]] = desc
                    cpfs_erro += 1
                    _db_update_cpf(run_id, ci["cpf"], "erro", erro=desc, lote_num=lote_num)

        _save_progress(progress)
        _db_update_run(run_id, cpfs_ok=len(progress["cpfs_ok"]), cpfs_erro=len(progress["cpfs_erro"]),
                       lote_atual=lote_num)
        log.info(f"  Lote {lote_num} concluído: OK={cpfs_ok}, Erro={cpfs_erro}, "
                 f"Total processado={cpfs_ok + cpfs_erro}/{len(cpf_data)}")

    log.info(f"\n  S-1210 retif concluído: {cpfs_ok} OK, {cpfs_erro} erros")

    # ════════════════════════════════════════════════════════════
    # STEP 3: S-1299 — Fechar período
    # ════════════════════════════════════════════════════════════
    if not progress["s1299_done"]:
        log.info(f"\n{'─'*60}")
        log.info(f"  STEP 3: S-1299 Fechar {PER_APUR}")
        log.info(f"{'─'*60}")

        if cpfs_erro > 0:
            log.warning(f"  ATENÇÃO: {cpfs_erro} CPFs com erro. Fechando assim mesmo.")

        try:
            xml = S1299XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
            result = _enviar_evento_unico(xml, pfx_data, senha, empregador, is_producao)

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
                log.error("  Período ficará ABERTO. Execute novamente para tentar fechar.")
        except Exception as e:
            log.error(f"  ✗ S-1299 ERRO: {e}")
    else:
        log.info("  STEP 3: S-1299 já executado")

    _save_progress(progress)

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
    log.info(f"  Período: {PER_APUR}")
    log.info(f"  Run ID: {run_id}")
    log.info(f"  Total CPFs: {len(cpf_data)}")
    log.info(f"  S-1210 retificados: {len(progress['cpfs_ok'])}")
    log.info(f"  S-1210 com erro: {len(progress['cpfs_erro'])}")
    log.info(f"  S-1298 (reabrir): {'✓' if progress['s1298_done'] else '✗'}")
    log.info(f"  S-1299 (fechar):  {'✓' if progress['s1299_done'] else '✗'}")
    log.info(f"  STATUS: {final_status.upper()}")
    log.info(f"{'='*70}")

    # Salvar resultado final (backup JSON)
    final_result = {
        "run_id": run_id,
        "per_apur": PER_APUR,
        "status": final_status,
        "total_cpfs": len(cpf_data),
        "cpfs_ok": len(progress["cpfs_ok"]),
        "cpfs_erro": len(progress["cpfs_erro"]),
        "s1298_done": progress["s1298_done"],
        "s1299_done": progress["s1299_done"],
        "erros_detalhe": progress["cpfs_erro"],
        "timestamp": datetime.now().isoformat(),
    }
    with open(RESULT_FILE, "w") as f:
        json.dump(final_result, f, indent=2, default=str)
    log.info(f"\nResultado salvo em {RESULT_FILE}")
    log.info(f"Acompanhe na interface: Pipeline 98-10-99 → run #{run_id}")

    if progress["cpfs_erro"]:
        log.info(f"\nPrimeiros 10 CPFs com erro:")
        for cpf, erro in list(progress["cpfs_erro"].items())[:10]:
            log.info(f"  {cpf}: {erro}")


if __name__ == "__main__":
    main()
