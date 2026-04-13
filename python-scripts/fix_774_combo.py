"""
Fix 774->607: Enviar S-1200 retif + S-1210 retif NO MESMO LOTE.
Isso evita o bloqueio [989] do S-1200 ser rejeitado por S-1210 ativo.
"""
import sys, os, time, logging
import xml.etree.ElementTree as ET
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("combo")

AMBIENTE = "1"
GRUPO = 3
PER_APUR = "2025-09"
CPF_TEST = "31381951805"
S1200_RECIBO = "1.1.0000000035298884020"
S1210_RECIBO = "1.1.0000000035299436298"  # S-1210 ativo a retificar

CNPJ_OPERADORA = "44649812000138"
REG_ANS = "359017"
VLR_SAUDE_TIT = "188.51"

S1200_XML_FILE = "/opt/easy-social/xmls_set2025/ID1059690710000002025102413182600003.S-1200.xml"


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


def _parse_s1200_dmdevs():
    tree = ET.parse(S1200_XML_FILE)
    root = tree.getroot()
    ns = {"e": "http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00"}
    evt = root.find(".//e:evtRemun", ns)
    dm_devs = []

    for dm in evt.findall("e:dmDev", ns):
        dm_dict = {"ideDmDev": dm.find("e:ideDmDev", ns).text}
        cod_categ = dm.find("e:codCateg", ns)
        if cod_categ is not None:
            dm_dict["codCateg"] = cod_categ.text

        ipa = dm.find("e:infoPerApur", ns)
        if ipa is not None:
            estabs = []
            for ie in ipa.findall("e:ideEstabLot", ns):
                estab = {
                    "tpInsc": ie.find("e:tpInsc", ns).text,
                    "nrInsc": ie.find("e:nrInsc", ns).text,
                    "codLotacao": ie.find("e:codLotacao", ns).text,
                    "remunPerApur": [],
                }
                for rpa in ie.findall("e:remunPerApur", ns):
                    remun = {
                        "matricula": rpa.find("e:matricula", ns).text,
                        "itensRemun": [],
                    }
                    ind_s = rpa.find("e:indSimples", ns)
                    if ind_s is not None:
                        remun["indSimples"] = ind_s.text
                    for it in rpa.findall("e:itensRemun", ns):
                        cod_rubr = it.find("e:codRubr", ns).text
                        ide_tab = it.find("e:ideTabRubr", ns).text
                        vr_rubr = it.find("e:vrRubr", ns).text
                        if cod_rubr == "774":
                            log.info(f"  SWAP 774 -> 607 (valor {vr_rubr})")
                            cod_rubr = "607"
                        item = {
                            "codRubr": cod_rubr,
                            "ideTabRubr": ide_tab,
                            "vrRubr": vr_rubr,
                        }
                        ind_apur = it.find("e:indApurIR", ns)
                        if ind_apur is not None:
                            item["indApurIR"] = ind_apur.text
                        qtd = it.find("e:qtdRubr", ns)
                        if qtd is not None:
                            item["qtdRubr"] = qtd.text
                        fator = it.find("e:fatorRubr", ns)
                        if fator is not None:
                            item["fatorRubr"] = fator.text
                        remun["itensRemun"].append(item)
                    ag = rpa.find("e:infoAgNocivo", ns)
                    if ag is not None:
                        remun["infoAgNocivo"] = {"grauExp": ag.find("e:grauExp", ns).text}
                    estab["remunPerApur"].append(remun)
                estabs.append(estab)
            dm_dict["infoPerApur"] = {"ideEstabLot": estabs}
        dm_devs.append(dm_dict)
    return dm_devs


def gerar_s1200_retif(cnpj):
    dm_devs = _parse_s1200_dmdevs()
    log.info(f"S-1200: {len(dm_devs)} dmDevs")
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    trabalhador = {"cpfTrab": CPF_TEST}
    return S1200XMLGenerator.gerar_retificacao(
        empregador=empregador,
        trabalhador=trabalhador,
        dm_devs=dm_devs,
        per_apur=PER_APUR,
        nr_recibo=S1200_RECIBO,
        ind_apuracao="1",
        seq=1,
        tp_amb=AMBIENTE,
    )


