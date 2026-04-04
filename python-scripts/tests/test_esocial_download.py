"""
Testes para Download Cirúrgico e Consulta de Identificadores eSocial.
Usa mocking de requests.post para simular respostas do SERPRO.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PFX_PATH = os.path.join(FIXTURES, "cert_valid.pfx")
PFX_PASS = "test1234"

# ── Empregador padrão para testes ─────────────────────────────────

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071000110"}

# ── Respostas mockadas — Consultar Identificadores ────────────────

RESP_IDENT_TRABALHADOR_SUCESSO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <ConsultarIdentificadoresEventosTrabalhadorResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0">
        <retornoConsultaIdentificadoresEvts>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Consulta realizada com sucesso.</descResposta>
          </status>
          <retornoIdentificadoresEvts>
            <regEvts>
              <id>ID1059690710002025010112345600001</id>
              <nrRec>1.2.0000000001.2025010112000000001</nrRec>
            </regEvts>
            <regEvts>
              <id>ID1059690710002025010112345600002</id>
              <nrRec>1.2.0000000001.2025010112000000002</nrRec>
            </regEvts>
          </retornoIdentificadoresEvts>
        </retornoConsultaIdentificadoresEvts>
      </eSocial>
    </ConsultarIdentificadoresEventosTrabalhadorResult>
  </soapenv:Body>
</soapenv:Envelope>"""

RESP_IDENT_TRABALHADOR_VAZIO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <ConsultarIdentificadoresEventosTrabalhadorResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0">
        <retornoConsultaIdentificadoresEvts>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Consulta realizada com sucesso. Nenhum evento encontrado.</descResposta>
          </status>
        </retornoConsultaIdentificadoresEvts>
      </eSocial>
    </ConsultarIdentificadoresEventosTrabalhadorResult>
  </soapenv:Body>
</soapenv:Envelope>"""

RESP_IDENT_EMPREGADOR_SUCESSO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <ConsultarIdentificadoresEventosEmpregadorResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0">
        <retornoConsultaIdentificadoresEvts>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Consulta realizada com sucesso.</descResposta>
          </status>
          <retornoIdentificadoresEvts>
            <regEvts>
              <id>ID1059690710002025010112345600010</id>
              <nrRec>1.2.0000000001.2025010112000000010</nrRec>
            </regEvts>
          </retornoIdentificadoresEvts>
        </retornoConsultaIdentificadoresEvts>
      </eSocial>
    </ConsultarIdentificadoresEventosEmpregadorResult>
  </soapenv:Body>
</soapenv:Envelope>"""

# ── Respostas mockadas — Download ─────────────────────────────────

RESP_DOWNLOAD_SUCESSO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <SolicitarDownloadEventosPorNrReciboResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
        <retornoProcessamentoDownload>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Download realizado com sucesso.</descResposta>
          </status>
          <arquivo>
            <evento>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00">
                <evtRemun Id="ID1059690710002025010112345600001">
                  <ideEvento>
                    <indRetif>1</indRetif>
                    <perApur>2025-01</perApur>
                  </ideEvento>
                  <ideEmpregador>
                    <tpInsc>1</tpInsc>
                    <nrInsc>05969071</nrInsc>
                  </ideEmpregador>
                  <ideTrabalhador>
                    <cpfTrab>06184644173</cpfTrab>
                  </ideTrabalhador>
                </evtRemun>
              </eSocial>
            </evento>
            <recibo>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/retornoEvento/v_S_01_03_00">
                <retornoEvento>
                  <processamento>
                    <cdResposta>201</cdResposta>
                    <nrRecibo>1.2.0000000001.2025010112000000001</nrRecibo>
                  </processamento>
                </retornoEvento>
              </eSocial>
            </recibo>
          </arquivo>
        </retornoProcessamentoDownload>
      </eSocial>
    </SolicitarDownloadEventosPorNrReciboResult>
  </soapenv:Body>
