"""
Testes TDD para Geração de XML S-1210 (Pagamento de Rendimentos do Trabalho)
Valida: namespace, campos obrigatórios, Id, retificação, infoPgto,
        infoIRComplem, dedDepen, validações de entrada, lote.
"""

import re
import pytest
from lxml import etree

from esocial.xml_s1210 import S1210XMLGenerator

NS = "http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}
BENEFICIARIO = {"cpfBenef": "00004225686"}

# Pagamento mínimo válido (1 infoPgto)
INFO_PGTO_MINIMO = [
    {
        "dtPgto": "2026-02-06",
        "tpPgto": "1",
        "perRef": "2026-01",
        "ideDmDev": "01513108",
        "vrLiq": "1323",
    }
]

# Múltiplos pagamentos (2 infoPgto)
INFO_PGTO_MULTIPLO = [
    {
        "dtPgto": "2026-02-06",
        "tpPgto": "1",
        "perRef": "2026-01",
        "ideDmDev": "10712332",
        "vrLiq": "1150",
    },
    {
        "dtPgto": "2026-02-24",
        "tpPgto": "2",
        "perRef": "2026-02",
        "ideDmDev": "10712350",
        "vrLiq": "3895.46",
    },
]

# Complemento IR com dedução de dependente
INFO_IR_COMPLEM = {
    "infoIRCR": [
        {
            "tpCR": "056107",
            "dedDepen": [
                {
                    "tpRend": "11",
                    "cpfDep": "98945769668",
                    "vlrDedDep": "189.59",
                }
            ],
        }
    ]
}

# Complemento IR com vrCR e múltiplas deduções
INFO_IR_COMPLEM_COMPLETO = {
    "infoIRCR": [
        {
            "tpCR": "056107",
            "vrCR": "250.00",
            "dedDepen": [
                {
                    "tpRend": "11",
                    "cpfDep": "98945769668",
                    "vlrDedDep": "189.59",
                },
                {
                    "tpRend": "11",
                    "cpfDep": "03836387719",
                    "vlrDedDep": "189.59",
                },
            ],
        }
    ]
}


def _gerar_xml(**kwargs):
    """Helper para gerar XML com defaults."""
    defaults = {
        "empregador": EMPREGADOR,
        "beneficiario": BENEFICIARIO,
        "info_pgtos": INFO_PGTO_MINIMO,
        "per_apur": "2026-02",
    }
    defaults.update(kwargs)
    return S1210XMLGenerator.gerar(**defaults)


def _parse(xml_bytes):
    return etree.fromstring(xml_bytes)


# ── TEST-S1210-01: Namespace e estrutura raiz ────────────────────
class TestS1210Namespace:
    def test_root_is_esocial(self):
        root = _parse(_gerar_xml())
        assert root.tag == f"{{{NS}}}eSocial"

    def test_namespace_v_s_01_03_00(self):
        xml = _gerar_xml()
        assert b"v_S_01_03_00" in xml

    def test_has_evtPgtos(self):
        root = _parse(_gerar_xml())
        evt = root.find(f"{{{NS}}}evtPgtos")
        assert evt is not None

    def test_xml_is_bytes_utf8(self):
        xml = _gerar_xml()
        assert isinstance(xml, bytes)
        assert b"UTF-8" in xml

    def test_namespace_url_correct(self):
        xml = _gerar_xml()
        assert b"http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00" in xml


# ── TEST-S1210-02: ideEvento — campos básicos ───────────────────
class TestS1210IdeEvento:
    def _get_ide(self, **kwargs):
        root = _parse(_gerar_xml(**kwargs))
        return root.find(f".//{{{NS}}}ideEvento")

    def test_indRetif_original(self):
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}indRetif").text == "1"

    def test_indRetif_retificacao(self):
        ide = self._get_ide(ind_retif="2", nr_recibo="1.1.0000000038892502517")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"

    def test_nrRecibo_presente_quando_retificacao(self):
        ide = self._get_ide(ind_retif="2", nr_recibo="1.1.0000000038892502517")
        assert ide.find(f"{{{NS}}}nrRecibo").text == "1.1.0000000038892502517"

    def test_nrRecibo_ausente_quando_original(self):
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}nrRecibo") is None

    def test_perApur(self):
        ide = self._get_ide(per_apur="2026-02")
        assert ide.find(f"{{{NS}}}perApur").text == "2026-02"

    def test_tpAmb_homologacao(self):
        ide = self._get_ide(tp_amb="2")
        assert ide.find(f"{{{NS}}}tpAmb").text == "2"

    def test_tpAmb_producao(self):
        ide = self._get_ide(tp_amb="1")
        assert ide.find(f"{{{NS}}}tpAmb").text == "1"

    def test_procEmi_is_1(self):
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}procEmi").text == "1"

    def test_verProc(self):
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}verProc").text == "EasySocial_1.0"

    def test_no_indApuracao(self):
        """S-1210 NÃO tem indApuracao (diferente do S-1200)."""
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}indApuracao") is None


