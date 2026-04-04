"""
═══════════════════════════════════════════════════════════════════════════════
TESTES DE HOMOLOGAÇÃO — Envio REAL ao SERPRO (producaorestrita)
═══════════════════════════════════════════════════════════════════════════════

Estes testes fazem envio REAL ao ambiente de homologação do eSocial.
NÃO usam mock — conectam via mTLS com o certificado A1 real.

REQUISITOS:
  1. Certificado A1 real (.pfx) salvo na tabela esocial_certificados
  2. Servidor Python (FastAPI) rodando na porta 8000
  3. Conexão com internet

USO:
  # Rodar apenas testes de homologação:
  pytest tests/test_homologacao_periodicos.py -v -s

  # Marcar como skip se sem certificado:
  pytest tests/test_homologacao_periodicos.py -v -s -m homologacao

SEGURANÇA:
  - APENAS ambiente 2 (homologação / producaorestrita)
  - ZERO risco para produção
  - Pode ser executado quantas vezes quiser sem consequências reais

NOTA: Se o certificado não estiver configurado, os testes serão pulados.
═══════════════════════════════════════════════════════════════════════════════
"""

import pytest
import time
import sys
import os

# Adicionar o diretório pai ao path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

# ── Configuração ─────────────────────────────────────────────────

CNPJ_RAIZ_APPA = "05969071"
EMPREGADOR = {"tpInsc": 1, "nrInsc": CNPJ_RAIZ_APPA}

RESPONSAVEL = {
    "nmResp": "Alexandre Teste",
    "cpfResp": "00000000000",     # CPF fictício para homologação
    "telefone": "11999999999",
    "email": "teste@homologacao.com",
}

# Período seguro para testes (não conflita com dados reais)
PERIODO_TESTE = "2020-01"


def _load_cert_from_db():
    """Tenta carregar certificado do banco de dados (mesmo fluxo da API)."""
    try:
        from db_config import get_connection
        from esocial.certificate_manager import CertificateManager

        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT arquivo_path, senha_encrypted
                    FROM esocial_certificados
                    WHERE ativo = true
                    ORDER BY data_upload DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                if not row:
                    return None, None

                arquivo_path, senha_encrypted = row
                senha = CertificateManager.decrypt_password(senha_encrypted)
                with open(arquivo_path, "rb") as f:
                    pfx_data = f.read()
                return pfx_data, senha
        finally:
            conn.close()
    except Exception as e:
        print(f"\n⚠ Não foi possível carregar certificado: {e}")
        return None, None


# Fixture que carrega certificado real (skip se não disponível)
@pytest.fixture(scope="module")
def cert_real():
    pfx_data, senha = _load_cert_from_db()
    if not pfx_data:
        pytest.skip("Certificado A1 real não disponível — pulando testes de homologação")
    return pfx_data, senha


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 1: Validar que o certificado carregado é válido
# ══════════════════════════════════════════════════════════════════════════════

class TestHomologacaoCertificado:
    def test_certificado_valido(self, cert_real):
        from esocial.certificate_manager import CertificateManager
        pfx_data, senha = cert_real
        info = CertificateManager.validate_pfx(pfx_data, senha)
        assert info["valido"] is True
        assert info["cnpj"] is not None
        print(f"\n✅ Certificado válido — CNPJ: {info['cnpj']}, Validade: {info.get('validade_ate', 'N/A')}")


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 2: S-1298 — Envio real de Reabertura ao SERPRO homologação
# ══════════════════════════════════════════════════════════════════════════════