</soapenv:Envelope>"""

RESP_DOWNLOAD_POR_ID_SUCESSO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <SolicitarDownloadEventosPorIdResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
        <retornoProcessamentoDownload>
          <status>
            <cdResposta>201</cdResposta>
            <descResposta>Download realizado com sucesso.</descResposta>
          </status>
          <arquivo>
            <evento>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00">
                <evtPgtos Id="ID1059690710002025010112345600002">
                  <ideEvento>
                    <indRetif>1</indRetif>
                    <perApur>2025-01</perApur>
                  </ideEvento>
                  <ideEmpregador>
                    <tpInsc>1</tpInsc>
                    <nrInsc>05969071</nrInsc>
                  </ideEmpregador>
                  <ideBenef>
                    <cpfBenef>06184644173</cpfBenef>
                  </ideBenef>
                </evtPgtos>
              </eSocial>
            </evento>
            <recibo>
              <eSocial xmlns="http://www.esocial.gov.br/schema/evt/retornoEvento/v_S_01_03_00">
                <retornoEvento>
                  <processamento>
                    <cdResposta>201</cdResposta>
                    <nrRecibo>1.2.0000000001.2025010112000000002</nrRecibo>
                  </processamento>
                </retornoEvento>
              </eSocial>
            </recibo>
          </arquivo>
        </retornoProcessamentoDownload>
      </eSocial>
    </SolicitarDownloadEventosPorIdResult>
  </soapenv:Body>
</soapenv:Envelope>"""

RESP_DOWNLOAD_ERRO = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <SolicitarDownloadEventosPorNrReciboResult>
      <eSocial xmlns="http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0">
        <retornoProcessamentoDownload>
          <status>
            <cdResposta>301</cdResposta>
            <descResposta>Erro no processamento do download.</descResposta>
          </status>
        </retornoProcessamentoDownload>
      </eSocial>
    </SolicitarDownloadEventosPorNrReciboResult>
  </soapenv:Body>
