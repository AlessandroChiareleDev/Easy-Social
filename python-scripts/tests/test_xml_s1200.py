"""
Testes TDD para Geração de XML S-1200 (Remuneração do Trabalhador)
Valida: namespace, campos obrigatórios, Id, retificação, itensRemun,
        dmDev, ideEstabLot, validações de entrada, lote.
"""

import re
import pytest
from lxml import etree

from esocial.xml_s1200 import S1200XMLGenerator

NS = "http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}
TRABALHADOR = {"cpfTrab": "86223928564"}

# Demonstrativo mínimo válido (1 dmDev, 1 ideEstabLot, 1 remunPerApur, 1 itensRemun)
DM_DEV_MINIMO = [
    {
        "ideDmDev": "00005236",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [
                {
                    "tpInsc": "1",
                    "nrInsc": "05969071000110",
                    "codLotacao": "00335-001-02",
                    "remunPerApur": [
                        {
                            "matricula": "007-001-046914",
                            "itensRemun": [
                                {
                                    "codRubr": "350",
                                    "ideTabRubr": "1",
                                    "vrRubr": "1602.51",
                                    "indApurIR": "0",
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    }
]

# Demonstrativo completo com múltiplos itens, qtdRubr e descFolha
DM_DEV_COMPLETO = [
    {
        "ideDmDev": "00005236",
        "codCateg": "101",
        "infoPerApur": {
            "ideEstabLot": [
                {
                    "tpInsc": "1",
                    "nrInsc": "05969071000110",
                    "codLotacao": "00335-001-02",
                    "remunPerApur": [
                        {
                            "matricula": "007-001-046914",
                            "itensRemun": [
                                {
                                    "codRubr": "350",
                                    "ideTabRubr": "1",
                                    "vrRubr": "1602.51",
                                    "indApurIR": "0",
                                },
                                {
                                    "codRubr": "641",
                                    "ideTabRubr": "1",
                                    "qtdRubr": "9.00",
                                    "vrRubr": "170.42",
                                    "indApurIR": "0",
                                },
                                {
                                    "codRubr": "1016",
                                    "ideTabRubr": "1",
                                    "vrRubr": "303.23",
                                    "indApurIR": "0",
                                    "descFolha": {
                                        "tpDesc": "1",
                                        "instFinanc": "389",
                                        "nrDoc": "000590609144",
                                    },
                                },
                            ],
                            "infoAgNocivo": {"grauExp": "1"},
                        }
                    ],
                }
            ]
        },
    }
]


def _gerar_xml(**kwargs):
    """Helper para gerar XML com defaults."""
    defaults = {
        "empregador": EMPREGADOR,
        "trabalhador": TRABALHADOR,
        "dm_devs": DM_DEV_MINIMO,
        "per_apur": "2026-02",
    }
    defaults.update(kwargs)
    return S1200XMLGenerator.gerar(**defaults)


def _parse(xml_bytes):
    return etree.fromstring(xml_bytes)


# ── TEST-S1200-01: Namespace e estrutura raiz ────────────────────
class TestS1200Namespace:
    def test_root_is_esocial(self):
        root = _parse(_gerar_xml())
        assert root.tag == f"{{{NS}}}eSocial"

    def test_namespace_v_s_01_03_00(self):
        xml = _gerar_xml()
        assert b"v_S_01_03_00" in xml

    def test_has_evtRemun(self):
        root = _parse(_gerar_xml())
        evt = root.find(f"{{{NS}}}evtRemun")
        assert evt is not None

    def test_xml_is_bytes_utf8(self):
        xml = _gerar_xml()
        assert isinstance(xml, bytes)
        assert b"UTF-8" in xml

    def test_namespace_url_correct(self):
        xml = _gerar_xml()
        assert b"http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00" in xml


# ── TEST-S1200-02: ideEvento — campos básicos ───────────────────
class TestS1200IdeEvento:
    def _get_ide(self, **kwargs):
        root = _parse(_gerar_xml(**kwargs))
        return root.find(f".//{{{NS}}}ideEvento")

    def test_indRetif_original(self):
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}indRetif").text == "1"

    def test_indRetif_retificacao(self):
        ide = self._get_ide(ind_retif="2", nr_recibo="1.1.0000000038566203364")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"

    def test_nrRecibo_presente_quando_retificacao(self):
        ide = self._get_ide(ind_retif="2", nr_recibo="1.1.0000000038566203364")
        assert ide.find(f"{{{NS}}}nrRecibo").text == "1.1.0000000038566203364"

    def test_nrRecibo_ausente_quando_original(self):
        ide = self._get_ide()
        assert ide.find(f"{{{NS}}}nrRecibo") is None

    def test_indApuracao_mensal(self):
        ide = self._get_ide(ind_apuracao="1")
        assert ide.find(f"{{{NS}}}indApuracao").text == "1"

    def test_indApuracao_decimo_terceiro(self):
        ide = self._get_ide(ind_apuracao="2")
        assert ide.find(f"{{{NS}}}indApuracao").text == "2"

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


# ── TEST-S1200-03: ideEmpregador ────────────────────────────────
class TestS1200IdeEmpregador:
    def test_tpInsc(self):
        root = _parse(_gerar_xml())
        tp = root.find(f".//{{{NS}}}tpInsc")
        assert tp.text == "1"

    def test_nrInsc_cnpj_raiz_8_digitos(self):
        root = _parse(_gerar_xml())
        # ideEmpregador nrInsc
        emp = root.find(f".//{{{NS}}}ideEmpregador")
        nr = emp.find(f"{{{NS}}}nrInsc")
        assert nr.text == "05969071"
        assert len(nr.text) == 8

    def test_nrInsc_trunca_14_para_8(self):
        emp = {"tpInsc": 1, "nrInsc": "05969071000140"}
        root = _parse(_gerar_xml(empregador=emp))
        emp_el = root.find(f".//{{{NS}}}ideEmpregador")
        nr = emp_el.find(f"{{{NS}}}nrInsc")
        assert nr.text == "05969071"


# ── TEST-S1200-04: ideTrabalhador ───────────────────────────────
class TestS1200IdeTrabalhador:
    def test_cpfTrab(self):
        root = _parse(_gerar_xml())
        cpf = root.find(f".//{{{NS}}}cpfTrab")
        assert cpf.text == "86223928564"
        assert len(cpf.text) == 11


# ── TEST-S1200-05: Formato do Id ────────────────────────────────
class TestS1200EventoId:
    def test_id_starts_with_ID(self):
        root = _parse(_gerar_xml())
        evt = root.find(f"{{{NS}}}evtRemun")
        assert evt.get("Id").startswith("ID")

    def test_id_has_36_chars(self):
        root = _parse(_gerar_xml())
        evt = root.find(f"{{{NS}}}evtRemun")
        assert len(evt.get("Id")) == 36

    def test_ids_diferentes_por_seq(self):
        xml1 = _gerar_xml(seq=1)
        xml2 = _gerar_xml(seq=2)
        id1 = _parse(xml1).find(f"{{{NS}}}evtRemun").get("Id")
        id2 = _parse(xml2).find(f"{{{NS}}}evtRemun").get("Id")
        assert id1 != id2


# ── TEST-S1200-06: dmDev e infoPerApur ──────────────────────────
class TestS1200DmDev:
    def test_has_dmDev(self):
        root = _parse(_gerar_xml())
        dm = root.find(f".//{{{NS}}}dmDev")
        assert dm is not None

    def test_ideDmDev(self):
        root = _parse(_gerar_xml())
        ide = root.find(f".//{{{NS}}}ideDmDev")
        assert ide.text == "00005236"

    def test_codCateg(self):
        root = _parse(_gerar_xml())
        cat = root.find(f".//{{{NS}}}codCateg")
        assert cat.text == "101"

    def test_has_infoPerApur(self):
        root = _parse(_gerar_xml())
        info = root.find(f".//{{{NS}}}infoPerApur")
        assert info is not None

    def test_ideEstabLot_fields(self):
        root = _parse(_gerar_xml())
        estab = root.find(f".//{{{NS}}}ideEstabLot")
        assert estab.find(f"{{{NS}}}tpInsc").text == "1"
        assert estab.find(f"{{{NS}}}nrInsc").text == "05969071000110"
        assert estab.find(f"{{{NS}}}codLotacao").text == "00335-001-02"

    def test_remunPerApur_matricula(self):
        root = _parse(_gerar_xml())
        mat = root.find(f".//{{{NS}}}matricula")
        assert mat.text == "007-001-046914"

    def test_multiple_dm_devs(self):
        dm_devs = [
            {
                "ideDmDev": "DM001",
                "codCateg": "101",
                "infoPerApur": {
                    "ideEstabLot": [
                        {
                            "tpInsc": "1",
                            "nrInsc": "05969071000110",
                            "codLotacao": "LOT-01",
                            "remunPerApur": [
                                {
                                    "matricula": "MAT-001",
                                    "itensRemun": [
                                        {"codRubr": "100", "ideTabRubr": "1", "vrRubr": "500.00"}
                                    ],
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "ideDmDev": "DM002",
                "codCateg": "101",
                "infoPerApur": {
                    "ideEstabLot": [
                        {
                            "tpInsc": "1",
                            "nrInsc": "05969071000110",
                            "codLotacao": "LOT-02",
                            "remunPerApur": [
                                {
                                    "matricula": "MAT-001",
                                    "itensRemun": [
                                        {"codRubr": "200", "ideTabRubr": "1", "vrRubr": "300.00"}
                                    ],
                                }
                            ],
                        }
                    ]
                },
            },
        ]
        root = _parse(_gerar_xml(dm_devs=dm_devs))
        dm_els = root.findall(f".//{{{NS}}}dmDev")
        assert len(dm_els) == 2
        ids = [dm.find(f"{{{NS}}}ideDmDev").text for dm in dm_els]
        assert ids == ["DM001", "DM002"]


# ── TEST-S1200-07: itensRemun ───────────────────────────────────
class TestS1200ItensRemun:
    def test_itens_remun_basico(self):
        root = _parse(_gerar_xml())
        item = root.find(f".//{{{NS}}}itensRemun")
        assert item.find(f"{{{NS}}}codRubr").text == "350"
        assert item.find(f"{{{NS}}}ideTabRubr").text == "1"
        assert item.find(f"{{{NS}}}vrRubr").text == "1602.51"
        assert item.find(f"{{{NS}}}indApurIR").text == "0"

    def test_multiplos_itens_remun(self):
        root = _parse(_gerar_xml(dm_devs=DM_DEV_COMPLETO))
        itens = root.findall(f".//{{{NS}}}itensRemun")
        assert len(itens) == 3

    def test_qtdRubr_presente(self):
        root = _parse(_gerar_xml(dm_devs=DM_DEV_COMPLETO))
        itens = root.findall(f".//{{{NS}}}itensRemun")
        # O segundo item (641) tem qtdRubr
        item_641 = [i for i in itens if i.find(f"{{{NS}}}codRubr").text == "641"][0]
        assert item_641.find(f"{{{NS}}}qtdRubr").text == "9.00"

    def test_qtdRubr_ausente_quando_nao_informado(self):
        root = _parse(_gerar_xml())
        item = root.find(f".//{{{NS}}}itensRemun")
        assert item.find(f"{{{NS}}}qtdRubr") is None

    def test_descFolha_presente(self):
        root = _parse(_gerar_xml(dm_devs=DM_DEV_COMPLETO))
        itens = root.findall(f".//{{{NS}}}itensRemun")
        item_1016 = [i for i in itens if i.find(f"{{{NS}}}codRubr").text == "1016"][0]
        desc = item_1016.find(f"{{{NS}}}descFolha")
        assert desc is not None
        assert desc.find(f"{{{NS}}}tpDesc").text == "1"
        assert desc.find(f"{{{NS}}}instFinanc").text == "389"
        assert desc.find(f"{{{NS}}}nrDoc").text == "000590609144"

    def test_infoAgNocivo(self):
        root = _parse(_gerar_xml(dm_devs=DM_DEV_COMPLETO))
        ag = root.find(f".//{{{NS}}}infoAgNocivo")
        assert ag is not None
        assert ag.find(f"{{{NS}}}grauExp").text == "1"


# ── TEST-S1200-08: Retificação (indRetif=2) ─────────────────────
class TestS1200Retificacao:
    NR_RECIBO = "1.1.0000000038566203364"

    def test_gerar_retificacao_shortcut(self):
        xml = S1200XMLGenerator.gerar_retificacao(
            empregador=EMPREGADOR,
            trabalhador=TRABALHADOR,
            dm_devs=DM_DEV_MINIMO,
            per_apur="2026-02",
            nr_recibo=self.NR_RECIBO,
        )
        root = _parse(xml)
        ide = root.find(f".//{{{NS}}}ideEvento")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"
        assert ide.find(f"{{{NS}}}nrRecibo").text == self.NR_RECIBO

    def test_retificacao_sem_recibo_raises(self):
        with pytest.raises(ValueError, match="nrRecibo é obrigatório"):
            _gerar_xml(ind_retif="2", nr_recibo=None)

    def test_retificacao_com_recibo_vazio_raises(self):
        with pytest.raises(ValueError, match="nrRecibo é obrigatório"):
            _gerar_xml(ind_retif="2", nr_recibo="")


# ── TEST-S1200-09: Validações de entrada ────────────────────────
class TestS1200Validacoes:
    def test_tpAmb_invalido_raises(self):
        with pytest.raises(ValueError, match="tpAmb inválido"):
            _gerar_xml(tp_amb="3")

    def test_indApuracao_invalido_raises(self):
        with pytest.raises(ValueError, match="indApuracao inválido"):
            _gerar_xml(ind_apuracao="0")

    def test_indRetif_invalido_raises(self):
        with pytest.raises(ValueError, match="indRetif inválido"):
            _gerar_xml(ind_retif="3")

    def test_perApur_formato_errado_raises(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            _gerar_xml(per_apur="202602")

    def test_perApur_vazio_raises(self):
        with pytest.raises(ValueError, match="perApur inválido"):
            _gerar_xml(per_apur="")

    def test_cpf_invalido_curto_raises(self):
        with pytest.raises(ValueError, match="cpfTrab inválido"):
            _gerar_xml(trabalhador={"cpfTrab": "123"})

    def test_cpf_com_letras_raises(self):
        with pytest.raises(ValueError, match="cpfTrab inválido"):
            _gerar_xml(trabalhador={"cpfTrab": "8622392856A"})

    def test_dm_devs_vazio_raises(self):
        with pytest.raises(ValueError, match="dm_devs não pode ser vazio"):
            _gerar_xml(dm_devs=[])


# ── TEST-S1200-10: infoPerAnt (período anterior) ────────────────
class TestS1200InfoPerAnt:
    DM_DEV_ANT = [
        {
            "ideDmDev": "01513124",
            "codCateg": "106",
            "infoPerAnt": {
                "ideADC": [
                    {
                        "tpAcConv": "F",
                        "dsc": "RESCISAO COMPLEMENTAR",
                        "remunSuc": "N",
                        "idePeriodo": [
                            {
                                "perRef": "2026-01",
                                "ideEstabLot": [
                                    {
                                        "tpInsc": "1",
                                        "nrInsc": "05969071000110",
                                        "codLotacao": "02045-001-01",
                                        "remunPerAnt": [
                                            {
                                                "matricula": "002-000-862041",
                                                "itensRemun": [
                                                    {
                                                        "codRubr": "151",
                                                        "ideTabRubr": "1",
                                                        "vrRubr": "288.00",
                                                        "indApurIR": "0",
                                                    }
                                                ],
                                                "infoAgNocivo": {"grauExp": "1"},
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    ]

    def test_has_infoPerAnt(self):
        root = _parse(_gerar_xml(dm_devs=self.DM_DEV_ANT))
        info = root.find(f".//{{{NS}}}infoPerAnt")
        assert info is not None

    def test_ideADC_fields(self):
        root = _parse(_gerar_xml(dm_devs=self.DM_DEV_ANT))
        adc = root.find(f".//{{{NS}}}ideADC")
        assert adc.find(f"{{{NS}}}tpAcConv").text == "F"
        assert adc.find(f"{{{NS}}}dsc").text == "RESCISAO COMPLEMENTAR"
        assert adc.find(f"{{{NS}}}remunSuc").text == "N"

    def test_idePeriodo_perRef(self):
        root = _parse(_gerar_xml(dm_devs=self.DM_DEV_ANT))
        per = root.find(f".//{{{NS}}}perRef")
        assert per.text == "2026-01"

    def test_remunPerAnt_matricula(self):
        root = _parse(_gerar_xml(dm_devs=self.DM_DEV_ANT))
        mat = root.find(f".//{{{NS}}}matricula")
        assert mat.text == "002-000-862041"

    def test_remunPerAnt_itensRemun(self):
        root = _parse(_gerar_xml(dm_devs=self.DM_DEV_ANT))
        item = root.find(f".//{{{NS}}}itensRemun")
        assert item.find(f"{{{NS}}}codRubr").text == "151"
        assert item.find(f"{{{NS}}}vrRubr").text == "288.00"

    def test_infoAgNocivo_perAnt(self):
        root = _parse(_gerar_xml(dm_devs=self.DM_DEV_ANT))
        ag = root.find(f".//{{{NS}}}infoAgNocivo")
        assert ag.find(f"{{{NS}}}grauExp").text == "1"


# ── TEST-S1200-11: Geração em lote ──────────────────────────────
class TestS1200Lote:
    def test_gerar_lote(self):
        eventos = [
            {
                "trabalhador": {"cpfTrab": "86223928564"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            },
            {
                "trabalhador": {"cpfTrab": "12517018685"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            },
        ]
        lote = S1200XMLGenerator.gerar_lote(EMPREGADOR, eventos)
        assert len(lote) == 2
        for xml in lote:
            assert isinstance(xml, bytes)
            assert b"evtRemun" in xml

    def test_lote_cpfs_distintos(self):
        eventos = [
            {
                "trabalhador": {"cpfTrab": "86223928564"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            },
            {
                "trabalhador": {"cpfTrab": "12517018685"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            },
        ]
        lote = S1200XMLGenerator.gerar_lote(EMPREGADOR, eventos)
        cpfs = []
        for xml in lote:
            root = _parse(xml)
            cpf = root.find(f".//{{{NS}}}cpfTrab").text
            cpfs.append(cpf)
        assert cpfs == ["86223928564", "12517018685"]

    def test_lote_ids_unicos(self):
        eventos = [
            {
                "trabalhador": {"cpfTrab": "86223928564"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            },
            {
                "trabalhador": {"cpfTrab": "12517018685"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            },
        ]
        lote = S1200XMLGenerator.gerar_lote(EMPREGADOR, eventos)
        ids = [_parse(xml).find(f"{{{NS}}}evtRemun").get("Id") for xml in lote]
        assert len(set(ids)) == len(ids)

    def test_lote_maximo_50_raises(self):
        eventos = [
            {
                "trabalhador": {"cpfTrab": f"{i:011d}"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
            }
            for i in range(51)
        ]
        with pytest.raises(ValueError, match="máximo: 50"):
            S1200XMLGenerator.gerar_lote(EMPREGADOR, eventos)

    def test_lote_com_retificacao(self):
        eventos = [
            {
                "trabalhador": {"cpfTrab": "86223928564"},
                "dm_devs": DM_DEV_MINIMO,
                "per_apur": "2026-02",
                "ind_retif": "2",
                "nr_recibo": "1.1.0000000038566203364",
            },
        ]
        lote = S1200XMLGenerator.gerar_lote(EMPREGADOR, eventos)
        root = _parse(lote[0])
        ide = root.find(f".//{{{NS}}}ideEvento")
        assert ide.find(f"{{{NS}}}indRetif").text == "2"
        assert ide.find(f"{{{NS}}}nrRecibo").text == "1.1.0000000038566203364"

    def test_lote_vazio_retorna_lista_vazia(self):
        lote = S1200XMLGenerator.gerar_lote(EMPREGADOR, [])
        assert lote == []


# ── TEST-S1200-12: Conformidade com XML real importado ───────────
class TestS1200ConformidadeReal:
    """Testa que o XML gerado segue a mesma estrutura dos XMLs reais importados."""

    def test_ordem_elementos_ideEvento(self):
        """indRetif → [nrRecibo] → indApuracao → perApur → tpAmb → procEmi → verProc"""
        root = _parse(_gerar_xml())
        ide = root.find(f".//{{{NS}}}ideEvento")
        tags = [child.tag.split("}")[-1] for child in ide]
        expected = ["indRetif", "indApuracao", "perApur", "tpAmb", "procEmi", "verProc"]
        assert tags == expected

    def test_ordem_elementos_ideEvento_retificacao(self):
        root = _parse(_gerar_xml(ind_retif="2", nr_recibo="REC123"))
        ide = root.find(f".//{{{NS}}}ideEvento")
        tags = [child.tag.split("}")[-1] for child in ide]
        expected = ["indRetif", "nrRecibo", "indApuracao", "perApur", "tpAmb", "procEmi", "verProc"]
        assert tags == expected

    def test_ordem_filhos_evtRemun(self):
        """ideEvento → ideEmpregador → ideTrabalhador → dmDev"""
        root = _parse(_gerar_xml())
        evt = root.find(f"{{{NS}}}evtRemun")
        tags = [child.tag.split("}")[-1] for child in evt]
        assert tags == ["ideEvento", "ideEmpregador", "ideTrabalhador", "dmDev"]

    def test_ordem_filhos_dmDev(self):
        """ideDmDev → codCateg → infoPerApur"""
        root = _parse(_gerar_xml())
        dm = root.find(f".//{{{NS}}}dmDev")
        tags = [child.tag.split("}")[-1] for child in dm]
        assert tags == ["ideDmDev", "codCateg", "infoPerApur"]