class TestHomologacaoS1298:
    def test_enviar_s1298_homologacao(self, cert_real):
        """
        Envia S-1298 REAL ao ambiente de homologação.
        Resultado esperado: código 201 (sucesso) ou erro de validação (que também é OK — significa que
        a comunicação com SERPRO funcionou, o XML chegou, e o SERPRO processou).
        """
        pfx_data, senha = cert_real

        # 1. Gerar XML S-1298
        xml_bytes = S1298XMLGenerator.gerar(
            EMPREGADOR, PERIODO_TESTE, ind_apuracao="1", tp_amb="2"
        )
        print(f"\n📄 XML S-1298 gerado ({len(xml_bytes)} bytes)")

        # 2. Assinar
        xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
        assert b"Signature" in xml_assinado
        print(f"🔏 XML assinado ({len(xml_assinado)} bytes)")

        # 3. Montar SOAP com grupo=3
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )
        assert 'grupo="3"' in envelope
        print(f"📦 Envelope SOAP montado ({len(envelope)} bytes)")

        # 4. Enviar ao SERPRO (homologação)
        url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)
        assert "producaorestrita" in url_envio
        print(f"🌐 Enviando para: {url_envio}")

        resultado = ESocialClient.enviar_lote(
            envelope, pfx_data, senha, url=url_envio
        )

        # 5. Analisar resultado
        print(f"\n{'='*60}")
        print(f"📋 RESULTADO ENVIO S-1298:")
        print(f"   Sucesso:  {resultado.get('sucesso')}")
        print(f"   Código:   {resultado.get('codigo_resposta')}")
        print(f"   Desc:     {resultado.get('descricao')}")
        print(f"   Protocolo:{resultado.get('protocolo')}")
        print(f"   Recepção: {resultado.get('dh_recepcao')}")
        if resultado.get("ocorrencias"):
            for oc in resultado["ocorrencias"]:
                print(f"   ⚠ [{oc.get('codigo')}] {oc.get('descricao')}")
        if resultado.get("erro"):
            print(f"   ❌ Erro:   {resultado['erro']}")
        print(f"{'='*60}")

        # Comunicação com SERPRO funcinou se recebemos qualquer resposta estruturada
        assert resultado.get("codigo_resposta") is not None, \
            f"SERPRO não retornou resposta estruturada: {resultado}"

        # Salvar protocolo para consulta posterior
        if resultado.get("protocolo"):
            TestHomologacaoS1298._protocolo = resultado["protocolo"]
            TestHomologacaoS1298._pfx = pfx_data
            TestHomologacaoS1298._senha = senha

    def test_consultar_s1298_homologacao(self, cert_real):
        """Consulta o resultado do envio anterior (se teve protocolo)."""
        protocolo = getattr(TestHomologacaoS1298, "_protocolo", None)
        if not protocolo:
            pytest.skip("Envio anterior não gerou protocolo — skip consulta")

        pfx_data = TestHomologacaoS1298._pfx
        senha = TestHomologacaoS1298._senha

        # Aguardar processamento do SERPRO
        print(f"\n⏳ Aguardando 3s para processamento do SERPRO...")
        time.sleep(3)

        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=False)
        print(f"🔍 Consultando protocolo: {protocolo}")

        resultado = ESocialClient.consultar_lote(
            protocolo, pfx_data, senha, url=url_consulta
        )

        print(f"\n{'='*60}")
        print(f"📋 RESULTADO CONSULTA S-1298:")
        print(f"   Sucesso:  {resultado.get('sucesso')}")
        print(f"   Código:   {resultado.get('codigo_resposta')}")
        print(f"   Desc:     {resultado.get('descricao')}")
        if resultado.get("eventos"):
            for evt in resultado["eventos"]:
                print(f"   📌 Evento {evt.get('id', 'N/A')}:")
                print(f"      Código: {evt.get('codigo_resposta')}")
                print(f"      Recibo: {evt.get('nr_recibo', 'N/A')}")
                if evt.get("ocorrencias"):
                    for oc in evt["ocorrencias"]:
                        print(f"      ⚠ [{oc.get('codigo')}] {oc.get('descricao')}")
        print(f"{'='*60}")

        assert resultado.get("codigo_resposta") is not None


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 3: S-1299 — Envio real de Fechamento ao SERPRO homologação
# ══════════════════════════════════════════════════════════════════════════════

