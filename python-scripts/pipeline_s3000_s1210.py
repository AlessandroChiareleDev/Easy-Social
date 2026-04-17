"""
Pipeline S-3000 + S-1210 — Exclusão e Reenvio sem rubricas de plano de saúde
═══════════════════════════════════════════════════════════════════════════════
Estratégia:
  1. S-3000: Exclui o S-1210 atual do eSocial (usando nrRecEvt)
  2. S-1210: Reenvia como ORIGINAL (indRetif=1) SEM planSaude

A planilha define quais rubricas excluir por CPF, mas o S-1210 não contém
rubricas — o efeito é que ao excluir o S-1210 antigo e reenviar sem planSaude,
o eSocial não vai mais cobrar o grupo planSaude.

Uso:
  python pipeline_s3000_s1210.py --dry-run                    # gera XMLs sem enviar
  python pipeline_s3000_s1210.py --cpf 01865691739             # 1 CPF (teste)
  python pipeline_s3000_s1210.py --cpf-list C:\\tmp\\cpfs.txt    # lista de CPFs
  python pipeline_s3000_s1210.py                               # todos os 934 CPFs da planilha
"""

import sys
import os
import json
import time
import re
import argparse
import tempfile
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
import psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import openpyxl
from collections import defaultdict

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════

PER_APUR = "2025-01"
AMBIENTE = "1"          # PRODUÇÃO
GRUPO_S3000 = 2        # S-3000 exclusão vai no grupo 2 (não periódicos)
GRUPO_S1210 = 3        # eventos periódicos
POLL_DELAY = 5
MAX_POLL_RETRIES = 24
MAX_SEND_RETRIES = 3
SEND_RETRY_DELAY = 5

PLANILHA = os.path.expanduser(
    "~/Downloads/S_Tabela - Financeiro - 202412  certo caso final.xlsx"
)

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
    "name resolution", "temporary failure", "could not translate host name",
]

LOG_FILE = "/tmp/pipeline_s3000_s1210.log"

# Globals
_cert_pem_path = None
_key_pem_path = None
_pfx_data = None
_pfx_senha = None

log = logging.getLogger("s3000_s1210")


# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

def setup_logging():
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    log.addHandler(ch)
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    log.addHandler(fh)


# ═══════════════════════════════════════════════════════════════
# CERT + PEM
# ═══════════════════════════════════════════════════════════════

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


def setup_pem_cache(pfx_data, senha):
    global _cert_pem_path, _key_pem_path, _pfx_data, _pfx_senha
    _pfx_data = pfx_data
    _pfx_senha = senha
    cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, senha)
    cert_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_s3000_cert.pem")
    cert_file.write(cert_pem)
    cert_file.close()
    _cert_pem_path = cert_file.name
    key_file = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_s3000_key.pem")
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
# DB
# ═══════════════════════════════════════════════════════════════

def get_supabase_conn():
    return psycopg2.connect(**DB_CONFIG)


# ═══════════════════════════════════════════════════════════════
# SOAP
# ═══════════════════════════════════════════════════════════════

def soap_enviar(soap_envelope: str, url: str):
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


