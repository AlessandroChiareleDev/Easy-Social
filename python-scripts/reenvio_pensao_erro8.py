"""
Reenvio S-1210 — 51 CPFs com erro [8] (pensão alimentícia).

Fluxo:
  1. S-1298   — Reabrir período 2025-09
  2. S-1210   — Retificar os 51 CPFs (lotes de 50)
  3. S-1299   — Fechar período 2025-09

Lê dados atualizados (com penAlim) do explorador_eventos (Supabase).
Roda na VPS: python3 reenvio_pensao_erro8.py
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
LOTE_SIZE = 50
MAX_POLL_RETRIES = 8
POLL_DELAY = 15
MAX_SEND_RETRIES = 5
SEND_RETRY_DELAY = 10

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
    "name resolution", "temporary failure", "could not translate host name",
]

LOG_FILE = f"/tmp/reenvio_pensao_erro8_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE),
    ],
)
log = logging.getLogger("reenvio_pensao")


# ── DB helpers ────────────────────────────────────────────────

def _get_supabase_conn():
    for attempt in range(1, 6):
        try:
            return psycopg2.connect(
                **DB_CONFIG,
                keepalives=1, keepalives_idle=30,
                keepalives_interval=10, keepalives_count=3,
            )
        except psycopg2.OperationalError as e:
            if attempt < 5:
                log.warning(f"  DB connect attempt {attempt}/5 failed: {e}. Retrying...")
                time.sleep(5)
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


def _load_erro8_cpfs() -> list[dict]:
    """
    Carrega dados S-1210 para CPFs que falharam com erro [8].
    Usa o dados_json atualizado (com penAlim/dedDepen).
    """
    conn = _get_supabase_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Buscar CPFs com erro [8]
            cur.execute("""
                SELECT cpf FROM pipeline_cpf_results
                WHERE status = 'erro' AND erro_descricao LIKE '%[8]%'
                ORDER BY cpf
            """)
            erro8_cpfs = [r["cpf"] for r in cur.fetchall()]
            log.info(f"  {len(erro8_cpfs)} CPFs com erro [8]")

            if not erro8_cpfs:
                return []

            # Buscar dados S-1210 atualizados do explorador  
            ph = ",".join(["%s"] * len(erro8_cpfs))
            cur.execute(f"""
                SELECT e.cpf, e.nr_recibo, e.dados_json, e.dt_processamento
                FROM explorador_eventos e
                WHERE e.tipo_evento = 'S-1210'
                  AND e.per_apur = %s
                  AND e.cpf IN ({ph})
                  AND e.nr_recibo IS NOT NULL
                  AND COALESCE(e.dados_json->>'indRetif', '1') != '2'
                ORDER BY e.cpf, e.dt_processamento DESC
            """, [PER_APUR] + erro8_cpfs)
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

            # Verificar quais CPFs têm penAlim nos dados
            com_penalim = 0
            for d in cpf_map.values():
                for cr in d["infoIRCR"]:
                    if cr.get("penAlim"):
                        com_penalim += 1
                        break

            log.info(f"  {len(cpf_map)} CPFs com dados S-1210")
            log.info(f"  {com_penalim} CPFs com penAlim no dados_json")

            # Alertar CPFs sem dados
            sem_dados = set(erro8_cpfs) - set(cpf_map.keys())
            if sem_dados:
                log.warning(f"  {len(sem_dados)} CPFs sem dados S-1210: {sem_dados}")

            return list(cpf_map.values())
    finally:
        conn.close()


# ── SOAP helpers (copiados do pipeline_batch) ─────────────────

def _is_connection_error(resultado):
    if resultado.get("sucesso"):
        return False
    erro = (resultado.get("erro") or resultado.get("descricao") or "").lower()
    return any(kw in erro for kw in CONNECTION_ERRORS)


def _enviar_e_consultar(soap_envelope, pfx_data, senha, is_producao):
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
        elif consulta.get("sucesso") is False:
            break

    return {
        "sucesso": False,
        "protocolo": protocolo,
        "eventos": consulta.get("eventos", []) if consulta else [],
        "codigo_resposta": consulta.get("codigo_resposta") if consulta else None,
        "descricao": consulta.get("descricao") if consulta else None,
    }


def _enviar_evento_unico(xml_bytes, pfx_data, senha, empregador, is_producao):
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=GRUPO)
    return _enviar_e_consultar(soap, pfx_data, senha, is_producao)


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    log.info("=" * 70)
    log.info("  REENVIO PENSÃO ALIMENTÍCIA — 51 CPFs com erro [8]")
    log.info(f"  Período: {PER_APUR} | Ambiente: PRODUÇÃO")
    log.info("=" * 70)

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

    # Carregar dados
    cpf_data = _load_erro8_cpfs()
    if not cpf_data:
        log.error("Nenhum CPF encontrado!")
        sys.exit(1)

    sem_pgto = [d for d in cpf_data if not d["pagamentos"]]
    if sem_pgto:
        log.warning(f"  {len(sem_pgto)} CPFs sem pagamentos — serão IGNORADOS")
        cpf_data = [d for d in cpf_data if d["pagamentos"]]

    log.info(f"  {len(cpf_data)} CPFs para retificar")

    # ═══ STEP 1: S-1298 Reabrir ═══
    log.info(f"\n{'─'*60}")
    log.info(f"  STEP 1: S-1298 Reabrir {PER_APUR}")
    log.info(f"{'─'*60}")

    xml = S1298XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
    result = _enviar_evento_unico(xml, pfx_data, senha, empregador, is_producao)

    already_open = (
        not result["sucesso"] and result.get("descricao")
        and any(kw in result["descricao"].lower() for kw in [
            "já se encontra", "já está abert", "[715]", "período já"
        ])
    )
    if already_open:
        result["sucesso"] = True

    if not result["sucesso"]:
        log.error(f"  ✗ S-1298 FALHOU: {result.get('descricao')}")
        sys.exit(1)
    log.info(f"  ✓ S-1298: {result.get('descricao', 'OK')}")

    # ═══ STEP 2: S-1210 Retificar ═══
    log.info(f"\n{'─'*60}")
    log.info(f"  STEP 2: S-1210 Retificar {len(cpf_data)} CPFs")
    log.info(f"{'─'*60}")

    cpfs_ok = []
    cpfs_erro = {}
    total_lotes = (len(cpf_data) + LOTE_SIZE - 1) // LOTE_SIZE

    for lote_idx in range(0, len(cpf_data), LOTE_SIZE):
        batch = cpf_data[lote_idx:lote_idx + LOTE_SIZE]
        lote_num = (lote_idx // LOTE_SIZE) + 1
        log.info(f"\n  Lote {lote_num}/{total_lotes} — {len(batch)} CPFs")

        xmls_assinados = []
        batch_cpf_map = {}

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

                xml_str = signed.decode("utf-8") if isinstance(signed, bytes) else signed
                id_match = re.search(r'Id="(ID[^"]+)"', xml_str)
                if id_match:
                    batch_cpf_map[id_match.group(1)] = cpf_info["cpf"]
        except Exception as e:
            log.error(f"  ✗ Erro ao gerar XMLs do lote {lote_num}: {e}")
            for ci in batch:
                cpfs_erro[ci["cpf"]] = str(e)
            continue

        soap = SOAPEnvelopeBuilder.montar_envio(
            xmls_assinados, empregador, empregador, grupo=GRUPO
        )
        result = _enviar_e_consultar(soap, pfx_data, senha, is_producao)

        if result["sucesso"] and result["eventos"]:
            matched_cpfs = set()
            for evt in result["eventos"]:
                evt_id = evt.get("id", "")
                cpf_matched = batch_cpf_map.get(evt_id)
                nr_recibo = evt.get("nr_recibo")
                cod = evt.get("codigo_resposta", "")

                if nr_recibo and cpf_matched:
                    cpfs_ok.append(cpf_matched)
                    matched_cpfs.add(cpf_matched)
                    log.info(f"    ✓ CPF {cpf_matched}: recibo={nr_recibo}")
                elif cpf_matched and cod and cod not in ("201", "202"):
                    desc = evt.get("descricao", "")
                    ocorrencias = evt.get("ocorrencias", [])
                    if ocorrencias:
                        desc += " | " + " | ".join(
                            f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                        )
                    cpfs_erro[cpf_matched] = desc
                    matched_cpfs.add(cpf_matched)
                    log.warning(f"    ✗ CPF {cpf_matched}: [{cod}] {desc}")

            # Position-based matching
            if len(matched_cpfs) < len(batch) and len(result["eventos"]) == len(batch):
                for i, (evt, cpf_info) in enumerate(zip(result["eventos"], batch)):
                    if cpf_info["cpf"] not in matched_cpfs:
                        nr_recibo = evt.get("nr_recibo")
                        if nr_recibo:
                            cpfs_ok.append(cpf_info["cpf"])
                            log.info(f"    ✓ CPF {cpf_info['cpf']} (pos): recibo={nr_recibo}")
                        else:
                            desc = evt.get("descricao", "sem recibo")
                            cpfs_erro[cpf_info["cpf"]] = desc
                            log.warning(f"    ✗ CPF {cpf_info['cpf']} (pos): {desc}")
        else:
            desc = result.get("descricao", "Erro desconhecido")
            log.error(f"  ✗ Lote {lote_num} FALHOU: {desc}")
            for ci in batch:
                if ci["cpf"] not in cpfs_ok and ci["cpf"] not in cpfs_erro:
                    cpfs_erro[ci["cpf"]] = desc

        log.info(f"  Progresso: OK={len(cpfs_ok)}, Erro={len(cpfs_erro)}")

    # Atualizar pipeline_cpf_results
    log.info(f"\n  Atualizando pipeline_cpf_results...")
    try:
        conn = _get_supabase_conn()
        try:
            with conn.cursor() as cur:
                for cpf in cpfs_ok:
                    cur.execute("""
                        UPDATE pipeline_cpf_results
                        SET status = 'ok', erro_descricao = NULL, processed_at = NOW()
                        WHERE cpf = %s AND status = 'erro' AND erro_descricao LIKE '%%[8]%%'
                    """, (cpf,))
                for cpf, erro in cpfs_erro.items():
                    cur.execute("""
                        UPDATE pipeline_cpf_results
                        SET erro_descricao = %s, processed_at = NOW()
                        WHERE cpf = %s AND status = 'erro'
                    """, (f"[REENVIO] {erro}", cpf))
            conn.commit()
            log.info(f"  ✓ {len(cpfs_ok)} CPFs atualizados para OK")
        finally:
            conn.close()
    except Exception as e:
        log.error(f"  ✗ Erro ao atualizar DB: {e}")

    # ═══ STEP 3: S-1299 Fechar ═══
    log.info(f"\n{'─'*60}")
    log.info(f"  STEP 3: S-1299 Fechar {PER_APUR}")
    log.info(f"{'─'*60}")

    xml = S1299XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
    result = _enviar_evento_unico(xml, pfx_data, senha, empregador, is_producao)

    if result["sucesso"]:
        log.info(f"  ✓ S-1299: {result.get('descricao', 'OK')}")
    else:
        log.error(f"  ✗ S-1299 FALHOU: {result.get('descricao')}")

    # ═══ RESUMO ═══
    log.info(f"\n{'='*70}")
    log.info("  RESUMO REENVIO PENSÃO")
    log.info(f"{'='*70}")
    log.info(f"  CPFs retificados OK: {len(cpfs_ok)}")
    log.info(f"  CPFs com erro: {len(cpfs_erro)}")
    if cpfs_erro:
        for cpf, erro in cpfs_erro.items():
            log.info(f"    {cpf}: {erro}")
    log.info(f"  Log: {LOG_FILE}")
    log.info(f"{'='*70}")


if __name__ == "__main__":
    main()
