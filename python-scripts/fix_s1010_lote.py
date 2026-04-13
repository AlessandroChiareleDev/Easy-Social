"""
Fix S-1010 em LOTE: Corrigir tpRubr de 76 rubricas enviadas como tpRubr=1 (Vencimento)
que deveriam ser tpRubr=2 (Desconto) ou tpRubr=4 (Informativa dedutora).

Bug: _load_rubricas_by_ids() hardcodava tipo="Vencimento" → tpRubr=1 para TODAS.
571 e 572 já foram corrigidas em fix_s1010_tipo.py. Restam 76.

Fontes de dados:
  - cruzamento_eb: descricao, cod_natureza, incid_base_legal_*, ini_valid_esocial
  - explorador_rubricas: tp_rubr real (prioridade)
  - esocial_depara: tp_rubr fallback
  - tabela_marcos: tp_rubr fallback 2
  - esocial_depara: codIncPisPasep
"""
import sys, os, json, time, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2, psycopg2.extras
from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner as XMLSigner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fix_s1010_lote")

AMBIENTE = "1"  # PRODUÇÃO
GRUPO = 1       # tabelas
LOTE_MAX = 50   # máx eventos por lote eSocial

# 76 rubricas erradas (excluindo 571 e 572 já corrigidas)
WRONG_CODES = [
    '509','516','520','521','522','524','526','530','537','544',
    '546','547','550','552','554','555','556','558','566','575',
    '580','582','585','586','587','590','594','595','596','600',
    '605','606','607','610','615','616','619','621','627','631',
    '638','640','641','656','657','658','659','667','677','686',
    '698','701','702','703','709','715','716','724','729','730',
    '733','748','767','772','774','775','779','790','838','842',
    '843','895','899','964','971','1112',
]


def _extract_code(base_legal_str):
    """Extrai código numérico de 'CODE - Base legal text'. Ex: '11 - Artigo 28...' → '11'"""
    if not base_legal_str:
        return "0"
    s = str(base_legal_str).strip()
    if " - " in s:
        return s.split(" - ")[0].strip()
    # Se é só número
    try:
        int(s)
        return s
    except ValueError:
        return "0"