def enviar_e_poll(xml_bytes: bytes, empregador_xml: dict, empregador_soap: dict, label: str, grupo=4):
    """Assina, envelopa, envia 1 evento e faz poll. Retorna dict com resultado."""
    signed = XMLSigner.assinar(xml_bytes, _pfx_data, _pfx_senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador_soap, empregador_soap, grupo=grupo)
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)

    # Enviar via ESocialClient.enviar_lote (mTLS handling)
    resultado = None
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        try:
            resultado = ESocialClient.enviar_lote(soap, _pfx_data, _pfx_senha, url=url_envio)
            if resultado.get("sucesso"):
                break
            erro = (resultado.get("descricao") or resultado.get("erro") or "").lower()
            if not any(kw in erro for kw in CONNECTION_ERRORS):
                break
        except Exception as e:
            resultado = {"sucesso": False, "descricao": str(e), "protocolo": None}
        if attempt < MAX_SEND_RETRIES:
            time.sleep(SEND_RETRY_DELAY * attempt)

    if not resultado or not resultado.get("sucesso"):
        desc = (resultado or {}).get("descricao", "Envio falhou")
        erro_extra = (resultado or {}).get("erro", "")
        ocorrencias = (resultado or {}).get("ocorrencias", [])
        if ocorrencias:
            desc += " | " + " | ".join(
                f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
            )
        if erro_extra:
            desc += f" | erro: {erro_extra}"
        log.error(f"  {label} envio FALHOU: {desc}")
        return {"sucesso": False, "descricao": desc}

    protocolo = resultado.get("protocolo")
    if not protocolo:
        return {"sucesso": False, "descricao": "Sem protocolo"}

    log.info(f"  {label} protocolo={protocolo}, aguardando...")

    # Poll
    for _ in range(MAX_POLL_RETRIES):
        time.sleep(POLL_DELAY)
        try:
            consulta = ESocialClient.consultar_lote(protocolo, _pfx_data, _pfx_senha, url=url_consulta)
        except Exception:
            continue
        if consulta.get("sucesso") and consulta.get("eventos"):
            evt = consulta["eventos"][0]
            nr_rec = evt.get("nr_recibo")
            cod = evt.get("codigo_resposta", "")
            if nr_rec:
                return {"sucesso": True, "nr_recibo": nr_rec, "codigo": cod}
            else:
                desc = evt.get("descricao", "")
                ocorrencias = evt.get("ocorrencias", [])
                if ocorrencias:
                    desc += " | " + " | ".join(
                        f"[{oc.get('codigo')}] {oc.get('descricao')}" for oc in ocorrencias
                    )
                return {"sucesso": False, "descricao": desc, "codigo": cod}
        if consulta.get("codigo_resposta") == "101":
            continue
        if "em processamento" in (consulta.get("descricao") or "").lower():
            continue
        if consulta.get("sucesso") is False:
            return {"sucesso": False, "descricao": consulta.get("descricao", "Falha")}

    return {"sucesso": False, "descricao": "Timeout polling"}


# ═══════════════════════════════════════════════════════════════
# PLANILHA — CPFs e rubricas a excluir
# ═══════════════════════════════════════════════════════════════

def load_planilha_cpfs(planilha_path: str) -> dict:
    """Retorna {cpf_digits: set(rubricas_a_excluir)}"""
    wb = openpyxl.load_workbook(planilha_path, read_only=True)
    ws = wb.active
    cpf_rubricas = defaultdict(set)
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        cpf_raw = row[7]
        cod_ev = row[11]
        if cpf_raw and cod_ev:
            cpf = str(cpf_raw).replace(".", "").replace("-", "").strip()
            cpf_rubricas[cpf].add(int(cod_ev))
    wb.close()
    return dict(cpf_rubricas)


# ═══════════════════════════════════════════════════════════════
# DADOS DO CPF — explorador_eventos + pipeline_cpf_results
# ═══════════════════════════════════════════════════════════════