class TestHomologacaoS1299:
    def test_enviar_s1299_homologacao(self, cert_real):
        """Envia S-1299 REAL ao ambiente de homologação."""
        pfx_data, senha = cert_real

        # 1. Gerar XML
        xml_bytes = S1299XMLGenerator.gerar(
            EMPREGADOR, PERIODO_TESTE, ind_apuracao="1", tp_amb="2"
        )
        print(f"\n📄 XML S-1299 gerado ({len(xml_bytes)} bytes)")
        assert b"infoFech" in xml_bytes

        # 2. Assinar
        xml_assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, senha)
        print(f"🔏 XML assinado ({len(xml_assinado)} bytes)")

        # 3. SOAP grupo=3
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [xml_assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )
        print(f"📦 Envelope SOAP ({len(envelope)} bytes)")

        # 4. Enviar
        url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)
        assert "producaorestrita" in url_envio
        print(f"🌐 Enviando para: {url_envio}")

        resultado = ESocialClient.enviar_lote(
            envelope, pfx_data, senha, url=url_envio
        )

        # 5. Resultado
        print(f"\n{'='*60}")
        print(f"📋 RESULTADO ENVIO S-1299:")
        print(f"   Sucesso:  {resultado.get('sucesso')}")
        print(f"   Código:   {resultado.get('codigo_resposta')}")
        print(f"   Desc:     {resultado.get('descricao')}")
        print(f"   Protocolo:{resultado.get('protocolo')}")
        if resultado.get("ocorrencias"):
            for oc in resultado["ocorrencias"]:
                print(f"   ⚠ [{oc.get('codigo')}] {oc.get('descricao')}")
        if resultado.get("erro"):
            print(f"   ❌ Erro:   {resultado['erro']}")
        print(f"{'='*60}")

        assert resultado.get("codigo_resposta") is not None

        if resultado.get("protocolo"):
            TestHomologacaoS1299._protocolo = resultado["protocolo"]
            TestHomologacaoS1299._pfx = pfx_data
            TestHomologacaoS1299._senha = senha

    def test_consultar_s1299_homologacao(self, cert_real):
        """Consulta o resultado do envio de S-1299."""
        protocolo = getattr(TestHomologacaoS1299, "_protocolo", None)
        if not protocolo:
            pytest.skip("Envio S-1299 não gerou protocolo")

        print(f"\n⏳ Aguardando 3s para processamento...")
        time.sleep(3)

        url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=False)
        resultado = ESocialClient.consultar_lote(
            protocolo,
            TestHomologacaoS1299._pfx,
            TestHomologacaoS1299._senha,
            url=url_consulta,
        )

        print(f"\n{'='*60}")
        print(f"📋 RESULTADO CONSULTA S-1299:")
        print(f"   Código:   {resultado.get('codigo_resposta')}")
        print(f"   Desc:     {resultado.get('descricao')}")
        if resultado.get("eventos"):
            for evt in resultado["eventos"]:
                print(f"   📌 Evento: código={evt.get('codigo_resposta')}, recibo={evt.get('nr_recibo', 'N/A')}")
                if evt.get("ocorrencias"):
                    for oc in evt["ocorrencias"]:
                        print(f"      ⚠ [{oc.get('codigo')}] {oc.get('descricao')}")
        print(f"{'='*60}")

        assert resultado.get("codigo_resposta") is not None


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 4: Fluxo completo Reabre → Fecha (mesmo período)
# ══════════════════════════════════════════════════════════════════════════════

