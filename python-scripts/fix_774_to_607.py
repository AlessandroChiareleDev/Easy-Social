"""
Correção rubrica 774→607 para CPF 31381951805 (Adriana Pinheiro De Oliveira)
Período: Setembro/2025

Passos:
  1. Retificar S-1200 (trocar rubrica 774 por 607, manter mesmo valor)
  2. Incluir S-1210 (com planSaude - plano de saúde coletivo)
  3. Fechar período (S-1299)

Uso:
  python3 fix_774_to_607.py --dry-run     # Exibe XMLs sem enviar
  python3 fix_774_to_607.py --step1       # Envia apenas S-1200 retif
  python3 fix_774_to_607.py --step2       # Envia apenas S-1210 inclusão
  python3 fix_774_to_607.py --step3       # Envia apenas S-1299
"""
import sys, os, time, logging, argparse
import xml.etree.ElementTree as ET
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import LOCAL_DB_CONFIG
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fix774")

# ===== CONSTANTES =====
AMBIENTE = "1"    # produção
GRUPO = 3          # periódicos
PER_APUR = "2025-09"
CPF_TEST = "31381951805"
S1200_RECIBO = "1.1.0000000035298884020"  # recibo ativo S-1200 (pipeline Oct 24)

# Plano de Saúde
CNPJ_OPERADORA = "44649812000138"
REG_ANS = "359017"
VLR_SAUDE_TIT = "188.51"

# XML do S-1200 pipeline (mais recente)
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


def _enviar_e_consultar(soap_xml, pfx_data, senha, descricao):
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    log.info(f"[{descricao}] Enviando...")
    resultado = ESocialClient.enviar_lote(soap_xml, pfx_data, senha, url=url_envio)

    if not resultado.get("sucesso"):
        log.error(f"[{descricao}] FALHA envio: {resultado.get('erro') or resultado.get('descricao')}")
        return False, resultado

    protocolo = resultado.get("protocolo")
    log.info(f"[{descricao}] Protocolo: {protocolo}")

    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    for attempt in range(25):
        time.sleep(5)
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        if consulta.get("eventos"):
            for evt in consulta["eventos"]:
                nr_recibo = evt.get("nr_recibo")
                if nr_recibo:
                    log.info(f"[{descricao}] ACEITO recibo: {nr_recibo}")
                else:
                    ocorr = evt.get("ocorrencias", [])
                    desc_resp = evt.get("descricao", "")
                    ocorr_txt = "; ".join(
                        f"[{o.get('codigo')}] {o.get('descricao','')[:120]}" for o in ocorr
                    )
                    log.error(f"[{descricao}] REJEITADO: {desc_resp} {ocorr_txt}")
            return True, consulta
        elif consulta.get("codigo_resposta") == "101":
            log.info(f"[{descricao}] Processando... ({attempt+1}/25)")
        else:
            log.warning(
                f"[{descricao}] Resposta: {consulta.get('codigo_resposta')} "
                f"- {consulta.get('descricao')}"
            )
            if attempt > 12:
                return False, consulta

    log.warning(f"[{descricao}] Timeout")
    return False, {"protocolo": protocolo, "status": "timeout"}


# ===================== PASSO 1: S-1200 RETIFICAÇÃO =====================

def _parse_s1200_dmdevs():
    """Lê o S-1200 XML atual e extrai todos os dmDevs, trocando 774→607."""
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

        # infoPerApur
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
                    # indSimples
                    ind_s = rpa.find("e:indSimples", ns)
                    if ind_s is not None:
                        remun["indSimples"] = ind_s.text

                    for it in rpa.findall("e:itensRemun", ns):
                        cod_rubr = it.find("e:codRubr", ns).text
                        ide_tab = it.find("e:ideTabRubr", ns).text
                        vr_rubr = it.find("e:vrRubr", ns).text

                        # ===== SWAP 774 → 607 =====
                        if cod_rubr == "774":
                            log.info(f"  SWAP rubrica 774 -> 607 (valor {vr_rubr})")
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

                    # infoAgNocivo
                    ag = rpa.find("e:infoAgNocivo", ns)
                    if ag is not None:
                        remun["infoAgNocivo"] = {
                            "grauExp": ag.find("e:grauExp", ns).text
                        }

                    estab["remunPerApur"].append(remun)
                estabs.append(estab)
            dm_dict["infoPerApur"] = {"ideEstabLot": estabs}

        dm_devs.append(dm_dict)

    return dm_devs


