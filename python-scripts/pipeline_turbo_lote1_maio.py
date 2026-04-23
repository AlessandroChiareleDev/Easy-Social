"""
Pipeline TURBO Lote 1 / 2025-05.
- Le XMLs ja gerados em saida_retif_lote1_maio/xml/<cpf>.xml
- Quebra em batches de LOTE_SIZE (50) por SOAP
- WORKERS threads paralelas processam batches
- Garante scope no Supabase (s1210_xlsx + s1210_cpf_scope) p/ a tela refletir
- Grava cada CPF em s1210_cpf_envios (status, recibo, protocolo)

Uso:
  python pipeline_turbo_lote1_maio.py --max 250          # default
  python pipeline_turbo_lote1_maio.py --max 1000 --workers 5 --batch 50
  python pipeline_turbo_lote1_maio.py --backfill-envios   # so registra os 110 ja enviados
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import psycopg2
import psycopg2.extras
from db_config import DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_signer import S1010XMLSigner

XML_DIR = os.path.join(ROOT, "saida_retif_lote1_maio", "xml")
GEN_REPORT = os.path.join(ROOT, "saida_retif_lote1_maio", "relatorio.csv")
ENVIO_LOG = os.path.join(ROOT, "saida_retif_lote1_maio", "envios_producao.csv")

PER_APUR = "2025-05"
EMPRESA_ID = 1
LOTE_NUM = 1
CNPJ = "05969071000110"
PFX_PATH = os.path.join(ROOT, "certificados", "cert_05969071000110_45C7EBE84F3FE665.pfx")

XLSX_SYNTH_SHA = "synthetic_lote1_2025_05_zip"  # marca origem ZIP, nao XLSX real

# PEM cache global
_cert_pem_path = None
_key_pem_path = None
_pfx_data = None
_pfx_senha = None
_db_lock = threading.Lock()


def _setup_pem(pfx_data: bytes, senha: str) -> None:
    global _cert_pem_path, _key_pem_path, _pfx_data, _pfx_senha
    _pfx_data = pfx_data
    _pfx_senha = senha
    cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, senha)
    cf = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_cert.pem")
    cf.write(cert_pem); cf.close()
    _cert_pem_path = cf.name
    kf = tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix="_key.pem")
    kf.write(key_pem); kf.close()
    _key_pem_path = kf.name


def _soap_enviar(soap: str, url: str) -> dict:
    resp = requests.post(
        url=url, data=soap.encode("utf-8"),
        headers=SOAPEnvelopeBuilder.headers(),
        cert=(_cert_pem_path, _key_pem_path), verify=False, timeout=120,
    )
    resp.raise_for_status()
    return ESocialClient._parsear_resposta_envio(resp.text)


def _soap_consultar(protocolo: str, url: str) -> dict:
    soap = SOAPEnvelopeBuilder.montar_consulta(protocolo)
    resp = requests.post(
        url=url, data=soap.encode("utf-8"),
        headers=SOAPEnvelopeBuilder.headers_consulta(),
        cert=(_cert_pem_path, _key_pem_path), verify=False, timeout=120,
    )
    resp.raise_for_status()
    return ESocialClient._parsear_resposta_consulta(resp.text)


# ── DB ────────────────────────────────────────────────────────

def _db():
    return psycopg2.connect(
        **DB_CONFIG, keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3,
    )


def _ensure_scope(cpfs: list[str]) -> int:
    """Garante s1210_xlsx synthetic + s1210_cpf_scope com CPFs do Lote 1/2025-05."""
    sha = hashlib.sha256(XLSX_SYNTH_SHA.encode()).hexdigest()
    conn = _db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO s1210_xlsx (empresa_id, per_apur, nome_arquivo, tamanho_bytes,
                    sha256, storage_path, aba_geral, parse_ok, totais_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE,%s::jsonb)
                ON CONFLICT (empresa_id, per_apur, sha256) DO UPDATE SET parse_ok=TRUE
                RETURNING id
                """,
                (EMPRESA_ID, PER_APUR, "synthetic_zip_lote1_2025_05", 0, sha,
                 "synthetic/2025-05", "ZIP_29429551_maio", f'{{"1_LOTE": {len(cpfs)}}}'),
            )
            xlsx_id = cur.fetchone()[0]

            # Insere CPFs em scope (idempotente via UNIQUE)
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO s1210_cpf_scope
                    (xlsx_id, empresa_id, per_apur, cpf, lote_num)
                VALUES %s
                ON CONFLICT (empresa_id, per_apur, cpf) DO NOTHING
                """,
                [(xlsx_id, EMPRESA_ID, PER_APUR, cpf, LOTE_NUM) for cpf in cpfs],
                page_size=500,
            )
            conn.commit()
            cur.execute(
                "SELECT COUNT(*) FROM s1210_cpf_scope WHERE empresa_id=%s AND per_apur=%s",
                (EMPRESA_ID, PER_APUR),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def _registrar_envio(cpf: str, status: str, *, nr_recibo_usado=None,
                      nr_recibo_novo=None, protocolo=None, codigo=None,
                      descricao=None, erro=None) -> None:
    """Insere uma linha em s1210_cpf_envios (1 linha por envio, ULTIMO conta na view)."""
    with _db_lock:
        pass  # apenas pra serializar abertura de conexoes? nao precisa
    conn = _db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO s1210_cpf_envios
                    (empresa_id, per_apur, cpf, lote_num, status,
                     nr_recibo_usado, nr_recibo_novo, protocolo,
                     codigo_resposta, descricao_resposta, erro_descricao, enviado_em)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW())
                """,
                (EMPRESA_ID, PER_APUR, cpf, LOTE_NUM, status,
                 nr_recibo_usado, nr_recibo_novo, protocolo,
                 codigo, descricao, erro),
            )
            conn.commit()
    finally:
        conn.close()


