"""
Testes End-to-End para Eventos Periódicos (S-1298 e S-1299)
Pipeline completo: gerar XML → assinar → envelope SOAP (grupo=3) → enviar → consultar
Usa mocking de requests.post mas executa TODO o pipeline real.
"""

import pytest
import re
from unittest.mock import patch, MagicMock
import os

from esocial.certificate_manager import CertificateManager
from esocial.xml_s1298 import S1298XMLGenerator
from esocial.xml_s1299 import S1299XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PFX_PATH = os.path.join(FIXTURES, "cert_valid.pfx")
PFX_PASS = "test1234"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}  # CNPJ raiz APPA

RESPONSAVEL = {
    "nmResp": "Ana Silva",
    "cpfResp": "12345678901",
    "telefone": "1199999999",
    "email": "ana@empresa.com",
}

# ── Respostas mockadas ───────────────────────────────────────────

RESP_ENVIO_201 = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <EnviarLoteEventosResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0">
        <retornoEnvioLoteEventos>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Lote recebido com sucesso.</descResposta>
          </status>
          <dadosRecepcaoLote>
            <dhRecepcao>2026-04-03T14:00:00.000</dhRecepcao>
            <versaoAplicativoRecepcao>8.0.0.0</versaoAplicativoRecepcao>
            <protocoloEnvio>1.2.202604.7777777777</protocoloEnvio>
          </dadosRecepcaoLote>
        </retornoEnvioLoteEventos>
      </eSocial>
    </EnviarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""

RESP_ENVIO_ERRO_301 = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <EnviarLoteEventosResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0">
        <retornoEnvioLoteEventos>
          <status>
            <cdResposta>301</cdResposta>
            <descResposta>Erro na validação do lote.</descResposta>
            <ocorrencias>
              <ocorrencia>
                <tipo>1</tipo>
                <codigo>555</codigo>
                <descricao>Grupo informado não corresponde ao tipo de evento.</descricao>
              </ocorrencia>
            </ocorrencias>
          </status>
        </retornoEnvioLoteEventos>
      </eSocial>
    </EnviarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""


