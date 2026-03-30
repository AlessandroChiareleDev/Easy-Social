"""
Script de envio S-1010 alteração para rubrica 156 (DIF. FERIAS)
Ambiente: Homologação (tpAmb=2)

Dados da rubrica 156 (cruzamento_eb):
  - natRubr: 1016 (Férias - Gozadas)
  - INSS atual: 0  → correto: 11
  - IRRF atual: 0  → correto: 13
  - FGTS atual: 0  → correto: 11
"""

import sys
import os
import json

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "easy_social_db",
    "user": "easy_social_user",
    "password": "sua_senha_segura",
}

# ══════════════════════════════════════════════════════════════════
# 1. Dados da rubrica 156 (do cruzamento_eb - base legal correta)
# ══════════════════════════════════════════════════════════════════

RUBRICA_156 = {
    "codRubr": "156",
    "ideTabRubr": "1",
    "iniValid": "2026-03",
    "dscRubr": "DIF. FERIAS",
    "natRubr": 1016,        # Férias - Gozadas
    "tpRubr": 1,             # Vencimento
    "codIncCP": 11,          # INSS: Artigo 28, inciso I, da Lei nº 8.212/91
    "codIncIRRF": 13,        # IRRF: Artigos 3º e 7º da Lei nº 7.713/88
    "codIncFGTS": 11,        # FGTS: Artigo 15 da Lei nº 8.036/90
    "codIncPisPasep": 0,     # Sem incidência PIS/PASEP
}


def main():
    print("=" * 70)
    print("ENVIO S-1010 ALTERAÇÃO — RUBRICA 156 (DIF. FERIAS)")
    print("Ambiente: HOMOLOGAÇÃO (tpAmb=2)")
    print("=" * 70)

    # ── 1. Carregar certificado ativo do banco ──────────────────
    print("\n[1/6] Carregando certificado ativo...")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, cnpj, titular, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            cert_row = cur.fetchone()
    finally:
        conn.close()

    if not cert_row:
        print("ERRO: Nenhum certificado A1 ativo no banco!")
        return

    cert_id, cnpj, titular, arquivo_path, senha_encrypted = cert_row
    print(f"  Certificado #{cert_id}: {titular}")
    print(f"  CNPJ: {cnpj}")

    # Descriptografar senha e ler PFX
    senha = CertificateManager.decrypt_password(senha_encrypted)
    with open(arquivo_path, "rb") as f:
        pfx_data = f.read()
    print("  PFX carregado com sucesso!")

    # ── 2. Gerar XML S-1010 (alteração) ─────────────────────────
    print("\n[2/6] Gerando XML S-1010 alteração...")
    empregador = {"tpInsc": 1, "nrInsc": cnpj}

    xml_bytes = S1010XMLGenerator.gerar_alteracao(empregador, RUBRICA_156)
    print(f"  XML gerado: {len(xml_bytes)} bytes")

    # Mostrar preview
    print("\n  === PREVIEW XML ===")
    from lxml import etree
    root = etree.fromstring(xml_bytes)
    print(etree.tostring(root, pretty_print=True, encoding="unicode")[:2000])
    print("  === FIM PREVIEW ===")

    # ── 3. Assinar XML ──────────────────────────────────────────
    print("\n[3/6] Assinando XML com certificado A1...")
    xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
    print(f"  XML assinado: {len(xml_assinado)} bytes")
    print(f"  Assinatura presente: {'Signature' in xml_assinado.decode('utf-8')}")

    # ── 4. Montar envelope SOAP ─────────────────────────────────
    print("\n[4/6] Montando envelope SOAP...")
    transmissor = {"tpInsc": 1, "nrInsc": cnpj}
    soap_envelope = SOAPEnvelopeBuilder.montar_envio(
        eventos_assinados=[xml_assinado],
        empregador=empregador,
        transmissor=transmissor,
        grupo=1,
    )
    print(f"  Envelope SOAP: {len(soap_envelope)} chars")

    # ── 5. Enviar ao eSocial (Homologação) ──────────────────────
    print("\n[5/6] ENVIANDO ao eSocial (Homologação)...")
    print("  URL:", SOAPEnvelopeBuilder.url_envio())
    resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, senha)

    print("\n  ════════════════════════════════════════")
    print(f"  RESULTADO DO ENVIO:")
    print(f"  Sucesso:          {resultado.get('sucesso')}")
    print(f"  Código Resposta:  {resultado.get('codigo_resposta')}")
    print(f"  Descrição:        {resultado.get('descricao')}")
    print(f"  Protocolo:        {resultado.get('protocolo')}")
    print(f"  DH Recepção:      {resultado.get('dh_recepcao')}")
    if resultado.get("erro"):
        print(f"  ERRO:             {resultado.get('erro')}")
    if resultado.get("ocorrencias"):
        print(f"  Ocorrências:")
        for oc in resultado["ocorrencias"]:
            print(f"    - [{oc.get('tipo')}] {oc.get('codigo')}: {oc.get('descricao')}")
    print("  ════════════════════════════════════════")

    # ── 6. Salvar resultado no banco ────────────────────────────
    print("\n[6/6] Salvando resultado no banco...")
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO esocial_envios
                (tipo_evento, modo, status, protocolo_envio,
                 codigo_resposta, descricao_resposta, total_eventos,
                 rubrica_ids, ocorrencias)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                "S-1010",
                "alteracao",
                "enviado" if resultado.get("sucesso") else "erro",
                resultado.get("protocolo"),
                resultado.get("codigo_resposta"),
                resultado.get("descricao"),
                1,
                json.dumps(["156"]),
                json.dumps(resultado.get("ocorrencias", [])),
            ))
            envio_id = cur.fetchone()[0]
            conn.commit()
            print(f"  Envio salvo no banco com ID: {envio_id}")
    except Exception as e:
        print(f"  Aviso: Erro ao salvar no banco: {e}")
    finally:
        conn.close()

    # ── Resultado final ─────────────────────────────────────────
    protocolo = resultado.get("protocolo")
    if resultado.get("sucesso") and protocolo:
        print(f"\n✅ SUCESSO! Lote recebido pelo eSocial.")
        print(f"   Protocolo: {protocolo}")
        print(f"\n   Para consultar o resultado, execute:")
        print(f"   curl http://localhost:8000/api/esocial/s1010/consultar/{protocolo}")
    else:
        print(f"\n❌ FALHA no envio.")
        if resultado.get("erro"):
            print(f"   Erro: {resultado['erro']}")

    return resultado


if __name__ == "__main__":
    main()