def _ja_enviados_db() -> set[str]:
    """Retorna CPFs cujo ULTIMO envio em 2025-05 lote 1 = 'ok' ou 'erro'."""
    conn = _db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cpf FROM (
                    SELECT DISTINCT ON (cpf) cpf, status
                      FROM s1210_cpf_envios
                     WHERE empresa_id=%s AND per_apur=%s AND lote_num=%s
                     ORDER BY cpf, enviado_em DESC
                ) u
                WHERE status IN ('ok','erro')
                """,
                (EMPRESA_ID, PER_APUR, LOTE_NUM),
            )
            return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()


# ── XML helpers ───────────────────────────────────────────────

RE_EVT_ID = re.compile(r'<evtPgtos\s+Id="([^"]+)"')
RE_NR_RECIBO_USADO = re.compile(r"<nrRecibo>([\d.]+)</nrRecibo>")


def _xml_meta(xml_bytes: bytes) -> tuple[str, str | None]:
    """Retorna (id_evento, nr_recibo_usado_no_retif)."""
    s = xml_bytes.decode("utf-8", errors="replace")
    m_id = RE_EVT_ID.search(s)
    m_rec = RE_NR_RECIBO_USADO.search(s)
    return (m_id.group(1) if m_id else "", m_rec.group(1) if m_rec else None)


# ── Worker batch ──────────────────────────────────────────────

def _processar_batch(batch: list[str], idx_batch: int, n_batches: int) -> dict:
    """Envia 1 batch (ate 50 CPFs) ao eSocial e atualiza DB."""
    t0 = time.time()
    thread = threading.current_thread().name
    log = lambda m: print(f"[{thread} #{idx_batch}/{n_batches}] {m}", flush=True)

    # 1) Le + assina XMLs
    eventos_assinados = []
    id_to_cpf = {}
    cpf_to_recibo_usado = {}
    falhas_pre = []

    for cpf in batch:
        xml_path = os.path.join(XML_DIR, f"{cpf}.xml")
        if not os.path.exists(xml_path):
            falhas_pre.append((cpf, "xml ausente"))
            continue
        try:
            with open(xml_path, "rb") as f:
                xml_bytes = f.read()
            assinado = S1010XMLSigner.assinar(xml_bytes, _pfx_data, _pfx_senha)
            evt_id, nr_usado = _xml_meta(assinado)
            id_to_cpf[evt_id] = cpf
            cpf_to_recibo_usado[cpf] = nr_usado
            eventos_assinados.append(assinado)
        except Exception as e:
            falhas_pre.append((cpf, f"sign: {e}"[:200]))

    for cpf, err in falhas_pre:
        _registrar_envio(cpf, "erro", erro=err)

    if not eventos_assinados:
        log("nenhum evento valido")
        return {"ok": 0, "erro": len(falhas_pre), "tempo": time.time() - t0}

    # 2) Monta SOAP + envia
    empregador = {"tpInsc": 1, "nrInsc": CNPJ}
    soap = SOAPEnvelopeBuilder.montar_envio(
        eventos_assinados, empregador, empregador.copy(), grupo="3"
    )
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)

    log(f"enviando {len(eventos_assinados)} eventos...")
    try:
        resultado = _soap_enviar(soap, url_envio)
    except Exception as e:
        log(f"EXC envio: {e}")
        for cpf in batch:
            _registrar_envio(cpf, "erro",
                             nr_recibo_usado=cpf_to_recibo_usado.get(cpf),
                             erro=f"send_exc: {e}"[:200])
        return {"ok": 0, "erro": len(batch), "tempo": time.time() - t0}

    if not resultado.get("sucesso"):
        log(f"envio recusado: {resultado.get('descricao')}")
        for cpf in batch:
            _registrar_envio(cpf, "erro",
                             nr_recibo_usado=cpf_to_recibo_usado.get(cpf),
                             codigo=str(resultado.get("codigo_resposta", "")),
                             descricao=resultado.get("descricao", ""),
                             erro=str(resultado.get("descricao", ""))[:200])
        return {"ok": 0, "erro": len(batch), "tempo": time.time() - t0}

    protocolo = resultado.get("protocolo")
    log(f"recebido protocolo={protocolo}, polling...")

    # 3) Polling
    eventos_resp = None
    for tentativa in range(30):
        time.sleep(4)
        try:
            consulta = _soap_consultar(protocolo, url_consulta)
        except Exception as e:
            log(f"  poll {tentativa+1}: {e}")
            continue
        if consulta.get("eventos"):
            eventos_resp = consulta["eventos"]
            break

    ok = 0
    erro = 0
    if eventos_resp is None:
        log("TIMEOUT polling")
        for cpf in batch:
            _registrar_envio(cpf, "erro", protocolo=protocolo,
                             nr_recibo_usado=cpf_to_recibo_usado.get(cpf),
                             erro="timeout polling")
        erro = len(batch)
    else:
        # 4) Por evento, mapeia id -> cpf -> grava
        cpfs_resp = set()
        for evt in eventos_resp:
            evt_id = evt.get("id") or ""
            cpf = id_to_cpf.get(evt_id)
            if not cpf:
                continue
            cpfs_resp.add(cpf)
            nr_recibo_novo = evt.get("nr_recibo")
            cod = str(evt.get("codigo_resposta", ""))
            desc = str(evt.get("descricao", ""))
            ocorr = evt.get("ocorrencias", []) or []
            if nr_recibo_novo:
                _registrar_envio(cpf, "ok", protocolo=protocolo,
                                 nr_recibo_usado=cpf_to_recibo_usado.get(cpf),
                                 nr_recibo_novo=nr_recibo_novo,
                                 codigo=cod, descricao=desc)
                ok += 1
            else:
                erro_desc = f"cod={cod} desc={desc} ocorr={ocorr}"[:500]
                _registrar_envio(cpf, "erro", protocolo=protocolo,
                                 nr_recibo_usado=cpf_to_recibo_usado.get(cpf),
                                 codigo=cod, descricao=desc, erro=erro_desc)
                erro += 1
        # CPFs no batch mas nao retornaram pelo eSocial
        for cpf in batch:
            if cpf not in cpfs_resp and cpf not in [x[0] for x in falhas_pre]:
                _registrar_envio(cpf, "erro", protocolo=protocolo,
                                 nr_recibo_usado=cpf_to_recibo_usado.get(cpf),
                                 erro="ausente_na_resposta")
                erro += 1

    erro += len(falhas_pre)
    dt = time.time() - t0
    log(f"FIM ok={ok} erro={erro} tempo={dt:.1f}s")
    return {"ok": ok, "erro": erro, "tempo": dt}


# ── Backfill envios ja feitos ────────────────────────────────

def _backfill_csv() -> int:
    """Le envios_producao.csv e insere em s1210_cpf_envios (idempotente).
    Tambem garante scope.
    """
    if not os.path.exists(ENVIO_LOG):
        print("Nenhum CSV de envios pra backfill.")
        return 0
    rows = list(csv.DictReader(open(ENVIO_LOG, encoding="utf-8")))
    if not rows:
        return 0
    cpfs = sorted({r["cpf"] for r in rows})
    print(f"Garantindo scope ({len(cpfs)} CPFs)...")
    n = _ensure_scope(cpfs)
    print(f"  scope agora tem {n} CPFs em 2025-05")
    ja = _ja_enviados_db()
    ins = 0
    for r in rows:
        cpf = r["cpf"]
        if cpf in ja:
            continue
        sp = r.get("status_proc", "")
        status = "ok" if sp == "ok" else "erro"
        _registrar_envio(
            cpf, status,
            nr_recibo_novo=r.get("nr_recibo_novo") or None,
            protocolo=r.get("protocolo") or None,
            codigo=r.get("cod_resp") or None,
            descricao=r.get("descricao") or None,
            erro=None if status == "ok" else r.get("descricao"),
        )
        ins += 1
    print(f"Backfill: {ins} linhas inseridas em s1210_cpf_envios")
    return ins


# ── Main ─────────────────────────────────────────────────────

def _carregar_cpfs_geracao() -> list[str]:
    cpfs = []
    with open(GEN_REPORT, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] == "OK":
                cpfs.append(r["cpf"])
    return cpfs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=250, help="quantos CPFs nesta rodada")
    ap.add_argument("--batch", type=int, default=50, help="CPFs por SOAP (max 50)")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--senha", default=os.environ.get("CERT_PFX_PASSWORD"))
    ap.add_argument("--backfill-envios", action="store_true",
                    help="Apenas insere os 110 ja enviados no DB e sai")
    ap.add_argument("--skip-scope", action="store_true",
                    help="Nao tenta criar/atualizar scope")
    args = ap.parse_args()

    if not args.senha:
        print("ERRO: senha PFX ausente (--senha ou CERT_PFX_PASSWORD)")
        return 2
    if args.batch > 50:
        print("ERRO: batch max 50")
        return 2

    if args.backfill_envios:
        _backfill_csv()
        return 0

    todos = _carregar_cpfs_geracao()
    print(f"CSV geracao: {len(todos)} CPFs OK")

    if not args.skip_scope:
        n = _ensure_scope(todos)
        print(f"Scope DB: {n} CPFs em 2025-05 lote 1")

    ja = _ja_enviados_db()
    print(f"DB ja com 'ok'/'erro': {len(ja)}")
    pendentes = [c for c in todos if c not in ja]
    print(f"Pendentes: {len(pendentes)}")
    alvo = pendentes[:args.max]
    print(f"Vou enviar nesta rodada: {len(alvo)}")

    if not alvo:
        print("Nada pra enviar.")
        return 0

    # Cert
    print("Carregando cert...")
    with open(PFX_PATH, "rb") as f:
        pfx_data = f.read()
    info = CertificateManager.validate_pfx(pfx_data, args.senha)
    print(f"  cnpj={info.get('cnpj')} validade={info.get('validade')}")
    _setup_pem(pfx_data, args.senha)

    # Quebra em batches
    batches = [alvo[i:i + args.batch] for i in range(0, len(alvo), args.batch)]
    print(f"Batches: {len(batches)} de ate {args.batch} CPFs cada")
    print(f"Workers paralelos: {args.workers}")

    t0 = time.time()
    tot_ok = 0
    tot_erro = 0
    with ThreadPoolExecutor(max_workers=args.workers, thread_name_prefix="W") as exe:
        futures = {
            exe.submit(_processar_batch, b, i + 1, len(batches)): i
            for i, b in enumerate(batches)
        }
        for fut in as_completed(futures):
            try:
                r = fut.result()
                tot_ok += r["ok"]
                tot_erro += r["erro"]
            except Exception as e:
                print(f"BATCH EXCEPTION: {e}")
                tot_erro += args.batch

    dt = time.time() - t0
    print()
    print("=" * 60)
    print(f"FIM: {tot_ok} ok | {tot_erro} erro | {len(alvo)} total")
    print(f"Tempo: {dt:.1f}s | Media por CPF: {dt/max(len(alvo),1):.2f}s")
    print(f"Throughput: {len(alvo)/max(dt,0.001):.2f} CPFs/s")
    print("=" * 60)
    return 0 if tot_erro == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
