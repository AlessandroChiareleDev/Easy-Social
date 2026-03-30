"""
FASE 6 — Testes de Consulta de Resultado ao eSocial
Usa mocking de requests.post para simular respostas do SERPRO.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PFX_PATH = os.path.join(FIXTURES, "cert_valid.pfx")
PFX_PASS = "test1234"

# ── Respostas mockadas ───────────────────────────────────────────

RESP_CONSULTA_SUCESSO = """<?xml version="1.0" encoding="UTF-8"?>
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
            <evento Id="ID1123456780000002026032710370000001">
              <retornoEvento>
                <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00">
                  <retornoEvento>
                    <processamento>
                      <cdResposta>201</cdResposta>
                      <descResposta>Sucesso.</descResposta>
                      <nrRecibo>1.2.0000000000.2026032712000000001</nrRecibo>
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

RESP_CONSULTA_EVENTO_ERRO = """<?xml version="1.0" encoding="UTF-8"?>
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
            <evento Id="ID1123456780000002026032710370000001">
              <retornoEvento>
                <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00">
                  <retornoEvento>
                    <processamento>
                      <cdResposta>402</cdResposta>
                      <descResposta>Erro de validação.</descResposta>
                      <ocorrencias>
                        <ocorrencia>
                          <tipo>1</tipo>
                          <codigo>218</codigo>
                          <descricao>Rubrica não encontrada.</descricao>
                          <localizacao>/eSocial/evtTabRubrica/infoRubrica/alteracao/ideRubrica/codRubr</localizacao>
                        </ocorrencia>
                      </ocorrencias>
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


PROTOCOLO = "1.2.202603.1234567890"


# ── TEST-CONSULTA-01: Consultar com protocolo válido → resultado ──
class TestConsultaSucesso:
    @patch("esocial.esocial_client.requests.post")
    def test_consulta_retorna_sucesso(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_SUCESSO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True
        assert resultado["codigo_resposta"] == "201"

    @patch("esocial.esocial_client.requests.post")
    def test_consulta_url_correta(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_SUCESSO)

        ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        _, kwargs = mock_post.call_args
        assert "ConsultarLoteEventos" in kwargs["url"]


# ── TEST-CONSULTA-02: Parsear sucesso → extrair nrRecibo ────────
class TestConsultaRecibo:
    @patch("esocial.esocial_client.requests.post")
    def test_extrai_nr_recibo(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_SUCESSO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        assert len(resultado["eventos"]) == 1
        evt = resultado["eventos"][0]
        assert evt["nr_recibo"] == "1.2.0000000000.2026032712000000001"

    @patch("esocial.esocial_client.requests.post")
    def test_evento_tem_id(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_SUCESSO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        evt = resultado["eventos"][0]
        assert evt["id"].startswith("ID")

    @patch("esocial.esocial_client.requests.post")
    def test_evento_sucesso_codigo_201(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_SUCESSO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        evt = resultado["eventos"][0]
        assert evt["codigo_resposta"] == "201"


# ── TEST-CONSULTA-03: Parsear erro → código + descrição + ocorrências ──
class TestConsultaErroEvento:
    @patch("esocial.esocial_client.requests.post")
    def test_evento_rejeitado(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_EVENTO_ERRO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        # Lote processado OK, mas evento rejeitado
        assert resultado["codigo_resposta"] == "201"
        evt = resultado["eventos"][0]
        assert evt["codigo_resposta"] == "402"

    @patch("esocial.esocial_client.requests.post")
    def test_evento_erro_tem_ocorrencias(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_EVENTO_ERRO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        evt = resultado["eventos"][0]
        assert len(evt["ocorrencias"]) >= 1
        oc = evt["ocorrencias"][0]
        assert oc["codigo"] == "218"
        assert "Rubrica" in oc["descricao"]

    @patch("esocial.esocial_client.requests.post")
    def test_em_processamento(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_EM_PROCESSAMENTO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        assert resultado["codigo_resposta"] == "101"
        assert resultado["sucesso"] is False
        assert len(resultado["eventos"]) == 0


# ── TEST-CONSULTA-04: Resultado contém dados para atualizar DB ──
class TestConsultaDadosDB:
    @patch("esocial.esocial_client.requests.post")
    def test_resultado_tem_campos_para_update(self, mock_post, pfx_data):
        from esocial.esocial_client import ESocialClient
        mock_post.return_value = _mock_response(RESP_CONSULTA_SUCESSO)

        resultado = ESocialClient.consultar_lote(PROTOCOLO, pfx_data, PFX_PASS)

        assert "codigo_resposta" in resultado
        assert "descricao" in resultado
        assert "eventos" in resultado
        evt = resultado["eventos"][0]
        assert "nr_recibo" in evt
        assert "codigo_resposta" in evt
        assert "id" in evt