# ── TEST-S1210-03: ideEmpregador ────────────────────────────────
class TestS1210IdeEmpregador:
    def test_tpInsc(self):
        root = _parse(_gerar_xml())
        emp = root.find(f".//{{{NS}}}ideEmpregador")
        assert emp.find(f"{{{NS}}}tpInsc").text == "1"

    def test_nrInsc_cnpj_raiz_8_digitos(self):
        root = _parse(_gerar_xml())
        emp = root.find(f".//{{{NS}}}ideEmpregador")
        nr = emp.find(f"{{{NS}}}nrInsc").text
        assert nr == "05969071"
        assert len(nr) == 8


# ── TEST-S1210-04: ideBenef — cpfBenef ──────────────────────────
class TestS1210IdeBenef:
    def test_cpfBenef(self):
        root = _parse(_gerar_xml())
        benef = root.find(f".//{{{NS}}}ideBenef")
        assert benef.find(f"{{{NS}}}cpfBenef").text == "00004225686"

    def test_no_cpfTrab(self):
        """S-1210 usa cpfBenef, não cpfTrab (que é do S-1200)."""
        root = _parse(_gerar_xml())
        assert root.find(f".//{{{NS}}}cpfTrab") is None

    def test_cpfBenef_11_digitos(self):
        root = _parse(_gerar_xml(beneficiario={"cpfBenef": "23127875800"}))
        benef = root.find(f".//{{{NS}}}ideBenef")
        cpf = benef.find(f"{{{NS}}}cpfBenef").text
        assert len(cpf) == 11 and cpf.isdigit()


# ── TEST-S1210-05: infoPgto — Pagamentos ────────────────────────
class TestS1210InfoPgto:
    def test_infoPgto_unico(self):
        root = _parse(_gerar_xml(info_pgtos=INFO_PGTO_MINIMO))
        pgtos = root.findall(f".//{{{NS}}}infoPgto")
        assert len(pgtos) == 1

    def test_infoPgto_multiplo(self):
        root = _parse(_gerar_xml(info_pgtos=INFO_PGTO_MULTIPLO))
        pgtos = root.findall(f".//{{{NS}}}infoPgto")
        assert len(pgtos) == 2

    def test_dtPgto(self):
        root = _parse(_gerar_xml())
        pgto = root.find(f".//{{{NS}}}infoPgto")
        assert pgto.find(f"{{{NS}}}dtPgto").text == "2026-02-06"

    def test_tpPgto(self):
        root = _parse(_gerar_xml())
        pgto = root.find(f".//{{{NS}}}infoPgto")
        assert pgto.find(f"{{{NS}}}tpPgto").text == "1"

    def test_perRef(self):
        root = _parse(_gerar_xml())
        pgto = root.find(f".//{{{NS}}}infoPgto")
        assert pgto.find(f"{{{NS}}}perRef").text == "2026-01"

    def test_ideDmDev(self):
        root = _parse(_gerar_xml())
        pgto = root.find(f".//{{{NS}}}infoPgto")
        assert pgto.find(f"{{{NS}}}ideDmDev").text == "01513108"

    def test_vrLiq(self):
        root = _parse(_gerar_xml())
        pgto = root.find(f".//{{{NS}}}infoPgto")
        assert pgto.find(f"{{{NS}}}vrLiq").text == "1323"

    def test_multiplo_valores_corretos(self):
        root = _parse(_gerar_xml(info_pgtos=INFO_PGTO_MULTIPLO))
        pgtos = root.findall(f".//{{{NS}}}infoPgto")
        assert pgtos[0].find(f"{{{NS}}}tpPgto").text == "1"
        assert pgtos[0].find(f"{{{NS}}}vrLiq").text == "1150"
        assert pgtos[1].find(f"{{{NS}}}tpPgto").text == "2"
        assert pgtos[1].find(f"{{{NS}}}vrLiq").text == "3895.46"

    def test_perRef_opcional(self):
        """perRef pode ser omitido em infoPgto."""
        pgto_sem_perref = [
            {
                "dtPgto": "2026-02-06",
                "tpPgto": "1",
                "ideDmDev": "01513108",
                "vrLiq": "1323",
            }
        ]
        root = _parse(_gerar_xml(info_pgtos=pgto_sem_perref))
        pgto = root.find(f".//{{{NS}}}infoPgto")
        assert pgto.find(f"{{{NS}}}perRef") is None

    def test_infoPgto_dentro_de_ideBenef(self):
        root = _parse(_gerar_xml())
        benef = root.find(f".//{{{NS}}}ideBenef")
        pgto = benef.find(f"{{{NS}}}infoPgto")
        assert pgto is not None


