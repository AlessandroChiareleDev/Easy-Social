"""
FASE 5 — Testes de Envio Real ao eSocial (Homologação)
Usa mocking de requests.post para simular respostas do SERPRO.
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PFX_PATH = os.path.join(FIXTURES, "cert_valid.pfx")
PFX_PASS = "test1234"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "12345678000190"}
RUBRICA = {
    "codRubr": "1000",
    "ideTabRubr": "1",
    "iniValid": "2024-01",
    "dscRubr": "Salário Base",
    "natRubr": 1000,
    "tpRubr": 1,
    "codIncCP": 11,
    "codIncIRRF": 11,
    "codIncFGTS": 11,
    "codIncPisPasep": 0,
}

# ── Fixtures ─────────────────────────────────────────────────────

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
            <dhRecepcao>2026-03-27T12:00:00.000</dhRecepcao>
            <versaoAplicativoRecepcao>8.0.0.0</versaoAplicativoRecepcao>
            <protocoloEnvio>1.2.202603.1234567890</protocoloEnvio>
          </dadosRecepcaoLote>
        </retornoEnvioLoteEventos>
      </eSocial>
    </EnviarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""

RESP_ENVIO_ERRO = """<?xml version="1.0" encoding="UTF-8"?>
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
                <descricao>O Id do evento informado na tag evento do lote não corresponde ao Id contido no XML do evento.</descricao>
              </ocorrencia>
            </ocorrencias>
          </status>
        </retornoEnvioLoteEventos>
      </eSocial>
    </EnviarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""


@pytest.fixture(scope="module")
def pfx_data():
    with open(PFX_PATH, "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def soap_envelope(pfx_data):
    xml = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA)
    assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
    return SOAPEnvelopeBuilder.montar_envio(
        eventos_assinados=[assinado],
        empregador=EMPREGADOR,
        transmissor=EMPREGADOR,
        grupo="1",
    )


def _mock_response(text, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.content = text.encode("utf-8")
    resp.raise_for_status = MagicMock()
    return resp


# ── TEST-ENVIO-01: Enviar 1 S-1010 → cdResposta 201 ─────────────
class TestEnvioSucesso:
    @patch("esocial.esocial_client.requests.post")
    def test_envio_retorna_sucesso(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True
        assert resultado["codigo_resposta"] == "201"

    @patch("esocial.esocial_client.requests.post")
    def test_envio_extrai_protocolo(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert resultado["protocolo"] == "1.2.202603.1234567890"

    @patch("esocial.esocial_client.requests.post")
    def test_envio_extrai_dh_recepcao(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert "2026-03-27" in resultado["dh_recepcao"]


# ── TEST-ENVIO-02: mTLS funciona (PFX → PEM) ───────────────────
class TestMTLS:
    def test_extrair_pem_retorna_cert_e_key(self, pfx_data):
        from esocial.esocial_client import ESocialClient
        cert_pem, key_pem = ESocialClient._extrair_pem(pfx_data, PFX_PASS)

        assert b"BEGIN CERTIFICATE" in cert_pem
        assert b"BEGIN" in key_pem  # RSA PRIVATE KEY or PRIVATE KEY

    def test_extrair_pem_senha_errada_raises(self, pfx_data):
        from esocial.esocial_client import ESocialClient
        with pytest.raises(ValueError, match="[Ss]enha"):
            ESocialClient._extrair_pem(pfx_data, "wrongpassword")

    @patch("esocial.esocial_client.requests.post")
    def test_post_recebe_cert_tuple(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert "cert" in kwargs
        cert_path, key_path = kwargs["cert"]
        # Tempfiles are cleaned up after enviar_lote, just verify the tuple was passed
        assert cert_path.endswith(".pem")
        assert key_path.endswith(".pem")


# ── TEST-ENVIO-03: Headers HTTP corretos ─────────────────────────
class TestHeaders:
    @patch("esocial.esocial_client.requests.post")
    def test_content_type_text_xml(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Content-Type"] == "text/xml; charset=utf-8"

    @patch("esocial.esocial_client.requests.post")
    def test_soap_action_header(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert "EnviarLoteEventos" in kwargs["headers"]["SOAPAction"]

    @patch("esocial.esocial_client.requests.post")
    def test_url_homologacao(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert "producaorestrita" in kwargs["url"]


# ── TEST-ENVIO-04: Resposta com erro → estruturado (não crash) ──
class TestEnvioErro:
    @patch("esocial.esocial_client.requests.post")
    def test_erro_retorna_sucesso_false(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_ERRO)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is False
        assert resultado["codigo_resposta"] == "301"

    @patch("esocial.esocial_client.requests.post")
    def test_erro_extrai_ocorrencias(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_ERRO)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert len(resultado["ocorrencias"]) >= 1
        oc = resultado["ocorrencias"][0]
        assert oc["codigo"] == "555"

    @patch("esocial.esocial_client.requests.post")
    def test_http_500_nao_crash(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        resp = _mock_response("<html>Internal Server Error</html>", 500)
        resp.raise_for_status.side_effect = Exception("500 Server Error")
        mock_post.return_value = resp

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is False
        assert "erro" in resultado


# ── TEST-ENVIO-05: Resultado contém dados para persistência no DB ─
class TestDadosPersistencia:
    @patch("esocial.esocial_client.requests.post")
    def test_resultado_tem_protocolo_para_db(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_201)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        # Todos os campos necessários para INSERT no DB
        assert "protocolo" in resultado
        assert "dh_recepcao" in resultado
        assert "codigo_resposta" in resultado
        assert "descricao" in resultado
        assert resultado["protocolo"] is not None

    @patch("esocial.esocial_client.requests.post")
    def test_resultado_erro_tambem_tem_dados(self, mock_post, soap_envelope, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_ENVIO_ERRO)

        resultado = ESocialClient.enviar_lote(soap_envelope, pfx_data, PFX_PASS)

        assert "codigo_resposta" in resultado
        assert "descricao" in resultado
        assert "ocorrencias" in resultado