def gerar_s1200_retif(cnpj):
    """Gera XML S-1200 retificação com rubrica 774→607."""
    dm_devs = _parse_s1200_dmdevs()
    log.info(f"S-1200: {len(dm_devs)} dmDevs extraidos")
    for dm in dm_devs:
        rubrs = []
        if dm.get("infoPerApur"):
            for est in dm["infoPerApur"]["ideEstabLot"]:
                for rpa in est["remunPerApur"]:
                    rubrs = [
                        f"{it['codRubr']}({it['vrRubr']})"
                        for it in rpa["itensRemun"]
                    ]
        log.info(f"  dmDev {dm['ideDmDev']}: {', '.join(rubrs)}")

    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    trabalhador = {"cpfTrab": CPF_TEST}

    xml_bytes = S1200XMLGenerator.gerar_retificacao(
        empregador=empregador,
        trabalhador=trabalhador,
        dm_devs=dm_devs,
        per_apur=PER_APUR,
        nr_recibo=S1200_RECIBO,
        ind_apuracao="1",
        seq=1,
        tp_amb=AMBIENTE,
    )
    return xml_bytes


# ===================== PASSO 2: S-1210 INCLUSÃO =====================

def gerar_s1210_com_plansaude(cnpj):
    """Gera XML S-1210 inclusão com planSaude (plano coletivo)."""
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    beneficiario = {"cpfBenef": CPF_TEST}

    info_pgtos = [
        {
            "dtPgto": "2025-09-05",
            "tpPgto": "1",
            "perRef": "2025-08",
            "ideDmDev": "01511297",
            "vrLiq": "1339.23",
        },
        {
            "dtPgto": "2025-09-19",
            "tpPgto": "1",
            "perRef": "2025-09",
            "ideDmDev": "01511301",
            "vrLiq": "1322.65",
        },
    ]

    info_ir_complem = {
        "infoIRCR": [{"tpCR": "056107"}]
    }

    # Gerar XML base via generator (sem planSaude)
    xml_bytes = S1210XMLGenerator.gerar(
        empregador=empregador,
        beneficiario=beneficiario,
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="1",
        info_ir_complem=info_ir_complem,
        seq=1,
        tp_amb=AMBIENTE,
    )

    # Agora injetar planSaude no XML gerado
    NS_1210 = "http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00"
    root = etree.fromstring(xml_bytes)

    # Achar infoIRComplem
    info_ir = root.find(f".//{{{NS_1210}}}infoIRComplem")
    if info_ir is None:
        raise RuntimeError("infoIRComplem nao encontrado no XML S-1210!")

    # Criar planSaude APÓS infoIRCR (conforme XSD: planSaude vem depois de infoIRCR)
    plan_saude = etree.SubElement(info_ir, f"{{{NS_1210}}}planSaude")
    etree.SubElement(plan_saude, f"{{{NS_1210}}}cnpjOper").text = CNPJ_OPERADORA
    etree.SubElement(plan_saude, f"{{{NS_1210}}}regANS").text = REG_ANS
    etree.SubElement(plan_saude, f"{{{NS_1210}}}vlrSaudeTit").text = VLR_SAUDE_TIT
    # Sem infoDepSau - apenas titular

    log.info("S-1210: planSaude injetado")
    log.info(f"  cnpjOper={CNPJ_OPERADORA}, regANS={REG_ANS}, vlrSaudeTit={VLR_SAUDE_TIT}")

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


# ===================== PASSO 3: S-1299 =====================

def gerar_s1299(cnpj):
    """Gera XML S-1299 fechamento."""
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    xml_bytes = S1299XMLGenerator.gerar(
        empregador=empregador,
        per_apur=PER_APUR,
        ind_retif="1",
        evt_remun="S",
        evt_pgtos="S",
        tp_amb=AMBIENTE,
    )
    return xml_bytes


# ===================== MAIN =====================