def load_cpf_data(cpfs: list[str]) -> dict:
    """
    Para cada CPF, busca:
      - pagamentos e infoIRCR do S-1210 original (explorador_eventos)
      - recibo mais recente (pipeline_cpf_results ou explorador_eventos)
    Retorna: {cpf: {pagamentos, infoIRCR, nr_recibo}}
    """
    conn = get_supabase_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. S-1210 originais do explorador
            cur.execute("""
                SELECT e.cpf, e.nr_recibo, e.dados_json
                FROM explorador_eventos e
                WHERE e.tipo_evento = 'S-1210'
                  AND e.per_apur = %s
                  AND e.cpf = ANY(%s)
                  AND e.nr_recibo IS NOT NULL
                  AND COALESCE(e.dados_json->>'indRetif', '1') != '2'
                ORDER BY e.cpf, e.id ASC
            """, (PER_APUR, cpfs))
            rows = cur.fetchall()

        cpf_data = {}
        for row in rows:
            cpf = row["cpf"]
            if cpf in cpf_data:
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

            cpf_data[cpf] = {
                "pagamentos": pagamentos,
                "infoIRCR": info_ir_cr,
                "nr_recibo_original": row["nr_recibo"],
            }

        # 2. Recibo mais recente do pipeline (retificações anteriores)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (r.cpf) r.cpf, r.nr_recibo_novo
                FROM pipeline_cpf_results r
                JOIN pipeline_runs p ON p.id = r.run_id
                WHERE p.per_apur = %s
                  AND r.cpf = ANY(%s)
                  AND r.status = 'ok'
                  AND r.nr_recibo_novo IS NOT NULL
                ORDER BY r.cpf, r.processed_at DESC NULLS LAST
            """, (PER_APUR, cpfs))
            for row in cur.fetchall():
                cpf = row[0]
                if cpf in cpf_data:
                    cpf_data[cpf]["nr_recibo"] = row[1]

        # Fallback: se não teve retificação OK, usa o original
        for cpf, d in cpf_data.items():
            if "nr_recibo" not in d:
                d["nr_recibo"] = d["nr_recibo_original"]

        return cpf_data
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# PROCESSAMENTO PRINCIPAL — S-3000 + S-1210 por CPF
# ═══════════════════════════════════════════════════════════════

def process_cpf(cpf: str, cpf_info: dict, empregador_xml: dict, empregador_soap: dict, dry_run: bool = False):
    """
    Processa 1 CPF:
      1. Gera e envia S-3000 (exclui S-1210 atual)
      2. Gera e envia S-1210 novo (original, sem planSaude)
    
    Retorna: (cpf, status, nr_recibo_novo, erro)
    """
    nr_recibo = cpf_info["nr_recibo"]
    pagamentos = cpf_info["pagamentos"]
    info_ir_cr = cpf_info["infoIRCR"]

    # ── PASSO 1: Gerar S-3000 ──
    log.info(f"[{cpf}] Passo 1: S-3000 (excluir recibo {nr_recibo})")

    xml_s3000 = S3000XMLGenerator.gerar(
        empregador=empregador_xml,
        tp_evento="S-1210",
        nr_rec_evt=nr_recibo,
        cpf_trab=cpf,
        per_apur=PER_APUR,
        seq=1,
        tp_amb=AMBIENTE,
    )

    if dry_run:
        log.info(f"[{cpf}] [DRY-RUN] S-3000 XML:")
        log.info(xml_s3000.decode("utf-8"))
    else:
        res_s3000 = enviar_e_poll(xml_s3000, empregador_xml, empregador_soap, f"[{cpf}] S-3000", grupo=GRUPO_S3000)
        if not res_s3000.get("sucesso"):
            return cpf, "erro", None, f"S-3000 falhou: {res_s3000.get('descricao')}"
        log.info(f"[{cpf}] S-3000 OK — recibo exclusão: {res_s3000.get('nr_recibo')}")

    # ── PASSO 2: Gerar S-1210 novo (original, sem planSaude) ──
    log.info(f"[{cpf}] Passo 2: S-1210 novo (original, sem planSaude)")

    info_ir = None
    if info_ir_cr:
        info_ir = {"infoIRCR": info_ir_cr}

    xml_s1210 = S1210XMLGenerator.gerar(
        empregador=empregador_xml,
        beneficiario={"cpfBenef": cpf},
        info_pgtos=pagamentos,
        per_apur=PER_APUR,
        ind_retif="1",       # ORIGINAL (não retificação — o antigo foi excluído)
        nr_recibo=None,      # sem recibo (é original)
        info_ir_complem=info_ir,
        plan_saude=None,     # SEM planSaude
        seq=2,
        tp_amb=AMBIENTE,
    )

    if dry_run:
        log.info(f"[{cpf}] [DRY-RUN] S-1210 XML:")
        log.info(xml_s1210.decode("utf-8"))
        return cpf, "dry-run", None, None
    else:
        res_s1210 = enviar_e_poll(xml_s1210, empregador_xml, empregador_soap, f"[{cpf}] S-1210", grupo=GRUPO_S1210)
        if not res_s1210.get("sucesso"):
            return cpf, "erro", None, f"S-1210 falhou: {res_s1210.get('descricao')}"
        nr_novo = res_s1210.get("nr_recibo")
        log.info(f"[{cpf}] S-1210 OK — novo recibo: {nr_novo}")
        return cpf, "ok", nr_novo, None


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Pipeline S-3000 + S-1210")
    parser.add_argument("--dry-run", action="store_true", help="Gera XMLs sem enviar")
    parser.add_argument("--cpf", type=str, help="CPF único para teste")
    parser.add_argument("--cpf-list", type=str, help="Arquivo com lista de CPFs")
    args = parser.parse_args()

    setup_logging()
    log.info("=" * 60)
    log.info("Pipeline S-3000 + S-1210 — Exclusão e Reenvio")
    log.info("=" * 60)

    # 1. Determinar CPFs alvo
    if args.cpf:
        cpf_clean = args.cpf.replace(".", "").replace("-", "").strip()
        target_cpfs = [cpf_clean]
        log.info(f"Modo: CPF único = {cpf_clean}")
    elif args.cpf_list:
        with open(args.cpf_list) as f:
            target_cpfs = [
                line.strip().replace(".", "").replace("-", "")
                for line in f if line.strip()
            ]
        log.info(f"Modo: lista de CPFs = {len(target_cpfs)}")
    else:
        planilha_cpfs = load_planilha_cpfs(PLANILHA)
        target_cpfs = list(planilha_cpfs.keys())
        log.info(f"Modo: planilha = {len(target_cpfs)} CPFs")

    if not target_cpfs:
        log.error("Nenhum CPF para processar!")
        return

    # 2. Carregar dados dos CPFs
    log.info(f"Carregando dados de {len(target_cpfs)} CPFs...")
    cpf_data = load_cpf_data(target_cpfs)
    log.info(f"Dados encontrados para {len(cpf_data)} CPFs")

    missing = [c for c in target_cpfs if c not in cpf_data]
    if missing:
        log.warning(f"CPFs sem dados no explorador: {len(missing)}")
        for c in missing[:10]:
            log.warning(f"  {c}")

    # 3. Certificado
    if not args.dry_run:
        cert = load_cert()
        if not cert:
            log.error("Certificado não encontrado!")
            return
        with open(cert["arquivo_path"], "rb") as f:
            pfx_data = f.read()
        setup_pem_cache(pfx_data, cert["senha"])
        cnpj = cert["cnpj"]
    else:
        cnpj = "05969071"  # fallback dry-run

    empregador_xml = {"tpInsc": 1, "nrInsc": cnpj[:8]}
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj}

    # 4. Processar CPFs
    ok = 0
    erros = 0
    resultados = []

    for i, cpf in enumerate(target_cpfs, 1):
        if cpf not in cpf_data:
            log.warning(f"[{i}/{len(target_cpfs)}] {cpf} — sem dados, pulando")
            resultados.append((cpf, "skip", None, "Sem dados no explorador"))
            continue

        log.info(f"\n[{i}/{len(target_cpfs)}] Processando {cpf}")
        try:
            cpf_result = process_cpf(cpf, cpf_data[cpf], empregador_xml, empregador_soap, dry_run=args.dry_run)
            resultados.append(cpf_result)
            if cpf_result[1] == "ok":
                ok += 1
            elif cpf_result[1] == "erro":
                erros += 1
                log.error(f"  ERRO: {cpf_result[3]}")
        except Exception as e:
            log.error(f"  EXCEPTION: {e}")
            resultados.append((cpf, "erro", None, str(e)))
            erros += 1

        # Intervalo entre CPFs (sequencial — S-3000 precisa completar antes do S-1210)
        if not args.dry_run and i < len(target_cpfs):
            time.sleep(1)

    # 5. Resumo
    log.info("\n" + "=" * 60)
    log.info("RESUMO")
    log.info("=" * 60)
    log.info(f"Total CPFs: {len(target_cpfs)}")
    log.info(f"OK: {ok}")
    log.info(f"Erros: {erros}")
    log.info(f"Skips: {len(target_cpfs) - ok - erros}")

    if erros > 0:
        log.info("\nCPFs com ERRO:")
        for r in resultados:
            if r[1] == "erro":
                log.info(f"  {r[0]}: {r[3]}")

    # Salvar resultados
    result_file = "/tmp/pipeline_s3000_s1210_result.json"
    with open(result_file, "w") as f:
        json.dump([{"cpf": r[0], "status": r[1], "nr_recibo": r[2], "erro": r[3]}
                    for r in resultados], f, indent=2, ensure_ascii=False)
    log.info(f"\nResultados salvos em {result_file}")

    if not args.dry_run:
        cleanup_pem_cache()


if __name__ == "__main__":
    main()
