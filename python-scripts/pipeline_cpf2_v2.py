"""
Pipeline CPF 09820037735 v2 — Correção com dmDevs corretos do S-1210 original.

Fluxo:
  1. S-1298 — Reabrir 2024-12
  2. S-1210 retif — Retificar pagamento (2 infoPgtos, dmDevs corretos)
  3. S-1299 — Fechar 2024-12

NÃO usa WsSolicitarDownloadEventos (preserva cota).
USA ConsultarLoteEventos (polling pós-envio, sem cota).
"""

import sys, os, json, time, requests

sys.path.insert(0, "/opt/easy-social/python-scripts")
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

# ── Config ────────────────────────────────────────────────
CPF = "09820037735"
PER_APUR = "2024-12"
AMBIENTE = "1"  # PRODUÇÃO
IND_APURACAO = "1"  # mensal
API_BASE = "http://localhost:8000"

MAX_POLL_RETRIES = 8
POLL_DELAY = 15
MAX_SEND_RETRIES = 5
SEND_RETRY_DELAY = 10

CONNECTION_ERRORS = [
    "connection aborted", "connectionreseterror", "remotedisconnected",
    "connectionerror", "forcibly closed", "timed out",
]

# S-1210 dados — extraídos do XML original (download nrRecibo)
# Original S-1210 nrRecibo: 1.1.0000000030328699934 (indRetif=1)
S1210_NR_RECIBO = "1.1.0000000030328699934"
S1210_INFO_PGTOS = [
    {
        "dtPgto": "2024-12-06",
        "tpPgto": "1",
        "perRef": "2024-11",
        "ideDmDev": "01512623",
        "vrLiq": "2198",
    },
    {
        "dtPgto": "2024-12-20",
        "tpPgto": "1",
        "perRef": "2024",
        "ideDmDev": "01512666",
        "vrLiq": "1124",
    },
]
S1210_INFO_IR_COMPLEM = {
    "infoIRCR": [{"tpCR": "056107"}]
}


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


def _is_connection_error(resultado):
    if resultado.get("sucesso"):
        return False
    erro = (resultado.get("erro") or resultado.get("descricao") or "").lower()
    return any(kw in erro for kw in CONNECTION_ERRORS)


def _enviar_e_consultar(xml_bytes, pfx_data, senha, empregador, grupo, is_producao):
    signed = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio([signed], empregador, empregador, grupo=grupo)
    url = SOAPEnvelopeBuilder.url_envio(producao=is_producao)

    resultado = None
    for attempt in range(1, MAX_SEND_RETRIES + 1):
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url)
        if resultado.get("sucesso") or not _is_connection_error(resultado):
            break
        print(f"  [RETRY] Tentativa {attempt}/{MAX_SEND_RETRIES} falhou (conexão)")
        if attempt < MAX_SEND_RETRIES:
            time.sleep(SEND_RETRY_DELAY * attempt)
        else:
            return {"sucesso": False, "protocolo": None, "nr_recibo": None,
                    "descricao": f"Conexão falhou após {MAX_SEND_RETRIES} tentativas"}

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
        return {"sucesso": False, "protocolo": None, "nr_recibo": None,
                "descricao": "Sem protocolo no retorno"}

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
    nr_recibo = None
    consulta = None

    for attempt in range(MAX_POLL_RETRIES):
        time.sleep(POLL_DELAY)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)

        if _is_connection_error(consulta):
            print(f"  [POLL-RETRY] Tentativa {attempt+1}/{MAX_POLL_RETRIES}")
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
                    return {"sucesso": False, "protocolo": protocolo, "nr_recibo": None,
                            "codigo_resposta": ev["codigo_resposta"], "descricao": desc, "eventos": eventos}
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


def audit_snapshot(tipo):
    """Captura snapshot via API local."""
    print(f"\n{'='*60}")
    print(f"  AUDIT {tipo.upper()}")
    print(f"{'='*60}")
    resp = requests.post(f"{API_BASE}/api/pipeline-audit/capturar", json={
        "cpf": CPF,
        "per_apur": PER_APUR,
        "tipo": tipo,
        "descricao": f"Snapshot {tipo} v2 — pipeline CPF {CPF}",
        "rubrica_ids": [],
    }, timeout=30)
    data = resp.json()
    if data.get("sucesso"):
        print(f"  ✓ Snapshot #{data['snapshot_id']} capturado")
    else:
        print(f"  ✗ Erro: {data}")
    return data


