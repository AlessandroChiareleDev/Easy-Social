"""
FASE 4 — Testes de Envelope SOAP 1.1 para envio ao eSocial
TDD RED → GREEN
"""

import pytest
import re
from lxml import etree

from esocial.xml_generator import S1010XMLGenerator
from esocial.xml_signer import S1010XMLSigner

import os

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PFX_PATH = os.path.join(FIXTURES, "cert_valid.pfx")
PFX_PASS = "test1234"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "12345678000190"}
RUBRICA_BASE = {
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

SOAPENV = "http://schemas.xmlsoap.org/soap/envelope/"
V1_NS = "http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0"
LOTE_NS = "http://www.esocial.gov.br/schema/lote/eventos/envio/v1_1_1"
ESOCIAL_NS = "http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00"


@pytest.fixture(scope="module")
def pfx_data():
    with open(PFX_PATH, "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def signed_xml(pfx_data):
    xml_bytes = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_BASE)
    return S1010XMLSigner.assinar(xml_bytes, pfx_data, PFX_PASS)


@pytest.fixture(scope="module")
def soap_envelope_str(signed_xml):
    from esocial.soap_builder import SOAPEnvelopeBuilder
    return SOAPEnvelopeBuilder.montar_envio(
        eventos_assinados=[signed_xml],
        empregador=EMPREGADOR,
        transmissor=EMPREGADOR,
        grupo="1",
    )


@pytest.fixture(scope="module")
def soap_root(soap_envelope_str):
    return etree.fromstring(soap_envelope_str.encode("utf-8"))


# ── TEST-SOAP-01: Envelope SOAP 1.1 válido ──────────────────────
class TestSOAPStructure:
    def test_root_is_envelope(self, soap_root):
        assert soap_root.tag == f"{{{SOAPENV}}}Envelope"

    def test_has_header(self, soap_root):
        header = soap_root.find(f"{{{SOAPENV}}}Header")
        assert header is not None

    def test_has_body(self, soap_root):
        body = soap_root.find(f"{{{SOAPENV}}}Body")
        assert body is not None

    def test_body_has_enviar_lote(self, soap_root):
        enviar = soap_root.find(f".//{{{V1_NS}}}EnviarLoteEventos")
        assert enviar is not None

    def test_lote_eventos_element(self, soap_root):
        lote = soap_root.find(f".//{{{V1_NS}}}loteEventos")
        assert lote is not None


# ── TEST-SOAP-02: grupo="1" para S-1010 ─────────────────────────
class TestGrupo:
    def test_grupo_is_one(self, soap_envelope_str):
        assert 'grupo="1"' in soap_envelope_str


# ── TEST-SOAP-03: Id <evento> == Id interno (Regra 555) ─────────
class TestIdMatching:
    def test_evento_id_matches_internal_id(self, soap_envelope_str):
        # Extract Id from <evento Id="...">
        evento_ids = re.findall(r'<evento\s+Id="([^"]+)"', soap_envelope_str)
        assert len(evento_ids) == 1

        # Extract Id from <evtTabRubrica Id="...">
        interno_ids = re.findall(r'<[^>]*evtTabRubrica[^>]*\s+Id="([^"]+)"', soap_envelope_str)
        assert len(interno_ids) == 1

        assert evento_ids[0] == interno_ids[0]


# ── TEST-SOAP-04: Sem <?xml?> duplicado ──────────────────────────
class TestXmlDeclaration:
    def test_single_xml_declaration(self, soap_envelope_str):
        count = soap_envelope_str.count("<?xml")
        assert count == 1, f"Esperado 1 declaração <?xml?>, encontrado {count}"

    def test_declaration_at_start(self, soap_envelope_str):
        assert soap_envelope_str.strip().startswith("<?xml")


# ── TEST-SOAP-05: XML assinado intacto com <eSocial> wrapper (Regra 402) ──
class TestSignedXMLIntact:
    def test_esocial_wrapper_present(self, soap_envelope_str):
        # The signed XML's <eSocial> should be inside <evento>
        # There should be TWO eSocial elements: lote root + event root
        esocial_count = soap_envelope_str.count("<eSocial")
        assert esocial_count >= 2, f"Esperado >=2 <eSocial>, encontrado {esocial_count}"

    def test_signature_preserved(self, soap_envelope_str):
        assert "<ds:Signature" in soap_envelope_str or "<Signature" in soap_envelope_str


# ── TEST-SOAP-06: Lote com N eventos (max 50) ───────────────────
class TestMultipleEvents:
    def test_multiple_eventos(self, pfx_data):
        from esocial.soap_builder import SOAPEnvelopeBuilder

        rubricas = [
            {**RUBRICA_BASE, "codRubr": str(1000 + i)} for i in range(3)
        ]
        xmls = S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
        assinados = [S1010XMLSigner.assinar(x, pfx_data, PFX_PASS) for x in xmls]

        envelope = SOAPEnvelopeBuilder.montar_envio(
            eventos_assinados=assinados,
            empregador=EMPREGADOR,
            transmissor=EMPREGADOR,
            grupo="1",
        )

        evento_count = envelope.count("<evento ")
        assert evento_count == 3

    def test_each_evento_has_unique_id(self, pfx_data):
        from esocial.soap_builder import SOAPEnvelopeBuilder

        rubricas = [
            {**RUBRICA_BASE, "codRubr": str(2000 + i)} for i in range(3)
        ]
        xmls = S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
        assinados = [S1010XMLSigner.assinar(x, pfx_data, PFX_PASS) for x in xmls]

        envelope = SOAPEnvelopeBuilder.montar_envio(
            eventos_assinados=assinados,
            empregador=EMPREGADOR,
            transmissor=EMPREGADOR,
            grupo="1",
        )

        ids = re.findall(r'<evento\s+Id="([^"]+)"', envelope)
        assert len(ids) == 3
        assert len(set(ids)) == 3  # all unique


# ── TEST-SOAP-07: Helpers / constantes ───────────────────────────
class TestSOAPConstants:
    def test_soap_action_header(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        headers = SOAPEnvelopeBuilder.headers()
        assert "SOAPAction" in headers
        assert "EnviarLoteEventos" in headers["SOAPAction"]
        assert headers["Content-Type"] == "text/xml; charset=utf-8"

    def test_url_homologacao(self):
        from esocial.soap_builder import SOAPEnvelopeBuilder
        url = SOAPEnvelopeBuilder.url_envio()
        assert "producaorestrita" in url
        assert "WsEnviarLoteEventos" in url
