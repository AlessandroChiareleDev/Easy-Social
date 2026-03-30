"""
FASE 3 — Testes de Assinatura Digital XMLDSig
TDD RED: todos devem falhar inicialmente (ModuleNotFoundError)
"""

import pytest
from lxml import etree

from esocial.xml_generator import S1010XMLGenerator
from esocial.certificate_manager import CertificateManager

# ── fixtures ────────────────────────────────────────────────────────
import os

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

DS_NS = "http://www.w3.org/2000/09/xmldsig#"


@pytest.fixture(scope="module")
def xml_bytes():
    return S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA)


@pytest.fixture(scope="module")
def pfx_data():
    with open(PFX_PATH, "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def signed_bytes(xml_bytes, pfx_data):
    from esocial.xml_signer import S1010XMLSigner
    return S1010XMLSigner.assinar(xml_bytes, pfx_data, PFX_PASS)


@pytest.fixture(scope="module")
def signed_root(signed_bytes):
    return etree.fromstring(signed_bytes)


# ── TEST-SIGN-01: <Signature> é último filho de <eSocial> ────────
class TestSignaturePosition:
    def test_signature_is_last_child(self, signed_root):
        children = list(signed_root)
        last = children[-1]
        assert last.tag == f"{{{DS_NS}}}Signature"

    def test_signature_exists(self, signed_root):
        sig = signed_root.find(f".//{{{DS_NS}}}Signature")
        assert sig is not None

    def test_exactly_one_signature(self, signed_root):
        sigs = signed_root.findall(f".//{{{DS_NS}}}Signature")
        assert len(sigs) == 1


# ── TEST-SIGN-02: Algoritmo RSA-SHA256 ───────────────────────────
class TestSignatureAlgorithm:
    def test_signature_method_rsa_sha256(self, signed_root):
        method = signed_root.find(
            f".//{{{DS_NS}}}SignedInfo/{{{DS_NS}}}SignatureMethod"
        )
        assert method is not None
        assert "rsa-sha256" in method.get("Algorithm").lower()

    def test_signature_value_present(self, signed_root):
        sig_val = signed_root.find(f".//{{{DS_NS}}}SignatureValue")
        assert sig_val is not None
        assert len(sig_val.text.strip()) > 0


# ── TEST-SIGN-03: Digest SHA-256 ────────────────────────────────
class TestDigestAlgorithm:
    def test_digest_method_sha256(self, signed_root):
        digest = signed_root.find(
            f".//{{{DS_NS}}}Reference/{{{DS_NS}}}DigestMethod"
        )
        assert digest is not None
        assert "sha256" in digest.get("Algorithm").lower()

    def test_digest_value_present(self, signed_root):
        dv = signed_root.find(f".//{{{DS_NS}}}Reference/{{{DS_NS}}}DigestValue")
        assert dv is not None
        assert len(dv.text.strip()) > 0


# ── TEST-SIGN-04: URI="" (vazia) — SERPRO Error 142 ─────────────
class TestReferenceURI:
    def test_uri_is_empty(self, signed_root):
        ref = signed_root.find(f".//{{{DS_NS}}}Reference")
        assert ref is not None
        assert ref.get("URI") == ""


# ── TEST-SIGN-05: Atributo Id maiúsculo no evento ───────────────
class TestIdAttribute:
    def test_id_is_uppercase(self, signed_root):
        esocial_ns = "http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00"
        evt = signed_root.find(f"{{{esocial_ns}}}evtTabRubrica")
        assert evt is not None
        assert "Id" in evt.attrib
        assert "id" not in evt.attrib or evt.attrib.get("id") == evt.attrib.get("Id")

    def test_id_starts_with_ID(self, signed_root):
        esocial_ns = "http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00"
        evt = signed_root.find(f"{{{esocial_ns}}}evtTabRubrica")
        assert evt.get("Id").startswith("ID")


# ── TEST-SIGN-06: XML assinado continua parseável ────────────────
class TestSignedXMLIntegrity:
    def test_output_is_bytes(self, signed_bytes):
        assert isinstance(signed_bytes, bytes)

    def test_parseable_xml(self, signed_bytes):
        root = etree.fromstring(signed_bytes)
        assert root.tag.endswith("eSocial")

    def test_original_content_preserved(self, signed_root):
        esocial_ns = "http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00"
        tp_amb = signed_root.find(f".//{{{esocial_ns}}}tpAmb")
        assert tp_amb is not None
        assert tp_amb.text == "2"

    def test_x509_certificate_embedded(self, signed_root):
        cert = signed_root.find(f".//{{{DS_NS}}}X509Certificate")
        assert cert is not None
        assert len(cert.text.strip()) > 0

    def test_c14n_transform_present(self, signed_root):
        transforms = signed_root.findall(f".//{{{DS_NS}}}Transform")
        algorithms = [t.get("Algorithm") for t in transforms]
        assert any("c14n" in a.lower() for a in algorithms if a)


# ── TEST-SIGN-07: Erros ─────────────────────────────────────────
class TestSigningErrors:
    def test_wrong_password_raises(self, xml_bytes, pfx_data):
        from esocial.xml_signer import S1010XMLSigner
        with pytest.raises(ValueError, match="[Ss]enha"):
            S1010XMLSigner.assinar(xml_bytes, pfx_data, "wrongpassword")

    def test_invalid_xml_raises(self, pfx_data):
        from esocial.xml_signer import S1010XMLSigner
        with pytest.raises(ValueError):
            S1010XMLSigner.assinar(b"not xml at all", pfx_data, PFX_PASS)

    def test_invalid_pfx_raises(self, xml_bytes):
        from esocial.xml_signer import S1010XMLSigner
        with pytest.raises(ValueError):
            S1010XMLSigner.assinar(xml_bytes, b"not a pfx", PFX_PASS)
