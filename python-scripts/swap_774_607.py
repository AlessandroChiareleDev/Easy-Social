"""
Swap rubrica 774 → 607 para CPF de teste.
Fluxo: S-1298 (reabrir) → S-1200 retif → S-1210 retif → S-1299 (fechar)

Uso: python3 swap_774_607.py --cpf 31381951805 [--dry-run]
"""
import sys, os, time, logging, argparse, json
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
log = logging.getLogger("swap774")

AMBIENTE = "1"       # produção
PER_APUR = "2025-09"
GRUPO = "3"          # periódicos
RUBRICA_ANTIGA = "774"
RUBRICA_NOVA = "607"
XMLS_DIR = "/opt/easy-social/xmls_set2025"

# ── Helpers ─────────────────────────────────────────────────────

def _load_cert():
    """Carrega certificado A1 do banco local."""
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
    """Assina, envelopa, envia e consulta resultado."""
    xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
    transmissor = empregador.copy()
    soap = SOAPEnvelopeBuilder.montar_envio(
        [xml_assinado], empregador, transmissor, grupo=grupo
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
        else:
            log.info(f"  Consulta: {consulta.get('codigo_resposta')} - {consulta.get('descricao')}")

    return {"sucesso": False, "erro": f"Timeout após {max_poll} tentativas", "protocolo": protocolo}


def _parse_s1200_xml(xml_path):
    """Parseia XML S-1200 original e extrai estrutura dm_devs."""
    tree = etree.parse(xml_path)
    root = tree.getroot()

    # Navigate through the download wrapper to find evtRemun
    ns_dl = "http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0"
    ns_1200 = "http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00"

    # Try direct (download envelope) or bare event
    evt = root.find(f".//{{{ns_1200}}}evtRemun")
    if evt is None:
        raise ValueError(f"evtRemun não encontrado em {xml_path}")

    dm_devs = []
    for dm_el in evt.findall(f"{{{ns_1200}}}dmDev"):
        dm = {
            "ideDmDev": dm_el.findtext(f"{{{ns_1200}}}ideDmDev"),
            "codCateg": dm_el.findtext(f"{{{ns_1200}}}codCateg"),
        }

        info_per_apur = dm_el.find(f"{{{ns_1200}}}infoPerApur")
        if info_per_apur is not None:
            estab_list = []
            for ie_el in info_per_apur.findall(f"{{{ns_1200}}}ideEstabLot"):
                estab = {
                    "tpInsc": ie_el.findtext(f"{{{ns_1200}}}tpInsc"),
                    "nrInsc": ie_el.findtext(f"{{{ns_1200}}}nrInsc"),
                    "codLotacao": ie_el.findtext(f"{{{ns_1200}}}codLotacao"),
                }
                remun_list = []
                for rpa_el in ie_el.findall(f"{{{ns_1200}}}remunPerApur"):
                    remun = {
                        "matricula": rpa_el.findtext(f"{{{ns_1200}}}matricula"),
                        "itensRemun": [],
                    }
                    for it_el in rpa_el.findall(f"{{{ns_1200}}}itensRemun"):
                        item = {
                            "codRubr": it_el.findtext(f"{{{ns_1200}}}codRubr"),
                            "ideTabRubr": it_el.findtext(f"{{{ns_1200}}}ideTabRubr"),
                            "vrRubr": it_el.findtext(f"{{{ns_1200}}}vrRubr"),
                        }
                        qtd = it_el.findtext(f"{{{ns_1200}}}qtdRubr")
                        if qtd:
                            item["qtdRubr"] = qtd
                        fator = it_el.findtext(f"{{{ns_1200}}}fatorRubr")
                        if fator:
                            item["fatorRubr"] = fator
                        ind_ap = it_el.findtext(f"{{{ns_1200}}}indApurIR")
                        if ind_ap:
                            item["indApurIR"] = ind_ap
                        remun["itensRemun"].append(item)

                    # infoAgNocivo
                    ag_el = rpa_el.find(f"{{{ns_1200}}}infoAgNocivo")
                    if ag_el is not None:
                        remun["infoAgNocivo"] = {
                            "grauExp": ag_el.findtext(f"{{{ns_1200}}}grauExp")
                        }
                    remun_list.append(remun)
                estab["remunPerApur"] = remun_list
                estab_list.append(estab)
            dm["infoPerApur"] = {"ideEstabLot": estab_list}

        dm_devs.append(dm)

    return dm_devs


def _swap_rubrica(dm_devs, old_code, new_code):
    """Troca codRubr old_code → new_code em todos os itensRemun. Retorna contagem."""
    count = 0
    for dm in dm_devs:
        ipa = dm.get("infoPerApur", {})
        for est in ipa.get("ideEstabLot", []):
            for remun in est.get("remunPerApur", []):
                for item in remun.get("itensRemun", []):
                    if item["codRubr"] == old_code:
                        item["codRubr"] = new_code
                        count += 1
    return count


def _find_s1200_xml(cpf):
    """Encontra o XML S-1200 mais recente para esse CPF no diretório."""
    import subprocess
    result = subprocess.run(
        ["grep", "-rl", cpf, XMLS_DIR],
        capture_output=True, text=True, timeout=60
    )
    files = [f for f in result.stdout.strip().split("\n") if f and "S-1200" in f]
    if not files:
        return None
    # Return the one with highest recibo (latest retification)
    # The files are named by event ID which may not correspond to recibo order
    # So we parse and find the most recent by indRetif chain
    files.sort()
    return files[-1]  # Last one should be most recent by event ID


def main():
    parser = argparse.ArgumentParser(description="Swap rubrica 774→607 no S-1200/S-1210")
    parser.add_argument("--cpf", required=True, help="CPF (11 dígitos)")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que faria")
    args = parser.parse_args()

    cpf = args.cpf.replace(".", "").replace("-", "").strip()
    dry_run = args.dry_run

    log.info(f"{'[DRY-RUN] ' if dry_run else ''}Swap {RUBRICA_ANTIGA}→{RUBRICA_NOVA} para CPF {cpf}")

    # ── 0. Carregar certificado e dados ──────────────────────────
    cnpj_cert, pfx_data, senha = _load_cert()
    empregador = {"tpInsc": 1, "nrInsc": cnpj_cert}

    # ── 0.1. Encontrar XML S-1200 original ──────────────────────
    log.info("Buscando XML S-1200 original...")
    s1200_xml_path = _find_s1200_xml(cpf)
    if not s1200_xml_path:
        log.error(f"XML S-1200 não encontrado para CPF {cpf} em {XMLS_DIR}")
        return

    log.info(f"  XML encontrado: {s1200_xml_path}")

    # ── 0.2. Parsear e modificar ─────────────────────────────────
    dm_devs = _parse_s1200_xml(s1200_xml_path)
    log.info(f"  {len(dm_devs)} dmDevs encontrados")

    swap_count = _swap_rubrica(dm_devs, RUBRICA_ANTIGA, RUBRICA_NOVA)
    if swap_count == 0:
        log.warning(f"  ⚠ Rubrica {RUBRICA_ANTIGA} NÃO encontrada nos itensRemun!")
        return
    log.info(f"  ✓ {swap_count} ocorrência(s) de {RUBRICA_ANTIGA} → {RUBRICA_NOVA}")

    # ── 0.3. Buscar recibos atuais ──────────────────────────────
    conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                            keepalives_interval=10, keepalives_count=3)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # S-1200: recibo mais recente do explorador
    cur.execute("""
        SELECT nr_recibo FROM explorador_eventos
        WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1200'
        ORDER BY nr_recibo DESC LIMIT 1
    """, (cpf, PER_APUR))
    row = cur.fetchone()
    s1200_nr_recibo = row["nr_recibo"]
    log.info(f"  S-1200 recibo atual: {s1200_nr_recibo}")

    # S-1210: recibo retificado (do pipeline) E original
    s1210_nr_recibo_retif = None
    s1210_nr_recibo_original = None
    cur.execute("""
        SELECT nr_recibo_original, nr_recibo_novo FROM pipeline_cpf_results
        WHERE cpf = %s AND nr_recibo_novo IS NOT NULL
        ORDER BY id DESC LIMIT 1
    """, (cpf,))
    row = cur.fetchone()
    if row:
        s1210_nr_recibo_retif = row["nr_recibo_novo"]
        s1210_nr_recibo_original = row["nr_recibo_original"]
        log.info(f"  S-1210 recibo retif (pipeline): {s1210_nr_recibo_retif}")
        log.info(f"  S-1210 recibo original: {s1210_nr_recibo_original}")
    else:
        cur.execute("""
            SELECT nr_recibo FROM explorador_eventos
            WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1210'
            ORDER BY nr_recibo DESC LIMIT 1
        """, (cpf, PER_APUR))
        row = cur.fetchone()
        s1210_nr_recibo_original = row["nr_recibo"]
        log.info(f"  S-1210 recibo (explorador, sem retif): {s1210_nr_recibo_original}")

    # S-1210: pagamentos e infoIRCR
    cur.execute("""
        SELECT pagamentos, info_ir_cr FROM pipeline_cpf_results
        WHERE cpf = %s ORDER BY id DESC LIMIT 1
    """, (cpf,))
    row = cur.fetchone()
    if row and row["pagamentos"]:
        info_pgtos = row["pagamentos"]
        info_ir_cr = row["info_ir_cr"]
    else:
        # Fallback: explorador
        cur.execute("""
            SELECT dados_json FROM explorador_eventos
            WHERE cpf = %s AND per_apur = %s AND tipo_evento = 'S-1210'
            ORDER BY nr_recibo DESC LIMIT 1
        """, (cpf, PER_APUR))
        row = cur.fetchone()
        dados = row["dados_json"]
        info_pgtos = dados.get("pagamentos", [])
        info_ir_cr = dados.get("infoIRCR", [])

    conn.close()

    log.info(f"  S-1210 pagamentos: {len(info_pgtos)}")
    log.info(f"  S-1210 infoIRCR: {info_ir_cr}")

    # ── Preview ──────────────────────────────────────────────────
    log.info("\n=== RESUMO DA OPERAÇÃO ===")
    log.info(f"  CPF: {cpf}")
    log.info(f"  Swap: rubrica {RUBRICA_ANTIGA} → {RUBRICA_NOVA}")
    log.info(f"  S-1200 retif contra: {s1200_nr_recibo}")
    log.info(f"  S-1210 recibo retif: {s1210_nr_recibo_retif}")
    log.info(f"  S-1210 recibo original: {s1210_nr_recibo_original}")
    for dm in dm_devs:
        ipa = dm.get("infoPerApur", {})
        for est in ipa.get("ideEstabLot", []):
            for remun in est.get("remunPerApur", []):
                for item in remun.get("itensRemun", []):
                    if item["codRubr"] == RUBRICA_NOVA:
                        log.info(f"  → dmDev={dm['ideDmDev']} codRubr={item['codRubr']} vr={item['vrRubr']}")

    if dry_run:
        log.info("\n[DRY-RUN] Nenhum evento enviado.")
        return

    # ── STEP 1: S-1298 (reabrir período) ────────────────────────
    log.info("\n=== STEP 1: S-1298 Reabertura ===")
    xml_1298 = S1298XMLGenerator.gerar(empregador, PER_APUR, tp_amb=AMBIENTE)
    result = _enviar_e_consultar(xml_1298, pfx_data, senha, empregador, grupo=GRUPO)
    if result["sucesso"]:
        log.info(f"  ✓ S-1298 OK — Recibo: {result['nr_recibo']}")
    else:
        # Check if already open (error 715)
        erro = result.get("erro", "")
        if "715" in str(erro) or "já se encontra aberto" in str(erro).lower() or "já se encontra" in str(erro).lower():
            log.info("  ✓ Período já estava aberto")
        else:
            log.error(f"  ✗ S-1298 FALHOU: {erro}")
            return

    # ── STEP 2: S-3000 (excluir S-1210 para liberar dmDevs) ────
    # Se há retificação do pipeline, excluir primeiro ela, depois o original.
    # Se não há retificação, excluir apenas o original.
    recibos_para_excluir = []
    if s1210_nr_recibo_retif:
        recibos_para_excluir.append(("retif", s1210_nr_recibo_retif))
    if s1210_nr_recibo_original:
        recibos_para_excluir.append(("original", s1210_nr_recibo_original))

    for label, nr_recibo_excluir in recibos_para_excluir:
        log.info(f"\n=== STEP 2: S-3000 Excluir S-1210 ({label}: {nr_recibo_excluir}) ===")
        xml_3000 = S3000XMLGenerator.gerar(
            empregador=empregador,
            tp_evento="S-1210",
            nr_rec_evt=nr_recibo_excluir,
            cpf_trab=cpf,
            per_apur=PER_APUR,
            tp_amb=AMBIENTE,
        )
        # S-3000 uses grupo "2" (non-periodic events)
        result = _enviar_e_consultar(xml_3000, pfx_data, senha, empregador, grupo="2")
        if result["sucesso"]:
            log.info(f"  ✓ S-3000 OK — Recibo: {result['nr_recibo']}")
        else:
            erro = result.get("erro", "")
            # If already excluded, not found, or incompatible (already gone), that's OK
            if any(kw in str(erro).lower() for kw in ["não encontrado", "já foi exclu", "incompatíveis", "536"]):
                log.info(f"  ✓ S-1210 ({label}) já estava excluído/não encontrado, continuando")
            else:
                log.error(f"  ✗ S-3000 FALHOU ({label}): {erro}")
                return

    # ── STEP 3: S-1200 Retificação ──────────────────────────────
    log.info("\n=== STEP 3: S-1200 Retificação ===")
    xml_1200 = S1200XMLGenerator.gerar(
        empregador=empregador,
        trabalhador={"cpfTrab": cpf},
        dm_devs=dm_devs,
        per_apur=PER_APUR,
        ind_retif="2",
        nr_recibo=s1200_nr_recibo,
        tp_amb=AMBIENTE,
    )
    result = _enviar_e_consultar(xml_1200, pfx_data, senha, empregador, grupo=GRUPO)
    if result["sucesso"]:
        s1200_novo_recibo = result["nr_recibo"]
        log.info(f"  ✓ S-1200 OK — Recibo: {s1200_novo_recibo}")
    else:
        log.error(f"  ✗ S-1200 FALHOU: {result.get('erro')}")
        return

    # ── STEP 4: S-1210 Inclusão (re-incluir após exclusão) ─────
    log.info("\n=== STEP 4: S-1210 Inclusão ===")

    # Build infoIRComplem
    info_ir_complem = None
    if info_ir_cr:
        info_ir_complem = {"infoIRCR": info_ir_cr}

    xml_1210 = S1210XMLGenerator.gerar(
        empregador=empregador,
        beneficiario={"cpfBenef": cpf},
        info_pgtos=info_pgtos,
        per_apur=PER_APUR,
        ind_retif="1",
        nr_recibo=None,
        info_ir_complem=info_ir_complem,
        tp_amb=AMBIENTE,
    )
    result = _enviar_e_consultar(xml_1210, pfx_data, senha, empregador, grupo=GRUPO)
    if result["sucesso"]:
        s1210_novo_recibo = result["nr_recibo"]
        log.info(f"  ✓ S-1210 OK — Recibo: {s1210_novo_recibo}")
    else:
        log.error(f"  ✗ S-1210 FALHOU: {result.get('erro')}")
        log.info("  ⚠ S-1200 foi aceito mas S-1210 falhou. Período ficará aberto.")
        return

    # ── STEP 5: S-1299 (fechar período) ─────────────────────────
    log.info("\n=== STEP 5: S-1299 Fechamento ===")
    xml_1299 = S1299XMLGenerator.gerar(empregador, PER_APUR, tp_amb=AMBIENTE)
    result = _enviar_e_consultar(xml_1299, pfx_data, senha, empregador, grupo=GRUPO)
    if result["sucesso"]:
        log.info(f"  ✓ S-1299 OK — Recibo: {result['nr_recibo']}")
    else:
        log.warning(f"  ⚠ S-1299 falhou: {result.get('erro')}")
        log.info("  Período ficará aberto — pode fechar manualmente depois")

    # ── Resultado final ──────────────────────────────────────────
    log.info("\n" + "="*50)
    log.info(f"✅ SWAP CONCLUÍDO — CPF {cpf}")
    log.info(f"   Rubrica {RUBRICA_ANTIGA} → {RUBRICA_NOVA}")
    log.info(f"   S-1200 novo recibo: {s1200_novo_recibo}")
    log.info(f"   S-1210 novo recibo: {s1210_novo_recibo}")
    log.info("="*50)


if __name__ == "__main__":
    main()