# ── TEST-S1210-06: infoIRComplem — Complemento IR ───────────────
class TestS1210InfoIRComplem:
    def test_sem_ir_complem(self):
        root = _parse(_gerar_xml())
        assert root.find(f".//{{{NS}}}infoIRComplem") is None

    def test_com_ir_complem(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM))
        irc = root.find(f".//{{{NS}}}infoIRComplem")
        assert irc is not None

    def test_tpCR(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM))
        tpcr = root.find(f".//{{{NS}}}tpCR")
        assert tpcr.text == "056107"

    def test_dedDepen_tpRend(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM))
        dd = root.find(f".//{{{NS}}}dedDepen")
        assert dd.find(f"{{{NS}}}tpRend").text == "11"

    def test_dedDepen_cpfDep(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM))
        dd = root.find(f".//{{{NS}}}dedDepen")
        assert dd.find(f"{{{NS}}}cpfDep").text == "98945769668"

    def test_dedDepen_vlrDedDep(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM))
        dd = root.find(f".//{{{NS}}}dedDepen")
        assert dd.find(f"{{{NS}}}vlrDedDep").text == "189.59"

    def test_vrCR_presente(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM_COMPLETO))
        ircr = root.find(f".//{{{NS}}}infoIRCR")
        assert ircr.find(f"{{{NS}}}vrCR").text == "250.00"

    def test_multiplas_deducoes(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM_COMPLETO))
        deps = root.findall(f".//{{{NS}}}dedDepen")
        assert len(deps) == 2

    def test_ir_complem_dentro_de_ideBenef(self):
        root = _parse(_gerar_xml(info_ir_complem=INFO_IR_COMPLEM))
        benef = root.find(f".//{{{NS}}}ideBenef")
        irc = benef.find(f"{{{NS}}}infoIRComplem")
        assert irc is not None

    def test_ir_sem_dedDepen(self):
        """infoIRCR pode existir sem dedDepen."""
        ir = {"infoIRCR": [{"tpCR": "056107"}]}
        root = _parse(_gerar_xml(info_ir_complem=ir))
        assert root.find(f".//{{{NS}}}infoIRCR") is not None
        assert root.find(f".//{{{NS}}}dedDepen") is None


# ── TEST-S1210-07: Id do evento ─────────────────────────────────
class TestS1210EventId:
    def test_id_starts_with_ID(self):
        root = _parse(_gerar_xml())
        evt = root.find(f"{{{NS}}}evtPgtos")
        assert evt.get("Id").startswith("ID")

    def test_id_contains_tp_insc(self):
        root = _parse(_gerar_xml())
        evt_id = root.find(f"{{{NS}}}evtPgtos").get("Id")
        assert evt_id[2] == "1"  # tpInsc=1 (CNPJ)

    def test_id_contains_nr_insc(self):
        root = _parse(_gerar_xml())
        evt_id = root.find(f"{{{NS}}}evtPgtos").get("Id")
        assert "05969071" in evt_id

    def test_id_length(self):
        root = _parse(_gerar_xml())
        evt_id = root.find(f"{{{NS}}}evtPgtos").get("Id")
        assert len(evt_id) == 36  # ID + 1 + 14 + 14 + 5 = 36

    def test_ids_unicos_em_lote(self):
        xmls = S1210XMLGenerator.gerar_lote(
            empregador=EMPREGADOR,
            eventos=[
                {
                    "beneficiario": BENEFICIARIO,
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                },
                {
                    "beneficiario": {"cpfBenef": "23127875800"},
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                },
            ],
        )
        ids = set()
        for xml in xmls:
            root = _parse(xml)
            ids.add(root.find(f"{{{NS}}}evtPgtos").get("Id"))
        assert len(ids) == 2