class TestHomologacaoFluxoCompleto:
    def test_fluxo_reabre_fecha_homologacao(self, cert_real):
        """
        Fluxo real completo em homologação:
        1. S-1298 reabre período 2020-01
        2. Aguarda processamento
        3. S-1299 fecha período 2020-01

        Simula exatamente o que será feito em produção.
        """
        pfx_data, senha = cert_real
        per = PERIODO_TESTE

        print(f"\n{'='*60}")
        print(f"🔄 FLUXO COMPLETO: Reabre → Fecha período {per}")
        print(f"{'='*60}")

        # === ETAPA 1: S-1298 Reabertura ===
        print(f"\n>>> ETAPA 1: Reabrindo {per} (S-1298)...")
        xml_reabre = S1298XMLGenerator.gerar(EMPREGADOR, per, tp_amb="2")
        assinado_reabre = S1010XMLSigner.assinar(xml_reabre, pfx_data, senha)
        envelope_reabre = SOAPEnvelopeBuilder.montar_envio(
            [assinado_reabre], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        url_envio = SOAPEnvelopeBuilder.url_envio(producao=False)
        resultado_reabre = ESocialClient.enviar_lote(
            envelope_reabre, pfx_data, senha, url=url_envio
        )

        print(f"   Código: {resultado_reabre.get('codigo_resposta')} - {resultado_reabre.get('descricao')}")
        assert resultado_reabre.get("codigo_resposta") is not None

        # === ETAPA 2: Aguardar ===
        print(f"\n>>> Aguardando 5s entre reabertura e fechamento...")
        time.sleep(5)

        # === ETAPA 3: S-1299 Fechamento ===
        print(f"\n>>> ETAPA 2: Fechando {per} (S-1299)...")
        xml_fecha = S1299XMLGenerator.gerar(EMPREGADOR, per, tp_amb="2")
        assinado_fecha = S1010XMLSigner.assinar(xml_fecha, pfx_data, senha)
        envelope_fecha = SOAPEnvelopeBuilder.montar_envio(
            [assinado_fecha], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        resultado_fecha = ESocialClient.enviar_lote(
            envelope_fecha, pfx_data, senha, url=url_envio
        )

        print(f"   Código: {resultado_fecha.get('codigo_resposta')} - {resultado_fecha.get('descricao')}")
        assert resultado_fecha.get("codigo_resposta") is not None

        print(f"\n{'='*60}")
        print(f"🏁 FLUXO COMPLETO FINALIZADO")
        print(f"   S-1298: {resultado_reabre.get('codigo_resposta')} - {resultado_reabre.get('descricao')}")
        print(f"   S-1299: {resultado_fecha.get('codigo_resposta')} - {resultado_fecha.get('descricao')}")
        print(f"{'='*60}")


# ══════════════════════════════════════════════════════════════════════════════
# TESTE 5: Segurança — garante que NUNCA envia para produção
# ══════════════════════════════════════════════════════════════════════════════

class TestHomologacaoSeguranca:
    def test_url_envio_nao_producao(self):
        """Verifica que url_envio(producao=False) NUNCA aponta para produção"""
        url = SOAPEnvelopeBuilder.url_envio(producao=False)
        assert "producaorestrita" in url
        assert "envio.esocial.gov.br" not in url

    def test_url_consulta_nao_producao(self):
        url = SOAPEnvelopeBuilder.url_consulta(producao=False)
        assert "producaorestrita" in url
        assert "consulta.esocial.gov.br" not in url

    def test_xml_s1298_tpAmb_2(self):
        """XML gerado com tp_amb='2' DEVE ter tpAmb=2 (homologação)"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01", tp_amb="2")
        from lxml import etree
        ns = "http://www.esocial.gov.br/schema/evt/evtReabreEvPer/v_S_01_03_00"
        root = etree.fromstring(xml)
        tp_amb = root.find(f".//{{{ns}}}tpAmb")
        assert tp_amb.text == "2", "XML S-1298 NÃO está em homologação!"

    def test_xml_s1299_tpAmb_2(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01", tp_amb="2")
        from lxml import etree
        ns = "http://www.esocial.gov.br/schema/evt/evtFechaEvPer/v_S_01_03_00"
        root = etree.fromstring(xml)
        tp_amb = root.find(f".//{{{ns}}}tpAmb")
        assert tp_amb.text == "2", "XML S-1299 NÃO está em homologação!"

    def test_default_ambiente_homologacao(self):
        """Por padrão, geradores devem usar tp_amb='2' (homologação)"""
        xml_1298 = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        xml_1299 = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        assert b">2<" in xml_1298 or b"<tpAmb>2</tpAmb>" in xml_1298
        assert b">2<" in xml_1299 or b"<tpAmb>2</tpAmb>" in xml_1299
