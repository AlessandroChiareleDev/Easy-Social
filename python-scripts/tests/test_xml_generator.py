"""
FASE 2 — Testes TDD para Geração de XML S-1010 (alteração)
Estes testes DEFINEM o comportamento esperado do S1010XMLGenerator.
TDD: escrever testes → rodar (RED) → implementar → rodar (GREEN)
"""
import re
import pytest
from lxml import etree

from esocial.xml_generator import S1010XMLGenerator

NS = "http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00"

# Dados de rubrica usados em todos os testes
RUBRICA_SAMPLE = {
    "codRubr": "1",
    "ideTabRubr": "1",
    "iniValid": "2026-03",
    "dscRubr": "HORAS NORMAIS",
    "natRubr": 1000,
    "tpRubr": 1,
    "codIncCP": 11,
    "codIncIRRF": 11,
    "codIncFGTS": 11,
    "codIncPisPasep": 0,
}

EMPREGADOR = {
    "tpInsc": 1,
    "nrInsc": "12345678",  # CNPJ raiz 8 dígitos
}


class TestXmlAlteracaoNamespace:
    """TEST-XML-01: Gerar XML alteração 1 rubrica → namespace v_S_01_03_00"""

    def test_root_is_esocial(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        assert root.tag == f"{{{NS}}}eSocial"

    def test_namespace_is_v_s_01_03_00(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        assert b"v_S_01_03_00" in xml_str

    def test_has_evtTabRubrica(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        evt = root.find(f"{{{NS}}}evtTabRubrica")
        assert evt is not None

    def test_has_alteracao_node(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        alt = root.find(f".//{{{NS}}}alteracao")
        assert alt is not None

    def test_tpAmb_is_2(self):
        """Homologação obrigatória — tpAmb deve ser 2"""
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        tp_amb = root.find(f".//{{{NS}}}tpAmb")
        assert tp_amb is not None
        assert tp_amb.text == "2"

    def test_xml_is_parseable_bytes(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        assert isinstance(xml_str, bytes)
        root = etree.fromstring(xml_str)
        assert root is not None


class TestXmlCamposObrigatorios:
    """TEST-XML-02: TODOS os campos obrigatórios em dadosRubrica"""

    def _get_dados_rubrica(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        return root.find(f".//{{{NS}}}dadosRubrica")

    def test_dscRubr_present(self):
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}dscRubr")
        assert el is not None
        assert el.text == "HORAS NORMAIS"

    def test_natRubr_present(self):
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}natRubr")
        assert el is not None
        assert el.text == "1000"

    def test_tpRubr_present(self):
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}tpRubr")
        assert el is not None
        assert el.text == "1"

    def test_codIncCP_present(self):
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}codIncCP")
        assert el is not None
        assert el.text == "11"

    def test_codIncIRRF_present(self):
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}codIncIRRF")
        assert el is not None
        assert el.text == "11"

    def test_codIncFGTS_present(self):
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}codIncFGTS")
        assert el is not None
        assert el.text == "11"

    def test_codIncPisPasep_present(self):
        """codIncPisPasep é obrigatório no S-1.3"""
        dr = self._get_dados_rubrica()
        el = dr.find(f"{{{NS}}}codIncPisPasep")
        assert el is not None
        assert el.text == "00"

    def test_ideRubrica_codRubr(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        ide = root.find(f".//{{{NS}}}ideRubrica")
        el = ide.find(f"{{{NS}}}codRubr")
        assert el is not None
        assert el.text == "1"

    def test_ideRubrica_ideTabRubr(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        ide = root.find(f".//{{{NS}}}ideRubrica")
        el = ide.find(f"{{{NS}}}ideTabRubr")
        assert el is not None
        assert el.text == "1"

    def test_ideRubrica_iniValid(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        ide = root.find(f".//{{{NS}}}ideRubrica")
        el = ide.find(f"{{{NS}}}iniValid")
        assert el is not None
        assert el.text == "2026-03"


class TestXmlIdFormato:
    """TEST-XML-03: Id segue formato ID{tpInsc}{nrInsc14}{ts}{seq5}"""

    def test_id_starts_with_ID(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        evt = root.find(f"{{{NS}}}evtTabRubrica")
        evt_id = evt.get("Id")
        assert evt_id.startswith("ID")

    def test_id_max_36_chars(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        evt = root.find(f"{{{NS}}}evtTabRubrica")
        evt_id = evt.get("Id")
        assert len(evt_id) <= 36

    def test_id_matches_regex(self):
        """ID{tpInsc(1)}{nrInsc(14)}{AAAA(4)}{MM(2)}{DD(2)}{HH(2)}{mm(2)}{ss(2)}{seq(5)}"""
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        evt = root.find(f"{{{NS}}}evtTabRubrica")
        evt_id = evt.get("Id")
        pattern = r"^ID[12]\d{14}\d{4}\d{2}\d{2}\d{2}\d{2}\d{2}\d{5}$"
        assert re.match(pattern, evt_id), f"Id '{evt_id}' não segue o formato esperado"

    def test_id_attribute_is_uppercase_Id(self):
        """eSocial exige 'Id' (I maiúsculo, d minúsculo)"""
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        evt = root.find(f"{{{NS}}}evtTabRubrica")
        assert "Id" in evt.attrib
        assert "id" not in evt.attrib or evt.attrib.get("id") is None


class TestXmlNrInsc:
    """TEST-XML-04: nrInsc empregador = 8 dígitos (CNPJ raiz) — Regra 646"""

    def test_nrInsc_is_8_digits(self):
        xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        nr_insc = root.find(f".//{{{NS}}}nrInsc")
        assert nr_insc is not None
        assert nr_insc.text == "12345678"
        assert len(nr_insc.text) == 8

    def test_nrInsc_14_digit_is_truncated(self):
        """Se passar CNPJ completo 14 dígitos, deve truncar para 8"""
        emp = {"tpInsc": 1, "nrInsc": "12345678000190"}
        xml_str = S1010XMLGenerator.gerar_alteracao(emp, RUBRICA_SAMPLE)
        root = etree.fromstring(xml_str)
        nr_insc = root.find(f".//{{{NS}}}nrInsc")
        assert nr_insc.text == "12345678"


class TestXmlValidacaoCodIncCP:
    """TEST-XML-05: codIncCP ∈ valores válidos Tabela 04"""

    VALID_VALUES = [0, 1, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26,
                    31, 32, 34, 35, 51, 61, 91, 92, 93, 94, 95, 96, 97, 98]

    def test_valid_codIncCP_accepted(self):
        for val in self.VALID_VALUES:
            rubrica = {**RUBRICA_SAMPLE, "codIncCP": val}
            xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)
            assert xml_str is not None

    def test_invalid_codIncCP_raises(self):
        rubrica = {**RUBRICA_SAMPLE, "codIncCP": 99}
        with pytest.raises(ValueError, match="codIncCP"):
            S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)


class TestXmlValidacaoCodIncIRRF:
    """TEST-XML-06: codIncIRRF ∈ valores válidos Tabela 21"""

    def test_valid_codIncIRRF_accepted(self):
        for val in [0, 1, 9, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35,
                    41, 42, 43, 44, 46, 47, 51, 52, 53, 54, 55,
                    61, 62, 63, 64, 68, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
                    81, 82, 83, 91, 92, 93, 94, 95, 702, 703, 704]:
            rubrica = {**RUBRICA_SAMPLE, "codIncIRRF": val}
            xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)
            assert xml_str is not None

    def test_invalid_codIncIRRF_raises(self):
        rubrica = {**RUBRICA_SAMPLE, "codIncIRRF": 999}
        with pytest.raises(ValueError, match="codIncIRRF"):
            S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)


class TestXmlValidacaoCodIncFGTS:
    """TEST-XML-07: codIncFGTS ∈ valores válidos Tabela 22"""

    VALID_VALUES = [0, 11, 12, 21, 91, 92, 93]

    def test_valid_codIncFGTS_accepted(self):
        for val in self.VALID_VALUES:
            rubrica = {**RUBRICA_SAMPLE, "codIncFGTS": val}
            xml_str = S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)
            assert xml_str is not None

    def test_invalid_codIncFGTS_raises(self):
        rubrica = {**RUBRICA_SAMPLE, "codIncFGTS": 50}
        with pytest.raises(ValueError, match="codIncFGTS"):
            S1010XMLGenerator.gerar_alteracao(EMPREGADOR, rubrica)


class TestXmlLote:
    """TEST-XML-08: Gerar N XMLs (max 50)"""

    def test_generate_multiple_xmls(self):
        rubricas = [
            {**RUBRICA_SAMPLE, "codRubr": str(i)} for i in range(1, 4)
        ]
        xmls = S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
        assert len(xmls) == 3
        for xml_str in xmls:
            root = etree.fromstring(xml_str)
            assert root.tag == f"{{{NS}}}eSocial"

    def test_each_xml_has_unique_id(self):
        rubricas = [
            {**RUBRICA_SAMPLE, "codRubr": str(i)} for i in range(1, 6)
        ]
        xmls = S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
        ids = []
        for xml_str in xmls:
            root = etree.fromstring(xml_str)
            evt = root.find(f"{{{NS}}}evtTabRubrica")
            ids.append(evt.get("Id"))
        assert len(set(ids)) == 5, "IDs devem ser únicos"

    def test_max_50_raises_if_exceeded(self):
        rubricas = [
            {**RUBRICA_SAMPLE, "codRubr": str(i)} for i in range(1, 52)
        ]
        with pytest.raises(ValueError, match="50"):
            S1010XMLGenerator.gerar_lote_alteracao(EMPREGADOR, rubricas)