def main():
    print("=" * 60)
    print(f"  PIPELINE CPF {CPF} — {PER_APUR} — PRODUÇÃO (v2)")
    print(f"  Fluxo: S-1298 → S-1210 retif → S-1299")
    print(f"  SEM S-1200 | SEM download (preserva cota)")
    print(f"  dmDevs: 01512623, 01512666 (do XML original)")
    print("=" * 60)

    # ── Carregar certificado ──
    cert = _load_cert()
    if not cert:
        print("ERRO: Nenhum certificado A1 ativo!")
        sys.exit(1)

    with open(cert["arquivo_path"], "rb") as f:
        pfx_data = f.read()
    senha = cert["senha"]
    cnpj = cert["cnpj"]
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    is_producao = (AMBIENTE == "1")

    results = []

    # ════════════════════════════════════════════
    # STEP 1: S-1298 — Reabrir período 2024-12
    # ════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print(f"  STEP 1: S-1298 Reabrir {PER_APUR}")
    print(f"{'─'*60}")
    try:
        xml = S1298XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)

        # Período já aberto é ok
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

        icon = "✓" if result["sucesso"] else "✗"
        print(f"  {icon} S-1298: {result.get('descricao', 'OK')}")
        if result.get("nr_recibo"):
            print(f"    Recibo: {result['nr_recibo']}")
        results.append(("S-1298", result))

        if not result["sucesso"]:
            print("\n  ABORTANDO — S-1298 falhou!")
            sys.exit(1)
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        sys.exit(1)

    # ════════════════════════════════════════════
    # STEP 2: S-1210 retif — Retificar 2 pagamentos
    # ════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print(f"  STEP 2: S-1210 Retificar pagamentos {PER_APUR}")
    print(f"  Recibo original: {S1210_NR_RECIBO}")
    print(f"  info_pgtos: {json.dumps(S1210_INFO_PGTOS, indent=2)}")
    print(f"  infoIRComplem: {json.dumps(S1210_INFO_IR_COMPLEM)}")
    print(f"{'─'*60}")
    try:
        xml = S1210XMLGenerator.gerar(
            empregador=empregador,
            beneficiario={"cpfBenef": CPF},
            info_pgtos=S1210_INFO_PGTOS,
            per_apur=PER_APUR,
            ind_retif="2",
            nr_recibo=S1210_NR_RECIBO,
            info_ir_complem=S1210_INFO_IR_COMPLEM,
            tp_amb=AMBIENTE,
        )
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)

        icon = "✓" if result["sucesso"] else "✗"
        print(f"  {icon} S-1210 retif: {result.get('descricao', 'OK')}")
        if result.get("nr_recibo"):
            print(f"    Recibo: {result['nr_recibo']}")
        if result.get("codigo_resposta"):
            print(f"    Código: {result['codigo_resposta']}")
        results.append(("S-1210 retif", result))

        if not result["sucesso"]:
            print("\n  ATENÇÃO: S-1210 retif falhou! Continuando com S-1299 para fechar período...")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        results.append(("S-1210 retif", {"sucesso": False, "descricao": str(e)}))

    # ════════════════════════════════════════════
    # STEP 3: S-1299 — Fechar período
    # ════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print(f"  STEP 3: S-1299 Fechar {PER_APUR}")
    print(f"{'─'*60}")
    try:
        xml = S1299XMLGenerator.gerar(empregador, PER_APUR, IND_APURACAO, tp_amb=AMBIENTE)
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, "3", is_producao)

        icon = "✓" if result["sucesso"] else "✗"
        print(f"  {icon} S-1299: {result.get('descricao', 'OK')}")
        if result.get("nr_recibo"):
            print(f"    Recibo: {result['nr_recibo']}")
        results.append(("S-1299", result))
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        results.append(("S-1299", {"sucesso": False, "descricao": str(e)}))

    # ════════════════════════════════════════════
    # Audit PÓS
    # ════════════════════════════════════════════
    audit_snapshot("pos_pipeline")

    # ═══════════════ RESUMO ═══════════════
    print(f"\n{'='*60}")
    print("  RESUMO FINAL")
    print(f"{'='*60}")
    ok = sum(1 for _, r in results if r.get("sucesso"))
    total = len(results)
    for nome, r in results:
        icon = "✓" if r.get("sucesso") else "✗"
        recibo = r.get("nr_recibo", "—")
        print(f"  {icon} {nome}: recibo={recibo}")
    print(f"\n  {ok}/{total} steps OK")
    status = "COMPLETO" if ok == total else "PARCIAL"
    print(f"  STATUS: {status}")
    print(f"{'='*60}")

    # Salvar resultado
    with open(f"/tmp/pipeline_{CPF}_v2_result.json", "w") as f:
        json.dump({
            "cpf": CPF, "per_apur": PER_APUR, "status": status,
            "steps": [{"nome": n, "result": r} for n, r in results]
        }, f, indent=2, default=str)
    print(f"\nResultado salvo em /tmp/pipeline_{CPF}_v2_result.json")


if __name__ == "__main__":
    main()
