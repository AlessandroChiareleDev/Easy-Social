"""
FASE 7 — Testes End-to-End
Pipeline completo: cert → gerar XML → assinar → envelope SOAP → enviar → consultar
Usa mocking de requests.post mas executa TODO o pipeline real.
"""

import pytest
import re
from unittest.mock import patch, MagicMock
import os

from esocial.certificate_manager import CertificateManager
from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner
from esocial.soap_builder import SOAPEnvelopeBuilder
from esocial.esocial_client import ESocialClient

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PFX_PATH = os.path.join(FIXTURES, "cert_valid.pfx")
PFX_PASS = "test1234"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "12345678000190"}

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
            <dhRecepcao>2026-03-27T14:00:00.000</dhRecepcao>
            <versaoAplicativoRecepcao>8.0.0.0</versaoAplicativoRecepcao>
            <protocoloEnvio>1.2.202603.9999999999</protocoloEnvio>
          </dadosRecepcaoLote>
        </retornoEnvioLoteEventos>
      </eSocial>
    </EnviarLoteEventosResult>
  </soapenv:Body>
</soapenv:Envelope>"""


def _resp_consulta_sucesso(nr_recibo, evt_id):
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
                <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00">
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


def _resp_consulta_multi(eventos_info):
    """Gera resposta de consulta com múltiplos eventos."""
    blocos = []
    for evt_id, nr_recibo in eventos_info:
        blocos.append(f"""
            <evento Id="{evt_id}">
              <retornoEvento>
                <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00">
                  <retornoEvento>
                    <processamento>
                      <cdResposta>201</cdResposta>
                      <descResposta>Sucesso.</descResposta>
                      <nrRecibo>{nr_recibo}</nrRecibo>
                    </processamento>
                  </retornoEvento>
                </eSocial>
              </retornoEvento>
            </evento>""")
    eventos_xml = "\n".join(blocos)
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
          <retornoEventos>{eventos_xml}
          </retornoEventos>
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


# ── TEST-E2E-01: Pipeline completo — cert → gerar → assinar → enviar → consultar
class TestE2EPipelineCompleto:
    @patch("esocial.esocial_client.requests.post")
    def test_pipeline_cert_to_consulta(self, mock_post, pfx_data):
        """Upload cert → validar → gerar XML → assinar → SOAP → enviar → consultar"""
        # 1. Validar certificado
        info = CertificateManager.validate_pfx(pfx_data, PFX_PASS)
        assert info["valido"] is True
        cnpj = info["cnpj"]

        # 2. Gerar XML S-1010 (alteração)
        rubrica = {
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
        xml_bytes = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)
        assert b"evtTabRubrica" in xml_bytes

        # 3. Assinar
        assinado = S1010XMLSigner.assinar(xml_bytes, pfx_data, PFX_PASS)
        assert b"Signature" in assinado

        # 4. Montar envelope SOAP
        envelope = SOAPEnvelopeBuilder.montar_envio(
            eventos_assinados=[assinado],
            empregador=EMPREGADOR,
            transmissor=EMPREGADOR,
            grupo="1",
        )
        assert "soapenv:Envelope" in envelope

        # Extrair Id do evento para mock de consulta
        evt_id = re.search(r'<evento\s+Id="([^"]+)"', envelope).group(1)

        # 5. Enviar (mock)
        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado_envio = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado_envio["sucesso"] is True
        protocolo = resultado_envio["protocolo"]
        assert protocolo == "1.2.202603.9999999999"

        # 6. Consultar (mock)
        nr_recibo = "1.2.0000000000.2026032714000000001"
        mock_post.return_value = _mock_response(
            _resp_consulta_sucesso(nr_recibo, evt_id)
        )
        resultado_consulta = ESocialClient.consultar_lote(
            protocolo, pfx_data, PFX_PASS
        )

        assert resultado_consulta["sucesso"] is True
        assert len(resultado_consulta["eventos"]) == 1
        assert resultado_consulta["eventos"][0]["nr_recibo"] == nr_recibo

    @patch("esocial.esocial_client.requests.post")
    def test_pipeline_resultado_tem_todos_campos_para_db(self, mock_post, pfx_data):
        """Verifica que o resultado final tem todos os campos para salvar no DB."""
        rubrica = {
            "codRubr": "2000",
            "ideTabRubr": "1",
            "iniValid": "2024-01",
            "dscRubr": "Horas Extras 50%",
            "natRubr": 1002,
            "tpRubr": 1,
            "codIncCP": 11,
            "codIncIRRF": 11,
            "codIncFGTS": 11,
            "codIncPisPasep": 0,
        }
        xml = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, "1"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        envio = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        # Campos para INSERT no banco
        assert envio["protocolo"] is not None
        assert envio["dh_recepcao"] is not None
        assert envio["codigo_resposta"] is not None
        assert envio["descricao"] is not None


# ── TEST-E2E-02: Rubrica real (dados tipo tabela_cruzamento) → aceita
class TestE2ERubricaReal:
    @patch("esocial.esocial_client.requests.post")
    def test_rubrica_real_salario_base(self, mock_post, pfx_data):
        """Simula rubrica real como viria do tabela_cruzamento."""
        rubrica_real = {
            "codRubr": "1",
            "ideTabRubr": "1",
            "iniValid": "2024-01",
            "dscRubr": "Salário, vencimento, soldo ou subsídio",
            "natRubr": 1000,
            "tpRubr": 1,
            "codIncCP": 11,
            "codIncIRRF": 11,
            "codIncFGTS": 11,
            "codIncPisPasep": 11,
        }

        xml = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica_real)
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, "1"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True

    @patch("esocial.esocial_client.requests.post")
    def test_rubrica_real_horas_extras(self, mock_post, pfx_data):
        """Rubrica de horas extras com incidências típicas."""
        rubrica_real = {
            "codRubr": "5",
            "ideTabRubr": "1",
            "iniValid": "2024-01",
            "dscRubr": "Horas extras",
            "natRubr": 1002,
            "tpRubr": 1,
            "codIncCP": 11,
            "codIncIRRF": 11,
            "codIncFGTS": 11,
            "codIncPisPasep": 11,
        }

        xml = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica_real)
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, "1"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True

    @patch("esocial.esocial_client.requests.post")
    def test_rubrica_real_desconto_vt(self, mock_post, pfx_data):
        """Rubrica de desconto (vale transporte) — tpRubr=2, sem incidência FGTS."""
        rubrica_real = {
            "codRubr": "100",
            "ideTabRubr": "1",
            "iniValid": "2024-01",
            "dscRubr": "Desconto de vale transporte",
            "natRubr": 9220,
            "tpRubr": 2,
            "codIncCP": 0,
            "codIncIRRF": 0,
            "codIncFGTS": 0,
            "codIncPisPasep": 0,
        }

        xml = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica_real)
        assinado = S1010XMLSigner.assinar(xml, pfx_data, PFX_PASS)
        envelope = SOAPEnvelopeBuilder.montar_envio(
            [assinado], EMPREGADOR, EMPREGADOR, "1"
        )

        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        resultado = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)

        assert resultado["sucesso"] is True


# ── TEST-E2E-03: Lote com 5 rubricas → todas processadas ────────
class TestE2ELoteBatch:
    @patch("esocial.esocial_client.requests.post")
    def test_lote_5_rubricas_pipeline_completo(self, mock_post, pfx_data):
        """5 rubricas distintas → gerar → assinar cada → SOAP → enviar → consultar 5."""
        rubricas = [
            {"codRubr": "1", "ideTabRubr": "1", "iniValid": "2024-01",
             "dscRubr": "Salário Base", "natRubr": 1000, "tpRubr": 1,
             "codIncCP": 11, "codIncIRRF": 11, "codIncFGTS": 11, "codIncPisPasep": 11},
            {"codRubr": "5", "ideTabRubr": "1", "iniValid": "2024-01",
             "dscRubr": "Horas Extras 50%", "natRubr": 1002, "tpRubr": 1,
             "codIncCP": 11, "codIncIRRF": 11, "codIncFGTS": 11, "codIncPisPasep": 11},
            {"codRubr": "10", "ideTabRubr": "1", "iniValid": "2024-01",
             "dscRubr": "Adicional Noturno", "natRubr": 1003, "tpRubr": 1,
             "codIncCP": 11, "codIncIRRF": 11, "codIncFGTS": 11, "codIncPisPasep": 11},
            {"codRubr": "50", "ideTabRubr": "1", "iniValid": "2024-01",
             "dscRubr": "Férias", "natRubr": 1020, "tpRubr": 1,
             "codIncCP": 11, "codIncIRRF": 11, "codIncFGTS": 11, "codIncPisPasep": 11},
            {"codRubr": "100", "ideTabRubr": "1", "iniValid": "2024-01",
             "dscRubr": "Desc. VT", "natRubr": 9220, "tpRubr": 2,
             "codIncCP": 0, "codIncIRRF": 0, "codIncFGTS": 0, "codIncPisPasep": 0},
        ]

        # Gerar lote de XMLs
        xmls = S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
        assert len(xmls) == 5

        # Assinar cada um
        assinados = [S1010XMLSigner.assinar(x, pfx_data, PFX_PASS) for x in xmls]
        assert all(b"Signature" in a for a in assinados)

        # Montar envelope SOAP
        envelope = SOAPEnvelopeBuilder.montar_envio(
            assinados, EMPREGADOR, EMPREGADOR, "1"
        )
        assert envelope.count("<evento ") == 5

        # Extrair Ids dos eventos
        evt_ids = re.findall(r'<evento\s+Id="([^"]+)"', envelope)
        assert len(evt_ids) == 5

        # Enviar (mock)
        mock_post.return_value = _mock_response(RESP_ENVIO_201)
        envio = ESocialClient.enviar_lote(envelope, pfx_data, PFX_PASS)
        assert envio["sucesso"] is True
        protocolo = envio["protocolo"]

        # Consultar (mock) — 5 eventos processados
        eventos_info = [
            (evt_id, f"1.2.0000000000.202603271400000000{i+1}")
            for i, evt_id in enumerate(evt_ids)
        ]
        mock_post.return_value = _mock_response(_resp_consulta_multi(eventos_info))
        consulta = ESocialClient.consultar_lote(protocolo, pfx_data, PFX_PASS)

        assert consulta["sucesso"] is True
        assert len(consulta["eventos"]) == 5
        assert all(e["codigo_resposta"] == "201" for e in consulta["eventos"])
        assert all(e["nr_recibo"] is not None for e in consulta["eventos"])

    @patch("esocial.esocial_client.requests.post")
    def test_lote_ids_unicos_no_pipeline(self, mock_post, pfx_data):
        """Verifica que IDs são únicos em todo o pipeline."""
        rubricas = [
            {"codRubr": str(i), "ideTabRubr": "1", "iniValid": "2024-01",
             "dscRubr": f"Rubrica {i}", "natRubr": 1000, "tpRubr": 1,
             "codIncCP": 11, "codIncIRRF": 11, "codIncFGTS": 11, "codIncPisPasep": 0}
            for i in range(1, 6)
        ]

        xmls = S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
        assinados = [S1010XMLSigner.assinar(x, pfx_data, PFX_PASS) for x in xmls]
        envelope = SOAPEnvelopeBuilder.montar_envio(
            assinados, EMPREGADOR, EMPREGADOR, "1"
        )

        # Todos os IDs no envelope devem ser únicos
        all_ids = re.findall(r'Id="([^"]+)"', envelope)
        # Cada evento tem Id no <evento> e Id no <evtTabRubrica> — devem ser iguais em pares
        evento_ids = re.findall(r'<evento\s+Id="([^"]+)"', envelope)
        assert len(set(evento_ids)) == 5  # todos únicos entre si