def load_rubrica_data(conn):
    """Carrega todos os dados necessários para as 76 rubricas."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 1) Dados do cruzamento_eb (descricao, natRubr, incidencias, iniValid)
    cur.execute("""
        SELECT cod_rubrica, descricao, cod_natureza,
               incid_base_legal_inss, incid_base_legal_irrf, incid_base_legal_fgts,
               ini_valid_esocial, envio_status
        FROM cruzamento_eb
        WHERE cod_rubrica = ANY(%s)
          AND envio_status IN ('enviado', 'feito')
    """, (WRONG_CODES,))
    cruzamento = {r['cod_rubrica']: dict(r) for r in cur.fetchall()}
    log.info(f"Cruzamento_eb: {len(cruzamento)} rubricas encontradas")
    
    # 2) tpRubr do explorador_rubricas (o REAL do eSocial) — pega DISTINCT não-NULL
    cur.execute("""
        SELECT DISTINCT cod_rubr, tp_rubr
        FROM explorador_rubricas
        WHERE cod_rubr = ANY(%s)
          AND tp_rubr IS NOT NULL
    """, (WRONG_CODES,))
    expl_tp = {}
    for r in cur.fetchall():
        expl_tp[r['cod_rubr']] = int(r['tp_rubr'])
    log.info(f"Explorador tpRubr: {len(expl_tp)} rubricas com tp_rubr real")
    
    # 3) tpRubr do esocial_depara (fallback)
    cur.execute("""
        SELECT cod_rubrica, valor_novo
        FROM esocial_depara
        WHERE campo = 'tpRubr'
          AND cod_rubrica = ANY(%s)
    """, (WRONG_CODES,))
    depara_tp = {str(r['cod_rubrica']): r['valor_novo'] for r in cur.fetchall()}
    log.info(f"Depara tpRubr: {len(depara_tp)} rubricas")
    
    # 4) tpRubr do tabela_marcos (fallback 2)
    cur.execute("""
        SELECT codigo, tipo_rb
        FROM tabela_marcos
        WHERE codigo = ANY(%s)
    """, (WRONG_CODES,))
    marcos_tp = {str(r['codigo']): r['tipo_rb'] for r in cur.fetchall()}
    log.info(f"Marcos tpRubr: {len(marcos_tp)} rubricas")
    
    # 5) codIncPisPasep do depara
    cur.execute("""
        SELECT cod_rubrica, valor_novo
        FROM esocial_depara
        WHERE campo = 'codIncPisPasep'
          AND cod_rubrica = ANY(%s)
    """, (WRONG_CODES,))
    depara_pis = {str(r['cod_rubrica']): r['valor_novo'] for r in cur.fetchall()}
    log.info(f"Depara codIncPisPasep: {len(depara_pis)} rubricas")
    
    # 6) Montar lista final
    rubricas = []
    missing = []
    
    for cod in WRONG_CODES:
        if cod not in cruzamento:
            missing.append(f"{cod} (não encontrado em cruzamento_eb)")
            continue
        
        c = cruzamento[cod]
        
        # tpRubr: explorador > depara > marcos
        tp = expl_tp.get(cod)
        tp_fonte = "explorador"
        if tp is None:
            tp_val = depara_tp.get(cod)
            if tp_val:
                tp = int(tp_val)
                tp_fonte = "depara"
        if tp is None:
            tp_val = marcos_tp.get(cod)
            if tp_val:
                tp = int(tp_val)
                tp_fonte = "marcos"
        
        if tp is None or tp == 1:
            missing.append(f"{cod} (tpRubr={tp}, não tem fonte confiável)")
            continue
        
        rub = {
            "codRubr": cod,
            "ideTabRubr": "1",
            "iniValid": c.get('ini_valid_esocial') or "2018-02",
            "dscRubr": (c.get('descricao') or f"RUBRICA {cod}")[:100],
            "natRubr": _extract_code(c.get('cod_natureza')),
            "tpRubr": tp,
            "codIncCP": _extract_code(c.get('incid_base_legal_inss')),
            "codIncIRRF": _extract_code(c.get('incid_base_legal_irrf')),
            "codIncFGTS": _extract_code(c.get('incid_base_legal_fgts')),
            "codIncPisPasep": depara_pis.get(cod, "00"),
            "_tp_fonte": tp_fonte,
        }
        rubricas.append(rub)
    
    if missing:
        log.warning(f"\n⚠ {len(missing)} rubricas sem dados completos:")
        for m in missing:
            log.warning(f"  - {m}")
    
    return rubricas


def main():
    log.info("=" * 70)
    log.info("FIX S-1010 EM LOTE: 76 rubricas com tpRubr errado")
    log.info("=" * 70)
    
    # Conectar ao Supabase
    conn = psycopg2.connect(**DB_CONFIG, keepalives=1, keepalives_idle=30,
                            keepalives_interval=10, keepalives_count=3)
    
    # Carregar dados
    rubricas = load_rubrica_data(conn)
    conn.close()
    
    log.info(f"\n✓ {len(rubricas)} rubricas prontas para reenvio")
    
    if not rubricas:
        log.error("Nenhuma rubrica pronta. Abortando.")
        return
    
    # Preview
    log.info("\n--- PREVIEW (primeiras 10) ---")
    for rub in rubricas[:10]:
        log.info(f"  {rub['codRubr']:>5} | tpRubr={rub['tpRubr']} ({rub['_tp_fonte']:>10}) | "
                 f"nat={rub['natRubr']:>4} | cp={rub['codIncCP']:>2} irrf={rub['codIncIRRF']:>2} "
                 f"fgts={rub['codIncFGTS']:>2} pis={rub['codIncPisPasep']:>2} | "
                 f"{rub['dscRubr'][:40]}")
    if len(rubricas) > 10:
        log.info(f"  ... e mais {len(rubricas) - 10}")
    
    # Carregar certificado
    conn_local = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn_local.cursor() as cur:
            cur.execute(
                "SELECT cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn_local.close()
    
    if not row:
        log.error("Nenhum certificado A1 ativo!")
        return
    
    cnpj, cert_path, senha_enc = row
    senha = CertificateManager.decrypt_password(senha_enc)
    with open(cert_path, "rb") as f:
        pfx_data = f.read()
    
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    generator = S1010XMLGenerator()
    is_producao = (AMBIENTE == "1")
    
    # Dividir em lotes de 50
    lotes = []
    for i in range(0, len(rubricas), LOTE_MAX):
        lotes.append(rubricas[i:i + LOTE_MAX])
    
    log.info(f"\n{'='*70}")
    log.info(f"Enviando {len(rubricas)} rubricas em {len(lotes)} lote(s)")
    log.info(f"{'='*70}")
    
    total_ok = 0
    total_erro = 0
    erros_detalhe = []
    
    for lote_idx, lote in enumerate(lotes, 1):
        log.info(f"\n{'─'*50}")
        log.info(f"LOTE {lote_idx}/{len(lotes)} — {len(lote)} rubricas")
        log.info(f"{'─'*50}")
        
        # Gerar XMLs do lote
        xmls_assinados = []
        for seq, rub in enumerate(lote, 1):
            try:
                xml_bytes = generator.gerar_alteracao(empregador, rub, seq=seq, tp_amb=AMBIENTE)
                xml_assinado = XMLSigner.assinar(xml_bytes, pfx_data, senha)
                xmls_assinados.append((rub, xml_assinado))
            except Exception as e:
                log.error(f"  ✗ Rubrica {rub['codRubr']}: Erro ao gerar/assinar XML: {e}")
                total_erro += 1
                erros_detalhe.append(f"{rub['codRubr']}: XML error: {e}")
        
        if not xmls_assinados:
            log.error("  Nenhum XML gerado neste lote!")
            continue
        
        # Montar SOAP com todos os XMLs assinados
        soap = SOAPEnvelopeBuilder.montar_envio(
            [xa for _, xa in xmls_assinados],
            empregador, empregador, grupo=GRUPO
        )
        
        # Enviar
        url_envio = SOAPEnvelopeBuilder.url_envio(producao=is_producao)
        log.info(f"  Enviando {len(xmls_assinados)} eventos para {url_envio}...")
        resultado = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
        
        if not resultado.get("sucesso"):
            err = resultado.get("erro") or resultado.get("descricao")
            log.error(f"  ✗ Envio do lote falhou: {err}")
            total_erro += len(xmls_assinados)
            for rub, _ in xmls_assinados:
                erros_detalhe.append(f"{rub['codRubr']}: Envio falhou: {err}")
            continue
        
        protocolo = resultado.get("protocolo")
        log.info(f"  ✓ Lote enviado! Protocolo: {protocolo}")
        
        # Consultar resultado
        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=is_producao)
        lote_ok = 0
        lote_erro = 0
        
        for attempt in range(15):
            time.sleep(5)
            consulta = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
            
            if consulta.get("eventos"):
                for evt in consulta["eventos"]:
                    nr_recibo = evt.get("nr_recibo")
                    cod = evt.get("codigo_resposta", "")
                    desc = evt.get("descricao", "")
                    ocorr = evt.get("ocorrencias", [])
                    
                    # Identificar qual rubrica é
                    evt_id = evt.get("id", "")
                    
                    if nr_recibo:
                        lote_ok += 1
                        log.info(f"    ✅ Recibo: {nr_recibo}")
                    else:
                        ocorr_txt = "; ".join(
                            f"[{o.get('codigo')}] {o.get('descricao','')}" for o in ocorr
                        ) if ocorr else desc
                        lote_erro += 1
                        log.error(f"    ✗ [{cod}] {ocorr_txt}")
                        erros_detalhe.append(f"[{cod}] {ocorr_txt}")
                
                total_ok += lote_ok
                total_erro += lote_erro
                log.info(f"  Lote {lote_idx}: {lote_ok} OK, {lote_erro} erros")
                break
            elif consulta.get("codigo_resposta") == "101":
                log.info(f"  ⏳ Aguardando... (tentativa {attempt+1}/15)")
            else:
                cod_resp = consulta.get("codigo_resposta")
                desc_resp = consulta.get("descricao")
                log.warning(f"  Consulta: [{cod_resp}] {desc_resp}")
                if cod_resp not in ("101", "201", "202"):
                    total_erro += len(xmls_assinados)
                    break
        
        # Pausa entre lotes
        if lote_idx < len(lotes):
            log.info("  Aguardando 5s antes do próximo lote...")
            time.sleep(5)
    
    # Resultado final
    log.info(f"\n{'='*70}")
    log.info(f"RESULTADO FINAL")
    log.info(f"{'='*70}")
    log.info(f"  Total rubricas: {len(rubricas)}")
    log.info(f"  ✅ OK:    {total_ok}")
    log.info(f"  ✗ Erros: {total_erro}")
    
    if erros_detalhe:
        log.info(f"\n  Detalhes dos erros:")
        for e in erros_detalhe:
            log.info(f"    - {e}")
    
    if total_ok == len(rubricas):
        log.info(f"\n  🎉 TODAS as {total_ok} rubricas corrigidas com sucesso!")
    
    log.info(f"{'='*70}")


if __name__ == "__main__":
    main()
