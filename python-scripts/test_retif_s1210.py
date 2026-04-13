"""
Try retifying S-1210 (pointing to various recibos) to figure out
which one is currently active, then attempt S-1200 retif.
"""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2, psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s3000 import S3000XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("test_retif")

AMBIENTE = "1"
PER_APUR = "2025-09"
CPF = "31381951805"
GRUPO_PERIODICO = "3"
GRUPO_NAO_PERIODICO = "2"


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


def _enviar_e_consultar(xml_bytes, pfx_data, senha, empregador, grupo, max_poll=15, poll_interval=5):
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
                return {
                    "sucesso": False,
                    "erro": f"Código {codigo}: {descricao}. Ocorrências: {ocorr_txt}",
                    "protocolo": protocolo,
                }
        elif consulta.get("codigo_resposta") == "101":
            log.info(f"  ⏳ Processando... ({attempt+1}/{max_poll})")

    return {"sucesso": False, "erro": f"Timeout após {max_poll} tentativas"}


def main():
    cnpj, pfx_data, senha = _load_cert()
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    # payment data from the original S-1210
    info_pgtos = [
        {"vrLiq": "1339.23", "dtPgto": "2025-09-05", "perRef": "2025-08",
         "tpPgto": "1", "ideDmDev": "01511297"},
        {"vrLiq": "1322.65", "dtPgto": "2025-09-19", "perRef": "2025-09",
         "tpPgto": "1", "ideDmDev": "01511301"}
    ]
    info_ir_complem = {"infoIRCR": [{"tpCR": "056107", "vrCR": ""}]}

    # Known recibos — try retifying S-1210 against each to find which is active
    recibos = [
        "1.1.0000000035006855661",  # Original Oct 6
        "1.1.0000000035299436298",  # Retif Oct 24
        "1.1.0000000039841834445",  # Pipeline retif
    ]

    for recibo in recibos:
        log.info(f"\n=== Tentando RETIFICAR S-1210 contra recibo: {recibo} ===")
        xml = S1210XMLGenerator.gerar(
            empregador=empregador,
            beneficiario={"cpfBenef": CPF},
            info_pgtos=info_pgtos,
            per_apur=PER_APUR,
            ind_retif="2",
            nr_recibo=recibo,
            info_ir_complem=info_ir_complem,
            tp_amb=AMBIENTE,
        )
        result = _enviar_e_consultar(xml, pfx_data, senha, empregador, grupo=GRUPO_PERIODICO)
        if result["sucesso"]:
            log.info(f"  ✅ S-1210 retif OK! Novo recibo: {result['nr_recibo']}")
            new_recibo = result["nr_recibo"]

            # Now try S-3000 to delete this new S-1210
            log.info(f"\n  --- Agora excluindo S-1210 novo recibo: {new_recibo} ---")
            xml_3000 = S3000XMLGenerator.gerar(
                empregador=empregador,
                tp_evento="S-1210",
                nr_rec_evt=new_recibo,
                cpf_trab=CPF,
                per_apur=PER_APUR,
                tp_amb=AMBIENTE,
            )
            result2 = _enviar_e_consultar(xml_3000, pfx_data, senha, empregador, grupo=GRUPO_NAO_PERIODICO)
            if result2["sucesso"]:
                log.info(f"  ✅ S-3000 OK! Recibo: {result2['nr_recibo']}")
                log.info("\n  S-1210 removido! Agora tentando S-1200 retif...")
                return  # Signal that S-1210 is cleared
            else:
                log.info(f"  ❌ S-3000 falhou: {result2.get('erro')}")
        else:
            log.info(f"  ❌ Falhou: {result.get('erro', '?')}")

    log.info("\n=== Nenhuma retificação de S-1210 funcionou ===")


if __name__ == "__main__":
    main()
