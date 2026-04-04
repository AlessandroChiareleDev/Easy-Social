"""
Testes TDD para Geração de XML S-1298 (Reabertura de Eventos Periódicos)
Valida: namespace, campos obrigatórios, Id, validações de entrada, lote.
"""

import re
import pytest
from lxml import etree

from esocial.xml_s1298 import S1298XMLGenerator

NS = "http://www.esocial.gov.br/schema/evt/evtReabreEvPer/v_S_01_03_00"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}  # CNPJ raiz APPA


# ── TEST-S1298-01: Namespace e estrutura raiz ────────────────────
class TestS1298Namespace:
    def test_root_is_esocial(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        assert root.tag == f"{{{NS}}}eSocial"

    def test_namespace_v_s_01_03_00(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        assert b"v_S_01_03_00" in xml

    def test_has_evtReabreEvPer(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        evt = root.find(f"{{{NS}}}evtReabreEvPer")
        assert evt is not None

    def test_xml_is_bytes_utf8(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        assert isinstance(xml, bytes)
        assert b"UTF-8" in xml


# ── TEST-S1298-02: Campos de ideEvento ───────────────────────────
class TestS1298IdeEvento:
    def _get_ide_evento(self, **kwargs):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01", **kwargs)
        root = etree.fromstring(xml)
        return root.find(f".//{{{NS}}}ideEvento")

    def test_indApuracao_mensal(self):
        ide = self._get_ide_evento(ind_apuracao="1")
        assert ide.find(f"{{{NS}}}indApuracao").text == "1"

    def test_indApuracao_decimo_terceiro(self):
        ide = self._get_ide_evento(ind_apuracao="2")
        assert ide.find(f"{{{NS}}}indApuracao").text == "2"

    def test_perApur(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2026-02")
        root = etree.fromstring(xml)
        per = root.find(f".//{{{NS}}}perApur")
        assert per.text == "2026-02"

    def test_tpAmb_homologacao(self):
        ide = self._get_ide_evento(tp_amb="2")
        assert ide.find(f"{{{NS}}}tpAmb").text == "2"

    def test_tpAmb_producao(self):
        ide = self._get_ide_evento(tp_amb="1")
        assert ide.find(f"{{{NS}}}tpAmb").text == "1"

    def test_procEmi_is_1(self):
        ide = self._get_ide_evento()
        assert ide.find(f"{{{NS}}}procEmi").text == "1"

    def test_verProc(self):
        ide = self._get_ide_evento()
        assert ide.find(f"{{{NS}}}verProc").text == "EasySocial_1.0"


# ── TEST-S1298-03: Campos de ideEmpregador ───────────────────────
class TestS1298IdeEmpregador:
    def test_tpInsc(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        tp = root.find(f".//{{{NS}}}tpInsc")
        assert tp.text == "1"

    def test_nrInsc_cnpj_raiz_8_digitos(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        nr = root.find(f".//{{{NS}}}nrInsc")
        assert nr.text == "05969071"
        assert len(nr.text) == 8

    def test_nrInsc_trunca_14_para_8(self):
        """Regra 646: usar CNPJ raiz (8 dígitos)"""
        emp = {"tpInsc": 1, "nrInsc": "05969071000140"}
        xml = S1298XMLGenerator.gerar(emp, "2025-01")
        root = etree.fromstring(xml)
        nr = root.find(f".//{{{NS}}}nrInsc")
        assert nr.text == "05969071"


# ── TEST-S1298-04: Formato do Id ─────────────────────────────────
class TestS1298EventoId:
    def test_id_starts_with_ID(self):
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        evt = root.find(f"{{{NS}}}evtReabreEvPer")
        evt_id = evt.get("Id")
        assert evt_id.startswith("ID")

    def test_id_has_36_chars(self):
        """ID + tpInsc(1) + nrInsc(14) + timestamp(14) + seq(5) = 36"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        evt = root.find(f"{{{NS}}}evtReabreEvPer")
        evt_id = evt.get("Id")
        assert len(evt_id) == 36

    def test_ids_diferentes_por_seq(self):
        xml1 = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01", seq=1)
        xml2 = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01", seq=2)
        root1 = etree.fromstring(xml1)
        root2 = etree.fromstring(xml2)
        id1 = root1.find(f"{{{NS}}}evtReabreEvPer").get("Id")
        id2 = root2.find(f"{{{NS}}}evtReabreEvPer").get("Id")
        assert id1 != id2


# ── TEST-S1298-05: Validações de entrada ─────────────────────────
class TestS1298Validacoes:
    def test_tpAmb_invalido_raises(self):
        with pytest.raises(ValueError, match="tpAmb inválido"):
            S1298XMLGenerator.gerar(EMPREGADOR, "2025-01", tp_amb="3")

    def test_indApuracao_invalido_raises(self):
        with pytest.raises(ValueError, match="indApuracao inválido"):
            S1298XMLGenerator.gerar(EMPREGADOR, "2025-01", ind_apuracao="0")

    def test_perApur_formato_errado_raises(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            S1298XMLGenerator.gerar(EMPREGADOR, "202501")

    def test_perApur_vazio_raises(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            S1298XMLGenerator.gerar(EMPREGADOR, "")


# ── TEST-S1298-06: Geração em lote ──────────────────────────────
class TestS1298Lote:
    def test_gerar_lote_multiplos_periodos(self):
        periodos = ["2025-01", "2025-02", "2025-03"]
        lote = S1298XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        assert len(lote) == 3
        for xml in lote:
            assert isinstance(xml, bytes)
            assert b"evtReabreEvPer" in xml

    def test_lote_cada_um_tem_perApur_correto(self):
        periodos = ["2025-07", "2025-08", "2025-11"]
        lote = S1298XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        for i, xml in enumerate(lote):
            root = etree.fromstring(xml)
            per = root.find(f".//{{{NS}}}perApur")
            assert per.text == periodos[i]

    def test_lote_ids_unicos(self):
        periodos = ["2025-01", "2025-02"]
        lote = S1298XMLGenerator.gerar_lote(EMPREGADOR, periodos)
        ids = []
        for xml in lote:
            root = etree.fromstring(xml)
            evt = root.find(f"{{{NS}}}evtReabreEvPer")
            ids.append(evt.get("Id"))
        assert len(set(ids)) == len(ids)

    def test_lote_maximo_50_raises(self):
        with pytest.raises(ValueError, match="máximo: 50"):
            S1298XMLGenerator.gerar_lote(EMPREGADOR, [f"2025-{i:02d}" for i in range(1, 52)])

    def test_lote_vazio_retorna_lista_vazia(self):
        lote = S1298XMLGenerator.gerar_lote(EMPREGADOR, [])
        assert lote == []


# ── TEST-S1298-07: Não tem CPF/worker (evento de período) ───────
class TestS1298SemCPF:
    def test_nao_tem_cpf_trabalhador(self):
        """S-1298 é evento de empregador, não de trabalhador"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        # Não deve ter nenhum elemento com CPF de trabalhador
        cpf_trab = root.find(f".//{{{NS}}}cpfTrab")
        assert cpf_trab is None

    def test_nao_tem_ideRespInf(self):
        """S-1298 não tem bloco ideRespInf (diferente de S-1299)"""
        xml = S1298XMLGenerator.gerar(EMPREGADOR, "2025-01")
        root = etree.fromstring(xml)
        resp = root.find(f".//{{{NS}}}ideRespInf")
        assert resp is None