def _resp_consulta_sucesso(nr_recibo, evt_id, ns_evt="evtReabreEvPer"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <ConsultarLoteEventosResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0">
        <retornoProcessamentoLoteEventos>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Lote processado com sucesso.</descResposta>
          </status>
          <retornoEventos>
            <evento Id="{evt_id}">
              <retornoEvento>
                <eSocial xmlns="http://www.esocial.gov.br/schema/evt/{ns_evt}/v_S_01_03_00">
                  <retornoEvento>
                    <processamento>
                      <cdResposta>201</cdResposta>
                      <descResposta>Sucesso.</descResposta>
                      <nrRecibo>{nr_recibo}</nrRecibo>
                    </processamento>
                  </retornoEvento>
                </eSocial>
              </retornoEvento>
            </evento>
          </retornoEventos>
        </retornoProcessamentoLoteEventos>
      </eSocial>
    </ConsultarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""


RESP_CONSULTA_EM_PROCESSAMENTO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <ConsultarLoteEventosResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0">
        <retornoProcessamentoLoteEventos>
          <status>
            <cdResposta>101</cdResposta>
            <descResposta>Lote em processamento. Aguarde.</descResposta>
          </status>
        </retornoProcessamentoLoteEventos>
      </eSocial>
    </ConsultarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""


def _mock_response(text):
    resp = MagicMock()
    resp.status_code = 200
    resp.text = text
    resp.content = text.encode("utf-8")
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture(scope="module")
def pfx_data():
    with open(PFX_PATH, "rb") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════════
# S-1298: Pipeline completo (Reabertura)
# ══════════════════════════════════════════════════════════════════════════════

class TestE2ES1298Pipeline:
    """Pipeline completo: cert → gerar S-1298 → assinar → SOAP grupo=3 → enviar → consultar"""

    @patch("esocial.esocial_client.requests.post")
    def test_pipeline_s1298_completo(self, mock_post, pfx_data):
        # 1. Validar certificado
        info = CertificateManager.validate_pfx(pfx_data, PFX_PASS)
        assert info["valido"] is True

        # 2. Gerar XML S-1298

        xml_bytes = S1298XMLGenerator.gerar(EMPREGADOR, "2025-07", tp_amb="2")
        assert b"evtReabreEvPer" in xml_bytes

        # 3. Assinar
        assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, PFX_PASS)
        assert b"Signature" in assinado

        # 4. Montar SOAP com grupo=3 (periódicos!)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )
        assert "soapenv:Envelope" in envelope
        assert 'grupo="3"' in envelope

        # Extrair Id
        evt_id = re.search(r'<evento\s+Id="([^"]+)"', envelope).group(1)

        # 5. Enviar
        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True
        assert resultado["protocolo"] == "1.2.202604.7777777777"

        # 6. Consultar
        nr_recibo = "1.2.0000000039.2026040314000000001"
        mock_post.return_value = _mock_response(
            _resp_consulta_sucesso(nr_recibo, evt_id, "evtReabreEvPer")
        )
        consulta = ESocialClient.consultar_lote(
            resultado["protocolo"], pfx_data, PFX_PASS
        )

        assert consulta["sucesso"] is True
        assert len(consulta["eventos"]) == 1
        assert consulta["eventos"][0]["nr_recibo"] == nr_recibo

    @patch("esocial.esocial_client.requests.post")
    def test_s1298_soap_grupo_3(self, mock_post, pfx_data):
        """S-1298 DEVE usar grupo=3 (eventos periódicos), não grupo=1"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )
        assert 'grupo="3"' in envelope
        assert 'grupo="1"' not in envelope

    @patch("esocial.esocial_client.requests.post")
    def test_s1298_envio_erro_retorna_estruturado(self, mock_post, pfx_data):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_ERRO_301)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is False
        assert resultado["codigo_resposta"] == "301"
        assert len(resultado["ocorrencias"]) >= 1

    @patch("esocial.esocial_client.requests.post")
    def test_s1298_consulta_em_processamento(self, mock_post, pfx_data):
        """Quando SERPRO ainda está processando → código 101"""
        mock_post.return_value = _mock_response(RESP_CONSULTA_EM_PROCESSAMENTO)
        resultado = ESocialClient.consultar_lote(
            "1.2.202604.7777777777", pfx_data, PFX_PASS
        )
        assert resultado["codigo_resposta"] == "101"

    @patch("esocial.esocial_client.requests.post")
    def test_s1298_resultado_campos_para_db(self, mock_post, pfx_data):
        """Resultado do envio contém todos os campos necessários para esocial_envios"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["protocolo"] is not None
        assert resultado["dh_recepcao"] is not None
        assert resultado["codigo_resposta"] is not None
        assert resultado["descricao"] is not None

    @patch("esocial.esocial_client.requests.post")
    def test_s1298_url_homologacao(self, mock_post, pfx_data):
        """Envio em homologação usa URL producaorestrita"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-07", tp_amb="2")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert "producaorestrita" in kwargs["url"]


# ══════════════════════════════════════════════════════════════════════════════
# S-1299: Pipeline completo (Fechamento)
# ══════════════════════════════════════════════════════════════════════════════

class TestE2ES1299Pipeline:
    """Pipeline completo: cert → gerar S-1299 → assinar → SOAP grupo=3 → enviar → consultar"""

    @patch("esocial.esocial_client.requests.post")
    def test_pipeline_s1299_completo(self, mock_post, pfx_data):
        # 1. Validar certificado
        info = CertificateManager.validate_pfx(pfx_data, PFX_PASS)
        assert info["valido"] is True

        # 2. Gerar XML S-1299
        xml_bytes = S1299XMLGenerator.gerar(
            EMPREGADOR, "2025-07", tp_amb="2"
        )
        assert b"evtFechaEvPer" in xml_bytes
        assert b"infoFech" in xml_bytes

        # 3. Assinar
        assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, PFX_PASS)
        assert b"Signature" in assinado

        # 4. SOAP grupo=3
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )
        assert 'grupo="3"' in envelope

        # Extrair Id
        evt_id = re.search(r'<evento\s+Id="([^"]+)"', envelope).group(1)

        # 5. Enviar
        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True
        protocolo = resultado["protocolo"]

        # 6. Consultar
        nr_recibo = "1.2.0000000039.2026040314000000002"
        mock_post.return_value = _mock_response(
            _resp_consulta_sucesso(nr_recibo, evt_id, "evtFechaEvPer")
        )
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, PFX_PASS)

        assert consulta["sucesso"] is True
        assert consulta["eventos"][0]["nr_recibo"] == nr_recibo

    @patch("esocial.esocial_client.requests.post")
    def test_s1299_soap_grupo_3(self, mock_post, pfx_data):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )
        assert 'grupo="3"' in envelope

    @patch("esocial.esocial_client.requests.post")
    def test_s1299_xml_assinado_contem_infoFech(self, mock_post, pfx_data):
        """Após assinatura, o bloco infoFech deve permanecer intacto"""
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        assert b"infoFech" in assinado
        assert b"evtRemun" in assinado
        assert b"evtPgtos" in assinado

    @patch("esocial.esocial_client.requests.post")
    def test_s1299_envio_erro_301(self, mock_post, pfx_data):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_ERRO_301)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is False

    @patch("esocial.esocial_client.requests.post")
    def test_s1299_http_500(self, mock_post, pfx_data):
        """SERPRO retorna HTTP 500 → não crash"""
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        resp_500 = _mock_response("<html>Internal Server Error</html>")
        resp_500.status_code = 500
        resp_500.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = resp_500

        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)
        assert resultado["sucesso"] is False
        assert "erro" in resultado


# ══════════════════════════════════════════════════════════════════════════════
# S-1298 + S-1299 em sequência (fluxo real: reabre → retifica → fecha)
# ══════════════════════════════════════════════════════════════════════════════

class TestE2EFluxoReabreFecha:
    """Simula o fluxo real: S-1298 (reabre) → ... retificações ... → S-1299 (fecha)"""

    @patch("esocial.esocial_client.requests.post")
    def test_fluxo_reabre_depois_fecha_mesmo_periodo(self, mock_post, pfx_data):
        per_apur = "2025-07"

        # === ETAPA 1: Reabertura (S-1298) ===
        xml_reabre = S1298XMLGenerator.gerar(EMPREGADOR, per_apur, tp_amb="2")
        assinado_reabre = S1010XMLSigner.assinar(xml_reabre, pfx_data, PFX_PASS)
        envelope_reabre = SOAPEnvelopeBuilder.montar_envio(
            [assinado_reabre], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado_reabre = ESocialClient.enviar_lote(
            envelope_reabre, pfx_data, PFX_PASS
        )
        assert resultado_reabre["sucesso"] is True

        # === ETAPA 2: Fechamento (S-1299) ===
        xml_fecha = S1299XMLGenerator.gerar(
            EMPREGADOR, per_apur, tp_amb="2"
        )
        assinado_fecha = S1010XMLSigner.assinar(xml_fecha, pfx_data, PFX_PASS)
        envelope_fecha = SOAPEnvelopeBuilder.montar_envio(
            [assinado_fecha], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado_fecha = ESocialClient.enviar_lote(
            envelope_fecha, pfx_data, PFX_PASS
        )
        assert resultado_fecha["sucesso"] is True

        # Ambos devem receber protocolos distintos? No mock usamos o mesmo,
        # mas no ambiente real cada envio recebe protocolo diferente
        assert resultado_reabre["protocolo"] is not None
        assert resultado_fecha["protocolo"] is not None

    @patch("esocial.esocial_client.requests.post")
    def test_periodos_reais_appa(self, mock_post, pfx_data):
        """Testa com os períodos reais da APPA que precisam retificação"""
        periodos_appa = ["2025-07", "2025-08", "2025-11", "2026-02", "2026-03"]

        for per in periodos_appa:
            xml = S1298XMLGenerator.gerar(EMPREGADOR, per, tp_amb="2")
            assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
            envelope = SOAPEnvelopeBuilder.montar_envio(
                [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
            )

            mock_post.return_value = _mock_response(RESP_ENVIO_201)
            resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

            assert resultado["sucesso"] is True, f"Falhou para {per}"


# ══════════════════════════════════════════════════════════════════════════════
# Testes de mTLS para periódicos
# ══════════════════════════════════════════════════════════════════════════════

class TestE2EMTLSPeriodicos:
    @patch("esocial.esocial_client.requests.post")
    def test_s1298_post_envia_cert_pem(self, mock_post, pfx_data):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert "cert" in kwargs
        cert_path, key_path = kwargs["cert"]
        assert cert_path.endswith(".pem")
        assert key_path.endswith(".pem")

    @patch("esocial.esocial_client.requests.post")
    def test_s1299_headers_corretos(self, mock_post, pfx_data):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-07")
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, grupo="3"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Content-Type"] == "text/xml; charset=utf-8"
        assert "EnviarLoteEventos" in kwargs["headers"]["SOAPAction"]
