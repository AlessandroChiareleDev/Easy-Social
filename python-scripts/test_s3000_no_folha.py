"""Test S-3000 exclusion of S-1210 WITHOUT ideFolhaPagto."""
import sys, os, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_signer import S1010XMLSigner as XMLSigner
from lxml import etree
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("s3000")

AMBIENTE = "1"
GRUPO = 2  # S-3000 always grupo 2

# Only try the CURRENT active recibo
RECIBO = "1.1.0000000035299436298"
CPF = "31381951805"
PER_APUR = "2025-09"
TP_EVENTO = "S-1210"

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


def build_s3000_without_folha(empregador, nr_rec_evt, cpf_trab, tp_amb="1"):
    """Build S-3000 XML WITHOUT ideFolhaPagto."""
    NS = "http://www.esocial.gov.br/schema/evt/evtExclusao/v_S_01_03_00"
    from datetime import datetime
    now = datetime.now()
    seq = 1
    tp_insc = int(empregador["tpInsc"])
    nr_insc = str(empregador["nrInsc"])[:8]
    nr_insc_14 = str(empregador["nrInsc"])[:14].ljust(14, "0")
    
    evt_id = f"ID{tp_insc}{nr_insc_14}{now.strftime('%Y%m%d%H%M%S')}{seq:05d}"
    
    root = etree.Element("eSocial", xmlns=NS)
    evt = etree.SubElement(root, "evtExclusao", Id=evt_id)
    
    # ideEvento
    ide = etree.SubElement(evt, "ideEvento")
    etree.SubElement(ide, "tpAmb").text = tp_amb
    etree.SubElement(ide, "procEmi").text = "1"
    etree.SubElement(ide, "verProc").text = "EasySocial_1.0"
    
    # ideEmpregador
    ide_emp = etree.SubElement(evt, "ideEmpregador")
    etree.SubElement(ide_emp, "tpInsc").text = str(tp_insc)
    etree.SubElement(ide_emp, "nrInsc").text = nr_insc
    
    # infoExclusao
    info_exc = etree.SubElement(evt, "infoExclusao")
    etree.SubElement(info_exc, "tpEvento").text = TP_EVENTO
    etree.SubElement(info_exc, "nrRecEvt").text = nr_rec_evt
    
    # ideTrabalhador
    ide_trab = etree.SubElement(info_exc, "ideTrabalhador")
    etree.SubElement(ide_trab, "cpfTrab").text = cpf_trab
    
    # NO ideFolhaPagto!
    
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def main():
    cnpj_full, pfx_data, senha = _load_cert()
    empregador = {"tpInsc": 1, "nrInsc": cnpj_full}
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj_full}

    dry_run = "--dry-run" in sys.argv

    log.info(f"=== S-3000 para S-1210 recibo: {RECIBO} (SEM ideFolhaPagto) ===")
    xml = build_s3000_without_folha(empregador, RECIBO, CPF, tp_amb=AMBIENTE)
    
    if dry_run:
        log.info(f"DRY RUN - XML:\n{xml.decode()}")
        return

    xml_assinado = XMLSigner.assinar(xml, pfx_data, senha)
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador_soap, empregador_soap, grupo=GRUPO
    )

    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    log.info("Enviando...")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        log.error(f"Falha no envio: {resultado}")
        return

    protocolo = resultado["protocolo"]
    log.info(f"Protocolo: {protocolo}")

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(20):
        time.sleep(5)
        soap_c = SOAPEnvelopeBuilder.montar_consulta(protocolo)
        retorno = ESocialClient.consultar_lote(soap_c, pfx_data, senha, url=url_consulta)

        if retorno.get("em_processamento"):
            log.info(f"Aguardando... tentativa {attempt+1}")
            continue

        eventos = retorno.get("eventos", [])
        for ev in eventos:
            nr_recibo = ev.get("nr_recibo")
            ocorrencias = ev.get("ocorrencias", [])
            if nr_recibo:
                log.info(f"SUCESSO! S-3000 aceito, recibo: {nr_recibo}")
                return
            elif ocorrencias:
                desc = "; ".join(f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorrencias)
                log.warning(f"Rejeitado: {desc}")
                return
        
        log.info(f"Resultado consulta: {retorno}")
        return
    
    log.warning("Timeout aguardando resposta")


if __name__ == "__main__":
    main()