def main():
    parser = argparse.ArgumentParser(description="Fix rubrica 774 para 607")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra XMLs")
    parser.add_argument("--step1", action="store_true", help="Envia S-1200 retif")
    parser.add_argument("--step2", action="store_true", help="Envia S-1210 inclusao")
    parser.add_argument("--step3", action="store_true", help="Envia S-1299")
    args = parser.parse_args()

    cnpj_full, pfx_data, senha = _load_cert()
    cnpj_raiz = cnpj_full[:8]
    empregador_soap = {"tpInsc": 1, "nrInsc": cnpj_full}

    log.info(f"=== FIX 774->607 | CPF {CPF_TEST} | {PER_APUR} ===")
    log.info(f"CNPJ: {cnpj_full} (raiz: {cnpj_raiz})")
    log.info(f"Recibo S-1200 a retificar: {S1200_RECIBO}")

    # --- Gerar XMLs ---
    log.info("")
    log.info("--- Gerando S-1200 retificacao ---")
    s1200_xml = gerar_s1200_retif(cnpj_raiz)

    log.info("")
    log.info("--- Gerando S-1210 inclusao (com planSaude) ---")
    s1210_xml = gerar_s1210_com_plansaude(cnpj_raiz)

    if args.dry_run:
        log.info("")
        log.info("=" * 60)
        log.info("DRY RUN - XMLs gerados (nao enviados)")
        log.info("=" * 60)

        # S-1200
        log.info("")
        log.info("--- S-1200 RETIFICACAO ---")
        s1200_str = s1200_xml.decode("utf-8") if isinstance(s1200_xml, bytes) else s1200_xml
        if "<codRubr>774</codRubr>" in s1200_str:
            log.error("ERRO: rubrica 774 ainda presente no XML!")
        elif "<codRubr>607</codRubr>" in s1200_str:
            log.info("OK rubrica 607 presente (774 removida)")
        if f"<nrRecibo>{S1200_RECIBO}</nrRecibo>" in s1200_str:
            log.info(f"OK nrRecibo correto: {S1200_RECIBO}")
        log.info(f"XML size: {len(s1200_str)} bytes")

        # S-1210
        log.info("")
        log.info("--- S-1210 INCLUSAO ---")
        s1210_str = s1210_xml.decode("utf-8") if isinstance(s1210_xml, bytes) else s1210_xml
        if "planSaude" in s1210_str:
            log.info("OK planSaude presente")
        else:
            log.error("ERRO: planSaude NAO presente!")
        if f"<cnpjOper>{CNPJ_OPERADORA}</cnpjOper>" in s1210_str:
            log.info(f"OK cnpjOper={CNPJ_OPERADORA}")
        if f"<vlrSaudeTit>{VLR_SAUDE_TIT}</vlrSaudeTit>" in s1210_str:
            log.info(f"OK vlrSaudeTit={VLR_SAUDE_TIT}")
        if "<indRetif>1</indRetif>" in s1210_str:
            log.info("OK indRetif=1 (inclusao)")
        log.info(f"XML size: {len(s1210_str)} bytes")

        # Print snippet of S-1210 infoIRComplem
        idx = s1210_str.find("infoIRComplem")
        if idx > 0:
            end_idx = s1210_str.find("</ideBenef", idx)
            snippet = s1210_str[idx - 1 : end_idx]
            log.info(f"\nS-1210 infoIRComplem snippet:\n{snippet}")

        log.info("")
        log.info("DRY RUN completo. Use --step1/--step2/--step3 para enviar.")
        return

    # --- Step 1: S-1200 retif ---
    if args.step1:
        log.info("")
        log.info("=== STEP 1: Enviando S-1200 retificacao ===")
        s1200_assinado = XMLSigner.assinar(s1200_xml, pfx_data, senha)
        soap_s1200 = SOAPEnvelopeBuilder.montar_envio(
            [s1200_assinado], empregador_soap, empregador_soap, grupo=GRUPO
        )
        ok, result = _enviar_e_consultar(
            soap_s1200, pfx_data, senha, "S-1200 retif 774->607"
        )
        if not ok:
            log.error("S-1200 FALHOU. Abortando.")
            sys.exit(1)
        log.info("S-1200 retificacao aceita! Agora rode --step2 para S-1210.")

    # --- Step 2: S-1210 inclusão ---
    if args.step2:
        log.info("")
        log.info("=== STEP 2: Enviando S-1210 inclusao (com planSaude) ===")
        s1210_assinado = XMLSigner.assinar(s1210_xml, pfx_data, senha)
        soap_s1210 = SOAPEnvelopeBuilder.montar_envio(
            [s1210_assinado], empregador_soap, empregador_soap, grupo=GRUPO
        )
        ok, result = _enviar_e_consultar(
            soap_s1210, pfx_data, senha, "S-1210 inclusao c/ planSaude"
        )
        if not ok:
            log.error("S-1210 FALHOU. Verifique erros.")
            sys.exit(1)
        log.info("S-1210 inclusao aceita! Agora rode --step3 para S-1299.")

    # --- Step 3: S-1299 ---
    if args.step3:
        log.info("")
        log.info("=== STEP 3: Enviando S-1299 (fechamento) ===")
        s1299_xml = gerar_s1299(cnpj_raiz)
        s1299_assinado = XMLSigner.assinar(s1299_xml, pfx_data, senha)
        soap_s1299 = SOAPEnvelopeBuilder.montar_envio(
            [s1299_assinado], empregador_soap, empregador_soap, grupo=GRUPO
        )
        ok, result = _enviar_e_consultar(
            soap_s1299, pfx_data, senha, "S-1299 fechamento"
        )
        if not ok:
            log.error("S-1299 FALHOU.")
            sys.exit(1)
        log.info("S-1299 aceito! Periodo fechado.")

    if not (args.step1 or args.step2 or args.step3):
        log.info(
            "Nenhuma acao especificada. Use --dry-run, --step1, --step2 ou --step3"
        )


if __name__ == "__main__":
    main()
