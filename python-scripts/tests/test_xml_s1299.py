"""
Testes TDD para Geração de XML S-1299 (Fechamento de Eventos Periódicos)
Valida: namespace, campos obrigatórios, infoFech, validações, lote.
Conforme XSD evtFechaEvPer-v_S_01_03_00: NÃO possui ideRespInf nem evtAqProd.
"""

import re
import pytest
from lxml import etree

from esocial.xml_s1299 import S1299XMLGenerator

NS = "http://www.esocial.gov.br/schema/evt/evtFechaEvPer/v_S_01_03_00"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}  # CNPJ raiz APPA


# ── TEST-S1299-01: Namespace e estrutura raiz ────────────────────
class TestS1299Namespace:
    def test_root_is_esocial(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        assert root.tag == f"{{{NS}}}eSocial"

    def test_namespace_v_s_01_03_00(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        assert b"v_S_01_03_00" in xml

    def test_has_evtFechaEvPer(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        evt = root.find(f"{{{NS}}}evtFechaEvPer")
        assert evt is not None

    def test_namespace_diferente_do_s1298(self):
        """Cada evento tem namespace único — S-1299 ≠ S-1298"""
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        assert b"evtFechaEvPer" in xml
        assert b"evtReabreEvPer" not in xml

    def test_xml_is_bytes_utf8(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        assert isinstance(xml, bytes)
        assert b"UTF-8" in xml


# ── TEST-S1299-02: Campos de ideEvento ───────────────────────────
class TestS1299IdeEvento:
    def _get_ide_evento(self, **kwargs):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01", **kwargs)
        root = etree.fromstring(xml)
        return root.find(f".//{{{NS}}}ideEvento")

    def test_indApuracao_mensal(self):
        ide = self._get_ide_evento(ind_apuracao="1")
        assert ide.find(f"{{{NS}}}indApuracao").text == "1"

    def test_indApuracao_decimo_terceiro(self):
        ide = self._get_ide_evento(ind_apuracao="2")
        assert ide.find(f"{{{NS}}}indApuracao").text == "2"

    def test_perApur(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2026-02")
        root = etree.fromstring(xml)
        per = root.find(f".//{{{NS}}}perApur")
        assert per.text == "2026-02"

    def test_tpAmb_homologacao(self):
        ide = self._get_ide_evento(tp_amb="2")
        assert ide.find(f"{{{NS}}}tpAmb").text == "2"

    def test_tpAmb_producao(self):
        ide = self._get_ide_evento(tp_amb="1")
        assert ide.find(f"{{{NS}}}tpAmb").text == "1"

    def test_procEmi(self):
        ide = self._get_ide_evento()
        assert ide.find(f"{{{NS}}}procEmi").text == "1"

    def test_verProc(self):
        ide = self._get_ide_evento()
        assert ide.find(f"{{{NS}}}verProc").text == "EasySocial_1.0"


# ── TEST-S1299-03: Campos de ideEmpregador ───────────────────────
class TestS1299IdeEmpregador:
    def test_tpInsc(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        tp = root.find(f".//{{{NS}}}tpInsc")
        assert tp.text == "1"

    def test_nrInsc_cnpj_raiz_8(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        nr = root.find(f".//{{{NS}}}nrInsc")
        assert nr.text == "05969071"
        assert len(nr.text) == 8

    def test_nrInsc_trunca_cnpj_completo(self):
        emp = {"tpInsc": 1, "nrInsc": "05969071000140"}
        xml = S1299XMLGenerator.gerar(emp, "2025-01")
        root = etree.fromstring(xml)
        nr = root.find(f".//{{{NS}}}nrInsc")
        assert nr.text == "05969071"


# ── TEST-S1299-04: Bloco infoFech (conforme XSD v_S_01_03_00) ───
class TestS1299InfoFech:
    def _get_info_fech(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        return root.find(f".//{{{NS}}}infoFech")

    def test_infoFech_present(self):
        info = self._get_info_fech()
        assert info is not None

    def test_evtRemun_default_S(self):
        info = self._get_info_fech()
        assert info.find(f"{{{NS}}}evtRemun").text == "S"

    def test_evtPgtos_default_S(self):
        info = self._get_info_fech()
        assert info.find(f"{{{NS}}}evtPgtos").text == "S"

    def test_evtComProd_default_N(self):
        info = self._get_info_fech()
        assert info.find(f"{{{NS}}}evtComProd").text == "N"

    def test_evtContratAvNP_default_N(self):
        info = self._get_info_fech()
        assert info.find(f"{{{NS}}}evtContratAvNP").text == "N"

    def test_evtInfoComplPer_default_N(self):
        info = self._get_info_fech()
        assert info.find(f"{{{NS}}}evtInfoComplPer").text == "N"

    def test_nao_tem_evtAqProd(self):
        """evtAqProd NÃO existe no XSD v_S_01_03_00"""
        info = self._get_info_fech()
        assert info.find(f"{{{NS}}}evtAqProd") is None

    def test_nao_tem_ideRespInf(self):
        """ideRespInf NÃO existe no XSD v_S_01_03_00"""
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        assert root.find(f".//{{{NS}}}ideRespInf") is None


# ── TEST-S1299-05: Id do evento ──────────────────────────────────
class TestS1299EventoId:
    def test_id_starts_with_ID(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        evt = root.find(f"{{{NS}}}evtFechaEvPer")
        assert evt.get("Id").startswith("ID")

    def test_id_has_36_chars(self):
        xml = S1299XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        evt = root.find(f"{{{NS}}}evtFechaEvPer")
        assert len(evt.get("Id")) == 36


# ── TEST-S1299-06: Validações de entrada ─────────────────────────
class TestS1299Validacoes:
    def test_tpAmb_invalido(self):
        with pytest.raises(ValueError, match="tpAmb inválido"):
            S1299XMLGenerator.gerar(EMPREGADOR, "2025-01", tp_amb="9")

    def test_indApuracao_invalido(self):
        with pytest.raises(ValueError, match="indApuracao inválido"):
            S1299XMLGenerator.gerar(EMPREGADOR, "2025-01", ind_apuracao="5")

    def test_perApur_formato_errado(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            S1299XMLGenerator.gerar(EMPREGADOR, "202501")


# ── TEST-S1299-07: Geração em lote ──────────────────────────────
class TestS1299Lote:
    def test_gerar_lote_multiplos_periodos(self):
        periodos = ["2025-01", "2025-02", "2025-03"]
        lote = S1299XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        assert len(lote) == 3
        for xml in lote:
            assert isinstance(xml, bytes)
            assert b"evtFechaEvPer" in xml

    def test_lote_cada_perApur_correto(self):
        periodos = ["2025-07", "2025-08"]
        lote = S1299XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        for i, xml in enumerate(lote):
            root = etree.fromstring(xml)
            per = root.find(f".//{{{NS}}}perApur")
            assert per.text == periodos[i]

    def test_lote_todos_tem_infoFech(self):
        periodos = ["2025-01", "2025-02"]
        lote = S1299XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        for xml in lote:
            root = etree.fromstring(xml)
            info = root.find(f".//{{{NS}}}infoFech")
            assert info is not None

    def test_lote_ids_unicos(self):
        periodos = ["2025-01", "2025-02", "2025-03"]
        lote = S1299XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        ids = []
        for xml in lote:
            root = etree.fromstring(xml)
            evt = root.find(f"{{{NS}}}evtFechaEvPer")
            ids.append(evt.get("Id"))
        assert len(set(ids)) == len(ids)

    def test_lote_maximo_50_raises(self):
        with pytest.raises(ValueError, match="máximo: 50"):
            S1299XMLGenerator.gerar_lote(
                EMPREGADOR, [f"2025-{i:02d}" for i in range(1, 52)]
            )

    def test_lote_vazio(self):
        lote = S1299XMLGenerator.gerar_lote(EMPREGADOR, [])
        assert lote == []