def gerar_s1210_retif(cnpj):
    """S-1210 RETIFICACAO (indRetif=2) referenciando S1210_RECIBO, com planSaude."""
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    beneficiario = {"cpfBenef": CPF_TEST}

    info_pgtos = [
        {"dtPgto": "2025-09-05", "tpPgto": "1", "perRef": "2025-08",
         "ideDmDev": "01511297", "vrLiq": "1339.23"},
        {"dtPgto": "2025-09-19", "tpPgto": "1", "perRef": "2025-09",
         "ideDmDev": "01511301", "vrLiq": "1322.65"},
    ]
    info_ir_complem = {"infoIRCR": [{"tpCR": "056107"}]}

    xml_bytes = S1210XMLGenerator.gerar(
        empregador=empregador,
        beneficiario=beneficiario,
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="2",             # RETIFICACAO
        nr_recibo=S1210_RECIBO,    # recibo S-1210 a retificar
        info_ir_complem=info_ir_complem,
        seq=2,                     # seq diferente do S-1200
        tp_amb=AMBIENTE,
    )

    # Injetar planSaude
    NS_1210 = "http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00"
    root = etree.fromstring(xml_bytes)
    info_ir = root.find(f".//{{{NS_1210}}}infoIRComplem")
    if info_ir is None:
        raise RuntimeError("infoIRComplem nao encontrado!")

    plan_saude = etree.SubElement(info_ir, f"{{{NS_1210}}}planSaude")
    etree.SubElement(plan_saude, f"{{{NS_1210}}}cnpjOper").text = CNPJ_OPERADORA
    etree.SubElement(plan_saude, f"{{{NS_1210}}}regANS").text = REG_ANS
    etree.SubElement(plan_saude, f"{{{NS_1210}}}vlrSaudeTit").text = VLR_SAUDE_TIT

    log.info("S-1210 retif: planSaude injetado")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def main():
    dry_run = "--dry-run" in sys.argv
    cnpj_full, pfx_data, senha = _load_cert()
    cnpj_raiz = cnpj_full[:8]
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj_full}

    log.info(f"=== COMBO FIX 774->607 | CPF {CPF_TEST} | {PER_APUR} ===")
    log.info(f"S-1200 recibo: {S1200_RECIBO}")
    log.info(f"S-1210 recibo: {S1210_RECIBO}")

    # Gerar ambos
    s1200_xml = gerar_s1200_retif(cnpj_raiz)
    s1210_xml = gerar_s1210_retif(cnpj_raiz)

    s1200_str = s1200_xml.decode() if isinstance(s1200_xml, bytes) else s1200_xml
    s1210_str = s1210_xml.decode() if isinstance(s1210_xml, bytes) else s1210_xml

    # Validacoes
    assert "<codRubr>774</codRubr>" not in s1200_str, "774 ainda no S-1200!"
    assert "<codRubr>607</codRubr>" in s1200_str, "607 ausente no S-1200!"
    assert "planSaude" in s1210_str, "planSaude ausente no S-1210!"
    assert "<indRetif>2</indRetif>" in s1210_str, "S-1210 nao e retificacao!"
    assert f"<nrRecibo>{S1210_RECIBO}</nrRecibo>" in s1210_str, "nrRecibo S-1210 errado!"
    log.info("Validacoes OK")

    if dry_run:
        log.info("\n=== DRY RUN ===")
        log.info(f"S-1200 size: {len(s1200_str)}, 607 presente, 774 ausente")
        log.info(f"S-1210 size: {len(s1210_str)}, planSaude presente, indRetif=2")

        # Show infoIRComplem
        idx = s1210_str.find("infoIRComplem")
        if idx > 0:
            end = s1210_str.find("</ideBenef", idx)
            log.info(f"S-1210 infoIRComplem:\n{s1210_str[idx-1:end]}")
        return

    # Assinar ambos
    log.info("Assinando XMLs...")
    s1200_signed = XMLSigner.assinar(s1200_xml, pfx_data, senha)
    s1210_signed = XMLSigner.assinar(s1210_xml, pfx_data, senha)

    # Montar lote COMBINADO com ambos
    log.info("Montando lote combinado (S-1200 retif + S-1210 retif)...")
    soap = SOAPEnvelopeBuilder.montar_envio(
        [s1200_signed, s1210_signed],
        empregador_soap, empregador_soap, grupo=GRUPO
    )

    # Enviar
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    log.info(f"Enviando lote combinado... (URL: {url_envio})")
    resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        log.error(f"FALHA envio: {resultado}")
        sys.exit(1)

    protocolo = resultado["protocolo"]
    log.info(f"Protocolo: {protocolo}")

    # Consultar resultado
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(25):
        time.sleep(5)
        soap_c = SOAPEnvelopeBuilder.montar_consulta(protocolo)
        retorno = ESocialClient.consultar_lote(soap_c, pfx_data, senha, url=url_consulta)

        if retorno.get("em_processamento") or retorno.get("codigo_resposta") == "101":
            log.info(f"Processando... ({attempt+1}/25)")
            continue

        eventos = retorno.get("eventos", [])
        if not eventos:
            log.warning(f"Sem eventos na resposta: {retorno}")
            continue

        all_ok = True
        for i, ev in enumerate(eventos):
            nr_recibo = ev.get("nr_recibo")
            ocorr = ev.get("ocorrencias", [])
            if nr_recibo:
                log.info(f"Evento {i+1}: ACEITO recibo={nr_recibo}")
            else:
                desc = "; ".join(f"[{o.get('codigo')}] {o.get('descricao','')[:150]}" for o in ocorr)
                log.error(f"Evento {i+1}: REJEITADO: {desc}")
                all_ok = False

        if all_ok:
            log.info("SUCESSO! Ambos eventos aceitos.")
        else:
            log.error("Um ou mais eventos rejeitados.")
        return

    log.warning("Timeout aguardando resposta")


if __name__ == "__main__":
    main()