</soapenv:Envelope>"""


# ── Helpers ───────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pfx_data():
    with open(PFX_PATH, "rb") as f:
        return f.read()


def _mock_response(text, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.content = text.encode("utf-8")
    resp.raise_for_status = MagicMock()
    return resp


# ══════════════════════════════════════════════════════════════════
# SOAP Builder Tests
# ══════════════════════════════════════════════════════════════════


class TestSoapBuilderDownloadURLs:
    def test_url_identificadores_homologacao(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        url = SOAPEnvelopeBuilder.url_identificadores(producao=False)
        assert "producaorestrita" in url
        assert "WsConsultarIdentificadoresEventos" in url

    def test_url_identificadores_producao(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        url = SOAPEnvelopeBuilder.url_identificadores(producao=True)
        assert "webservices.download.esocial.gov.br" in url
        assert "WsConsultarIdentificadoresEventos" in url

    def test_url_download_homologacao(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        url = SOAPEnvelopeBuilder.url_download(producao=False)
        assert "producaorestrita" in url
        assert "WsSolicitarDownloadEventos" in url

    def test_url_download_producao(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        url = SOAPEnvelopeBuilder.url_download(producao=True)
        assert "webservices.download.esocial.gov.br" in url
        assert "WsSolicitarDownloadEventos" in url


class TestSoapBuilderInnerXML:
    def test_inner_ident_trabalhador(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        xml = SOAPEnvelopeBuilder.inner_consulta_ident_trabalhador(
            EMPREGADOR, "06184644173", "2025-01-01", "2025-12-31"
        )
        assert "cpfTrab" in xml
        assert "06184644173" in xml
        assert "2025-01-01" in xml
        assert "05969071" in xml
        assert "identificadores-eventos/trabalhador" in xml

    def test_inner_ident_empregador(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        xml = SOAPEnvelopeBuilder.inner_consulta_ident_empregador(
            EMPREGADOR, "S-1200", "2025-01"
        )
        assert "tpEvt" in xml
        assert "S-1200" in xml
        assert "perApur" in xml
        assert "2025-01" in xml
        assert "identificadores-eventos/empregador" in xml

    def test_inner_download_por_id(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        xml = SOAPEnvelopeBuilder.inner_download_por_id(
            EMPREGADOR, ["ID1059690710002025010112345600001"]
        )
        assert "solicDownloadEvtsPorId" in xml
        assert "ID1059690710002025010112345600001" in xml
        assert "download/solicitacao/id" in xml

    def test_inner_download_por_id_multiplos(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        ids = ["ID001", "ID002", "ID003"]
        xml = SOAPEnvelopeBuilder.inner_download_por_id(EMPREGADOR, ids)
        for eid in ids:
            assert f"<id>{eid}</id>" in xml

    def test_inner_download_por_nrrecibo(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        xml = SOAPEnvelopeBuilder.inner_download_por_nrrecibo(
            EMPREGADOR, ["1.2.0000000001.2025010112000000001"]
        )
        assert "solicDownloadEventosPorNrRecibo" in xml
        assert "1.2.0000000001.2025010112000000001" in xml
        assert "download/solicitacao/nrRecibo" in xml

    def test_inner_download_por_nrrecibo_multiplos(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        nrs = ["1.2.001", "1.2.002"]
        xml = SOAPEnvelopeBuilder.inner_download_por_nrrecibo(EMPREGADOR, nrs)
        for nr in nrs:
            assert f"<nrRec>{nr}</nrRec>" in xml

    def test_empregador_cnpj_truncado_8_digitos(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        xml = SOAPEnvelopeBuilder.inner_consulta_ident_trabalhador(
            {"tpInsc": 1, "nrInsc": "05969071000110"},
            "12345678901", "2025-01-01", "2025-12-31"
        )
        assert "<nrInsc>05969071</nrInsc>" in xml


class TestSoapBuilderEnvelopes:
    def test_montar_consulta_ident_trabalhador(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        inner = '<eSocial xmlns="test"><data>test</data></eSocial>'
        soap = SOAPEnvelopeBuilder.montar_consulta_ident_trabalhador(inner)
        assert "soapenv:Envelope" in soap
        assert "ConsultarIdentificadoresEventosTrabalhador" in soap
        assert "consultaEventosTrabalhador" in soap
        assert "<data>test</data>" in soap

    def test_montar_consulta_ident_empregador(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        inner = '<eSocial xmlns="test"><data>test</data></eSocial>'
        soap = SOAPEnvelopeBuilder.montar_consulta_ident_empregador(inner)
        assert "ConsultarIdentificadoresEventosEmpregador" in soap
        assert "consultaEventosEmpregador" in soap

    def test_montar_download_por_id(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        inner = '<eSocial xmlns="test"><data>test</data></eSocial>'
        soap = SOAPEnvelopeBuilder.montar_download_por_id(inner)
        assert "SolicitarDownloadEventosPorId" in soap
        assert "v1:solicitacao" in soap

    def test_montar_download_por_nrrecibo(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        inner = '<eSocial xmlns="test"><data>test</data></eSocial>'
        soap = SOAPEnvelopeBuilder.montar_download_por_nrrecibo(inner)
        assert "SolicitarDownloadEventosPorNrRecibo" in soap
        assert "v1:solicitacao" in soap

    def test_envelope_remove_xml_declaration(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        inner = '<?xml version="1.0" encoding="UTF-8"?><eSocial xmlns="test"><data>test</data></eSocial>'
        soap = SOAPEnvelopeBuilder.montar_download_por_nrrecibo(inner)
        # Should only have one xml declaration (the SOAP one)
        assert soap.count("<?xml") == 1


class TestSoapBuilderHeaders:
    def test_headers_ident_trabalhador(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        h = SOAPEnvelopeBuilder.headers_ident_trabalhador()
        assert "SOAPAction" in h
        assert "ConsultarIdentificadoresEventosTrabalhador" in h["SOAPAction"]

    def test_headers_ident_empregador(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        h = SOAPEnvelopeBuilder.headers_ident_empregador()
        assert "ConsultarIdentificadoresEventosEmpregador" in h["SOAPAction"]

    def test_headers_download_por_id(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        h = SOAPEnvelopeBuilder.headers_download_por_id()
        assert "SolicitarDownloadEventosPorId" in h["SOAPAction"]

    def test_headers_download_por_nrrecibo(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        h = SOAPEnvelopeBuilder.headers_download_por_nrrecibo()
        assert "SolicitarDownloadEventosPorNrRecibo" in h["SOAPAction"]


# ══════════════════════════════════════════════════════════════════
# ESocialClient — Consultar Identificadores
# ══════════════════════════════════════════════════════════════════


class TestConsultarIdentificadoresTrabalhador:
    @patch("esocial.esocial_client.requests.post")
    def test_retorna_eventos(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_TRABALHADOR_SUCESSO)

        resultado = ESocialClient.consultar_identificadores_trabalhador(
            cpf="06184644173",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is True
        assert resultado["codigo_resposta"] == "201"
        assert len(resultado["eventos"]) == 2

    @patch("esocial.esocial_client.requests.post")
    def test_extrai_id_e_nrrecibo(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_TRABALHADOR_SUCESSO)

        resultado = ESocialClient.consultar_identificadores_trabalhador(
            cpf="06184644173",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        evt = resultado["eventos"][0]
        assert evt["id"] == "ID1059690710002025010112345600001"
        assert evt["nrRec"] == "1.2.0000000001.2025010112000000001"

    @patch("esocial.esocial_client.requests.post")
    def test_consulta_vazia(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_TRABALHADOR_VAZIO)

        resultado = ESocialClient.consultar_identificadores_trabalhador(
            cpf="99999999999",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is True
        assert len(resultado["eventos"]) == 0

    @patch("esocial.esocial_client.requests.post")
    def test_url_homologacao_por_padrao(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_TRABALHADOR_SUCESSO)

        ESocialClient.consultar_identificadores_trabalhador(
            cpf="06184644173",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        _, kwargs = mock_post.call_args
        assert "producaorestrita" in kwargs["url"]
        assert "ConsultarIdentificadoresEventos" in kwargs["url"]

    @patch("esocial.esocial_client.requests.post")
    def test_url_producao(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_TRABALHADOR_SUCESSO)

        ESocialClient.consultar_identificadores_trabalhador(
            cpf="06184644173",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
            producao=True,
        )

        _, kwargs = mock_post.call_args
        assert "webservices.download.esocial.gov.br" in kwargs["url"]

    @patch("esocial.esocial_client.requests.post")
    def test_erro_http(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.side_effect = Exception("Connection refused")

        resultado = ESocialClient.consultar_identificadores_trabalhador(
            cpf="06184644173",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is False
        assert "erro" in resultado

    @patch("esocial.esocial_client.requests.post")
    def test_xml_resposta_incluido(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_TRABALHADOR_SUCESSO)

        resultado = ESocialClient.consultar_identificadores_trabalhador(
            cpf="06184644173",
            dt_ini="2025-01-01",
            dt_fim="2025-12-31",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert "xml_resposta" in resultado
        assert "soapenv:Envelope" in resultado["xml_resposta"]


class TestConsultarIdentificadoresEmpregador:
    @patch("esocial.esocial_client.requests.post")
    def test_retorna_eventos(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_EMPREGADOR_SUCESSO)

        resultado = ESocialClient.consultar_identificadores_empregador(
            tp_evt="S-1200",
            per_apur="2025-01",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is True
        assert len(resultado["eventos"]) == 1
        assert resultado["eventos"][0]["id"] == "ID1059690710002025010112345600010"

    @patch("esocial.esocial_client.requests.post")
    def test_soap_action_correta(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_IDENT_EMPREGADOR_SUCESSO)

        ESocialClient.consultar_identificadores_empregador(
            tp_evt="S-1200",
            per_apur="2025-01",
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        _, kwargs = mock_post.call_args
        assert "ConsultarIdentificadoresEventosEmpregador" in kwargs["headers"]["SOAPAction"]


# ══════════════════════════════════════════════════════════════════
# ESocialClient — Download por NrRecibo
# ══════════════════════════════════════════════════════════════════


class TestDownloadPorNrRecibo:
    @patch("esocial.esocial_client.requests.post")
    def test_download_sucesso(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_SUCESSO)

        resultado = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.0000000001.2025010112000000001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is True
        assert resultado["codigo_resposta"] == "201"

    @patch("esocial.esocial_client.requests.post")
    def test_download_retorna_arquivo(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_SUCESSO)

        resultado = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.0000000001.2025010112000000001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert len(resultado["arquivos"]) == 1
        arq = resultado["arquivos"][0]
        assert arq["nr_recibo"] == "1.2.0000000001.2025010112000000001"
        assert arq["cd_resposta"] == "201"

    @patch("esocial.esocial_client.requests.post")
    def test_download_contem_evento_xml(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_SUCESSO)

        resultado = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.0000000001.2025010112000000001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        arq = resultado["arquivos"][0]
        assert arq["evento_xml"] is not None
        assert "evtRemun" in arq["evento_xml"]
        assert "06184644173" in arq["evento_xml"]

    @patch("esocial.esocial_client.requests.post")
    def test_download_url_homologacao(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_SUCESSO)

        ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        _, kwargs = mock_post.call_args
        assert "producaorestrita" in kwargs["url"]
        assert "WsSolicitarDownloadEventos" in kwargs["url"]

    @patch("esocial.esocial_client.requests.post")
    def test_download_url_producao(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_SUCESSO)

        ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
            producao=True,
        )

        _, kwargs = mock_post.call_args
        assert "webservices.download.esocial.gov.br" in kwargs["url"]

    @patch("esocial.esocial_client.requests.post")
    def test_download_erro(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_ERRO)

        resultado = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.INVALIDO"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is False
        assert resultado["codigo_resposta"] == "301"
        assert len(resultado["arquivos"]) == 0

    @patch("esocial.esocial_client.requests.post")
    def test_download_erro_conexao(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.side_effect = Exception("SSL handshake failed")

        resultado = ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is False
        assert "erro" in resultado

    @patch("esocial.esocial_client.requests.post")
    def test_download_soap_action_correta(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_SUCESSO)

        ESocialClient.solicitar_download_por_nrrecibo(
            nr_recibos=["1.2.001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        _, kwargs = mock_post.call_args
        assert "SolicitarDownloadEventosPorNrRecibo" in kwargs["headers"]["SOAPAction"]


# ══════════════════════════════════════════════════════════════════
# ESocialClient — Download por Id
# ══════════════════════════════════════════════════════════════════


class TestDownloadPorId:
    @patch("esocial.esocial_client.requests.post")
    def test_download_sucesso(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_POR_ID_SUCESSO)

        resultado = ESocialClient.solicitar_download_por_id(
            ids=["ID1059690710002025010112345600002"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        assert resultado["sucesso"] is True
        assert len(resultado["arquivos"]) == 1

    @patch("esocial.esocial_client.requests.post")
    def test_download_por_id_contem_evento(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_POR_ID_SUCESSO)

        resultado = ESocialClient.solicitar_download_por_id(
            ids=["ID1059690710002025010112345600002"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        arq = resultado["arquivos"][0]
        assert "evtPgtos" in arq["evento_xml"]
        assert arq["nr_recibo"] == "1.2.0000000001.2025010112000000002"

    @patch("esocial.esocial_client.requests.post")
    def test_download_por_id_soap_action(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_POR_ID_SUCESSO)

        ESocialClient.solicitar_download_por_id(
            ids=["ID001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
        )

        _, kwargs = mock_post.call_args
        assert "SolicitarDownloadEventosPorId" in kwargs["headers"]["SOAPAction"]

    @patch("esocial.esocial_client.requests.post")
    def test_download_por_id_url_producao(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_DOWNLOAD_POR_ID_SUCESSO)

        ESocialClient.solicitar_download_por_id(
            ids=["ID001"],
            pfx_data=pfx_data,
            password=PFX_PASS,
            empregador=EMPREGADOR,
            producao=True,
        )

        _, kwargs = mock_post.call_args
        assert "webservices.download.esocial.gov.br" in kwargs["url"]


# ══════════════════════════════════════════════════════════════════
# Parsing Tests
# ══════════════════════════════════════════════════════════════════


class TestParsingIdentificadores:
    def test_parsear_resposta_sucesso(self):
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient._parsear_resposta_identificadores(RESP_IDENT_TRABALHADOR_SUCESSO)
        assert resultado["sucesso"] is True
        assert resultado["codigo_resposta"] == "201"
        assert len(resultado["eventos"]) == 2

    def test_parsear_resposta_vazia(self):
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient._parsear_resposta_identificadores(RESP_IDENT_TRABALHADOR_VAZIO)
        assert resultado["sucesso"] is True
        assert len(resultado["eventos"]) == 0

    def test_parsear_xml_invalido(self):
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient._parsear_resposta_identificadores("not xml")
        assert resultado["sucesso"] is False
        assert "erro" in resultado


class TestParsingDownload:
    def test_parsear_download_sucesso(self):
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient._parsear_resposta_download(RESP_DOWNLOAD_SUCESSO)
        assert resultado["sucesso"] is True
        assert len(resultado["arquivos"]) == 1

    def test_parsear_download_erro(self):
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient._parsear_resposta_download(RESP_DOWNLOAD_ERRO)
        assert resultado["sucesso"] is False
        assert resultado["codigo_resposta"] == "301"
        assert len(resultado["arquivos"]) == 0

    def test_parsear_download_xml_invalido(self):
        from esocial.esocial_client import ESocialClient
        resultado = ESocialClient._parsear_resposta_download("not xml")
        assert resultado["sucesso"] is False
        assert "erro" in resultado