# ── TEST-S1210-08: Retificação ──────────────────────────────────
class TestS1210Retificacao:
    def test_gerar_retificacao_indRetif_2(self):
        xml = S1210XMLGenerator.gerar_retificacao(
            empregador=EMPREGADOR,
            beneficiario=BENEFICIARIO,
            info_pgtos=INFO_PGTO_MINIMO,
            per_apur="2026-02",
            nr_recibo="1.1.0000000038892502517",
        )
        root = _parse(xml)
        ide = root.find(f".//{{{NS}}}ideEvento")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"
        assert ide.find(f"{{{NS}}}nrRecibo").text == "1.1.0000000038892502517"

    def test_retificacao_com_ir_complem(self):
        xml = S1210XMLGenerator.gerar_retificacao(
            empregador=EMPREGADOR,
            beneficiario=BENEFICIARIO,
            info_pgtos=INFO_PGTO_MULTIPLO,
            per_apur="2026-02",
            nr_recibo="1.1.0000000038892502517",
            info_ir_complem=INFO_IR_COMPLEM,
        )
        root = _parse(xml)
        assert root.find(f".//{{{NS}}}infoIRComplem") is not None
        assert root.find(f".//{{{NS}}}tpCR").text == "056107"


# ── TEST-S1210-09: Validações de entrada ────────────────────────
class TestS1210Validacoes:
    def test_tpAmb_invalido(self):
        with pytest.raises(ValueError, match="tpAmb inválido"):
            _gerar_xml(tp_amb="3")

    def test_indRetif_invalido(self):
        with pytest.raises(ValueError, match="indRetif inválido"):
            _gerar_xml(ind_retif="3")

    def test_perApur_invalido_formato(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            _gerar_xml(per_apur="202602")

    def test_perApur_vazio(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            _gerar_xml(per_apur="")

    def test_retificacao_sem_recibo(self):
        with pytest.raises(ValueError, match="nrRecibo é obrigatório"):
            _gerar_xml(ind_retif="2")

    def test_cpfBenef_invalido_curto(self):
        with pytest.raises(ValueError, match="cpfBenef inválido"):
            _gerar_xml(beneficiario={"cpfBenef": "123"})

    def test_cpfBenef_invalido_nao_numerico(self):
        with pytest.raises(ValueError, match="cpfBenef inválido"):
            _gerar_xml(beneficiario={"cpfBenef": "ABCDEFGHIJK"})

    def test_cpfBenef_vazio(self):
        with pytest.raises(ValueError, match="cpfBenef inválido"):
            _gerar_xml(beneficiario={"cpfBenef": ""})

    def test_info_pgtos_vazio(self):
        with pytest.raises(ValueError, match="info_pgtos não pode ser vazio"):
            _gerar_xml(info_pgtos=[])


# ── TEST-S1210-10: Lote ─────────────────────────────────────────
class TestS1210Lote:
    def test_lote_dois_eventos(self):
        xmls = S1210XMLGenerator.gerar_lote(
            empregador=EMPREGADOR,
            eventos=[
                {
                    "beneficiario": BENEFICIARIO,
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                },
                {
                    "beneficiario": {"cpfBenef": "23127875800"},
                    "info_pgtos": INFO_PGTO_MULTIPLO,
                    "per_apur": "2026-02",
                },
            ],
        )
        assert len(xmls) == 2
        for xml in xmls:
            assert isinstance(xml, bytes)
            root = _parse(xml)
            assert root.find(f"{{{NS}}}evtPgtos") is not None

    def test_lote_maximo_50(self):
        with pytest.raises(ValueError, match="Lote máximo: 50"):
            S1210XMLGenerator.gerar_lote(
                empregador=EMPREGADOR,
                eventos=[
                    {
                        "beneficiario": BENEFICIARIO,
                        "info_pgtos": INFO_PGTO_MINIMO,
                        "per_apur": "2026-02",
                    }
                ]
                * 51,
            )

    def test_lote_com_retificacao(self):
        xmls = S1210XMLGenerator.gerar_lote(
            empregador=EMPREGADOR,
            eventos=[
                {
                    "beneficiario": BENEFICIARIO,
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                    "ind_retif": "2",
                    "nr_recibo": "1.1.0000000038892502517",
                },
            ],
        )
        root = _parse(xmls[0])
        ide = root.find(f".//{{{NS}}}ideEvento")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"

    def test_lote_com_ir_complem(self):
        xmls = S1210XMLGenerator.gerar_lote(
            empregador=EMPREGADOR,
            eventos=[
                {
                    "beneficiario": BENEFICIARIO,
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                    "info_ir_complem": INFO_IR_COMPLEM,
                },
            ],
        )
        root = _parse(xmls[0])
        assert root.find(f".//{{{NS}}}infoIRComplem") is not None

    def test_lote_cpfs_diferentes(self):
        xmls = S1210XMLGenerator.gerar_lote(
            empregador=EMPREGADOR,
            eventos=[
                {
                    "beneficiario": {"cpfBenef": "00004225686"},
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                },
                {
                    "beneficiario": {"cpfBenef": "23127875800"},
                    "info_pgtos": INFO_PGTO_MINIMO,
                    "per_apur": "2026-02",
                },
            ],
        )
        cpf1 = _parse(xmls[0]).find(f".//{{{NS}}}cpfBenef").text
        cpf2 = _parse(xmls[1]).find(f".//{{{NS}}}cpfBenef").text
        assert cpf1 == "00004225686"
        assert cpf2 == "23127875800"


# ── TEST-S1210-11: Estrutura completa — XML realista ────────────
class TestS1210EstruturaCompleta:
    def test_xml_completo_com_tudo(self):
        """Gera S-1210 com múltiplos pagamentos + IR complem + dedDepen."""
        xml = _gerar_xml(
            info_pgtos=INFO_PGTO_MULTIPLO,
            info_ir_complem=INFO_IR_COMPLEM_COMPLETO,
        )
        root = _parse(xml)

        # Verificar estrutura
        evt = root.find(f"{{{NS}}}evtPgtos")
        assert evt is not None

        # ideEvento
        ide = evt.find(f"{{{NS}}}ideEvento")
        assert ide.find(f"{{{NS}}}indRetif").text == "1"
        assert ide.find(f"{{{NS}}}perApur").text == "2026-02"

        # ideEmpregador
        emp = evt.find(f"{{{NS}}}ideEmpregador")
        assert emp.find(f"{{{NS}}}nrInsc").text == "05969071"

        # ideBenef
        benef = evt.find(f"{{{NS}}}ideBenef")
        assert benef.find(f"{{{NS}}}cpfBenef").text == "00004225686"

        # 2 infoPgto
        pgtos = benef.findall(f"{{{NS}}}infoPgto")
        assert len(pgtos) == 2
        assert pgtos[0].find(f"{{{NS}}}dtPgto").text == "2026-02-06"
        assert pgtos[1].find(f"{{{NS}}}dtPgto").text == "2026-02-24"

        # infoIRComplem
        irc = benef.find(f"{{{NS}}}infoIRComplem")
        assert irc is not None
        ircr = irc.find(f"{{{NS}}}infoIRCR")
        assert ircr.find(f"{{{NS}}}tpCR").text == "056107"
        assert ircr.find(f"{{{NS}}}vrCR").text == "250.00"

        # 2 dedDepen
        deps = ircr.findall(f"{{{NS}}}dedDepen")
        assert len(deps) == 2

    def test_xml_retificacao_completa(self):
        """Retificação S-1210 com dados completos."""
        xml = S1210XMLGenerator.gerar_retificacao(
            empregador=EMPREGADOR,
            beneficiario=BENEFICIARIO,
            info_pgtos=INFO_PGTO_MULTIPLO,
            per_apur="2026-02",
            nr_recibo="1.1.0000000038892502517",
            info_ir_complem=INFO_IR_COMPLEM,
            tp_amb="1",
        )
        root = _parse(xml)

        ide = root.find(f".//{{{NS}}}ideEvento")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"
        assert ide.find(f"{{{NS}}}nrRecibo").text == "1.1.0000000038892502517"
        assert ide.find(f"{{{NS}}}tpAmb").text == "1"

        pgtos = root.findall(f".//{{{NS}}}infoPgto")
        assert len(pgtos) == 2

        assert root.find(f".//{{{NS}}}tpCR").text == "056107"

    def test_ordem_elementos_ideEvento(self):
        """Garante ordem: indRetif, [nrRecibo], perApur, tpAmb, procEmi, verProc."""
        root = _parse(_gerar_xml())
        ide = root.find(f".//{{{NS}}}ideEvento")
        tags = [etree.QName(child.tag).localname for child in ide]
        assert tags == ["indRetif", "perApur", "tpAmb", "procEmi", "verProc"]

    def test_ordem_elementos_ideEvento_retificacao(self):
        """Com retificação, nrRecibo vem após indRetif."""
        root = _parse(_gerar_xml(ind_retif="2", nr_recibo="1.1.0000000038892502517"))
        ide = root.find(f".//{{{NS}}}ideEvento")
        tags = [etree.QName(child.tag).localname for child in ide]
        assert tags == ["indRetif", "nrRecibo", "perApur", "tpAmb", "procEmi", "verProc"]

    def test_ordem_elementos_infoPgto(self):
        """Garante ordem: dtPgto, tpPgto, perRef, ideDmDev, vrLiq."""
        root = _parse(_gerar_xml())
        pgto = root.find(f".//{{{NS}}}infoPgto")
        tags = [etree.QName(child.tag).localname for child in pgto]
        assert tags == ["dtPgto", "tpPgto", "perRef", "ideDmDev", "vrLiq"]
