"""
Diagnose the S-1200/S-1210 state.
Step 1: Try to include a fresh S-1210 (ind_retif=1)
Step 2: If succeeds, close period (S-1299) to reset state
Step 3: Reopen period (S-1298)  
Step 4: S-3000 the new S-1210
Step 5: S-1200 retif (swap 774→607)
Step 6: Re-include S-1210 (ind_retif=1)
Step 7: S-1299 close
"""
import sys, os, time, logging
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2, psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("diag")

AMBIENTE = "1"
PER_APUR = "2025-09"
CPF = "31381951805"
XMLS_DIR = "/opt/easy-social/xmls_set2025"

info_pgtos = [
    {"vrLiq": "1339.23", "dtPgto": "2025-09-05", "perRef": "2025-08",
     "tpPgto": "1", "ideDmDev": "01511297"},
    {"vrLiq": "1322.65", "dtPgto": "2025-09-19", "perRef": "2025-09",
     "tpPgto": "1", "ideDmDev": "01511301"}
]
info_ir_complem = {"infoIRCR": [{"tpCR": "056107", "vrCR": ""}]}

def _load_cert():
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn.close()
    cnpj, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(cert_path, "rb") as f:
        pfx_data = f.read()
    return cnpj, pfx_data, senha

def _enviar(xml_bytes, pfx_data, senha, empregador, grupo, max_poll=15, poll_interval=5):
    xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador, empregador.copy(), grupo=grupo
    )
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    if not resultado.get("sucesso"):
        return {"sucesso": False, "erro": resultado.get("erro") or resultado.get("descricao")}
    protocolo = resultado["protocolo"]
    log.info(f"  Protocolo: {protocolo}")
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(max_poll):
        time.sleep(poll_interval)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        if consulta.get("eventos"):
            evt = consulta["eventos"][0]
            nr_recibo = evt.get("nr_recibo")
            if nr_recibo:
                return {"sucesso": True, "nr_recibo": nr_recibo, "protocolo": protocolo}
            else:
                ocorr = evt.get("ocorrencias", [])
                ocorr_txt = "; ".join(f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorr)
                codigo = evt.get("codigo_resposta", "?")
                descricao = evt.get("descricao", "")
                return {"sucesso": False, "erro": f"Código {codigo}: {descricao}. Ocorrências: {ocorr_txt}", "protocolo": protocolo}
        elif consulta.get("codigo_resposta") == "101":
            log.info(f"  ⏳ Processando... ({attempt+1}/{max_poll})")
    return {"sucesso": False, "erro": f"Timeout após {max_poll} tentativas"}


def main():
    cnpj, pfx_data, senha = _load_cert()
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    # Step 1: Try to include fresh S-1210
    log.info("=== STEP 1: Incluir S-1210 fresco (ind_retif=1) ===")
    xml = S1210XMLGenerator.gerar(
        empregador=empregador,
        beneficiario={"cpfBenef": CPF},
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="1",
        nr_recibo=None,
        info_ir_complem=info_ir_complem,
        tp_amb=AMBIENTE,
    )
    result = _enviar(xml, pfx_data, senha, empregador, grupo="3")
    if result["sucesso"]:
        new_s1210_recibo = result["nr_recibo"]
        log.info(f"  ✅ S-1210 OK! Recibo: {new_s1210_recibo}")
    else:
        log.error(f"  ❌ S-1210 falhou: {result.get('erro')}")
        log.info("Abortando — não existe S-1210 ativo e não é possível criar um novo")
        return

    # Step 2: Close period
    log.info("\n=== STEP 2: S-1299 Fechar período ===")
    xml = S1299XMLGenerator.gerar(empregador, PER_APUR, tp_amb=AMBIENTE)
    result = _enviar(xml, pfx_data, senha, empregador, grupo="3")
    if result["sucesso"]:
        log.info(f"  ✅ S-1299 OK! Recibo: {result['nr_recibo']}")
    else:
        log.info(f"  ❌ S-1299 falhou: {result.get('erro')}")
        log.info("  (Pode ser porque há inconsistências com S-1210 excluído)")

    # Step 3: Reopen period
    log.info("\n=== STEP 3: S-1298 Reabrir período ===")
    xml = S1298XMLGenerator.gerar(empregador, PER_APUR, tp_amb=AMBIENTE)
    result = _enviar(xml, pfx_data, senha, empregador, grupo="3")
    if result["sucesso"]:
        log.info(f"  ✅ S-1298 OK! Recibo: {result['nr_recibo']}")
    else:
        erro = result.get("erro", "")
        if "já se encontra" in str(erro).lower() or "715" in str(erro):
            log.info("  ✅ Já aberto")
        else:
            log.error(f"  ❌ S-1298 falhou: {erro}")

    # Step 4: S-3000 delete the new S-1210
    log.info(f"\n=== STEP 4: S-3000 Excluir S-1210 novo ({new_s1210_recibo}) ===")
    xml = S3000XMLGenerator.gerar(
        empregador=empregador,
        tp_evento="S-1210",
        nr_rec_evt=new_s1210_recibo,
        cpf_trab=CPF,
        per_apur=PER_APUR,
        tp_amb=AMBIENTE,
    )
    result = _enviar(xml, pfx_data, senha, empregador, grupo="2")
    if result["sucesso"]:
        log.info(f"  ✅ S-3000 OK! Recibo: {result['nr_recibo']}")
    else:
        log.error(f"  ❌ S-3000 falhou: {result.get('erro')}")
        log.info("Abortando — S-3000 falhou")
        return

    # Step 5: S-1200 retif (test with IDENTICAL data first — no swap)
    log.info("\n=== STEP 5: S-1200 Retif (sem alteração, teste) ===")
    # Parse original S-1200 without modifications
    from swap_774_607 import _parse_s1200_xml, _find_s1200_xml
    s1200_path = _find_s1200_xml(CPF)
    dm_devs = _parse_s1200_xml(s1200_path)

    conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                            keepalives_interval=10, keepalives_count=3)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT nr_recibo FROM explorador_eventos
        WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1200'
        ORDER BY nr_recibo DESC LIMIT 1
    """, (CPF, PER_APUR))
    s1200_recibo = cur.fetchone()["nr_recibo"]
    conn.close()

    xml = S1200XMLGenerator.gerar(
        empregador=empregador,
        trabalhador={"cpfTrab": CPF},
        dm_devs=dm_devs,
        per_apur=PER_APUR,
        ind_retif="2",
        nr_recibo=s1200_recibo,
        tp_amb=AMBIENTE,
    )
    result = _enviar(xml, pfx_data, senha, empregador, grupo="3")
    if result["sucesso"]:
        log.info(f"  ✅ S-1200 retif OK! Recibo: {result['nr_recibo']}")
        log.info("  S-1200 retificação funciona! Agora podemos fazer o swap.")
    else:
        log.error(f"  ❌ S-1200 retif falhou: {result.get('erro')}")


if __name__ == "__main__":
    main()
