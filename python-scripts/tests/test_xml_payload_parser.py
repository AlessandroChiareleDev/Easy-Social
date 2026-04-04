"""
Testes TDD para xml_payload_parser.py
Valida: parsing completo de S-1200 e S-1210, extração de metadados,
        round-trip (gerar XML → parsear → comparar), erros, parse_pasta,
        construir_input_pipeline.
"""

import os
import re
import shutil
import tempfile
import pytest
from lxml import etree

from esocial.xml_payload_parser import (
    parse_xml_completo,
    parse_pasta,
    construir_input_pipeline,
    extrair_s1200,
    extrair_s1210,
    extrair_s1210_ir_complem,
    _navigate_to_inner,
    _extrair_metadados,
    _detect_event_type,
    _child_text,
    _xdirect,
    _xdirect_first,
)
from esocial.xml_s1200 import S1200XMLGenerator
from esocial.xml_s1210 import S1210XMLGenerator


# ── Fixtures comuns ─────────────────────────────────────────────────────────

NS_DOWNLOAD = "http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0"
NS_RECIBO = "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0"

EMPREGADOR = {"tpInsc": 1, "nrInsc": "05969071"}
TRABALHADOR = {"cpfTrab": "86223928564"}
BENEFICIARIO = {"cpfBenef": "86223928564"}

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

DM_DEV_MULTI = [
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
                                    "codRubr": "9201",
                                    "ideTabRubr": "1",
                                    "vrRubr": "120.19",
                                    "indApurIR": "0",
                                    "qtdRubr": "30",
                                    "fatorRubr": "2",
                                },
                            ],
                        }
                    ],
                }
            ]
        },
    }
]

INFO_PGTOS_MINIMO = [
    {
        "dtPgto": "2026-02-05",
        "tpPgto": "1",
        "ideDmDev": "00005236",
        "vrLiq": "1200.50",
    }
]

INFO_PGTOS_MULTI = [
    {
        "dtPgto": "2026-02-05",
        "tpPgto": "1",
        "ideDmDev": "00005236",
        "vrLiq": "1200.50",
        "perRef": "2026-02",
    },
    {
        "dtPgto": "2026-02-20",
        "tpPgto": "3",
        "ideDmDev": "00005237",
        "vrLiq": "400.00",
    },
]


def _wrap_in_download(inner_xml_bytes: bytes, nr_recibo: str = "1.2.3456") -> bytes:
    """Envelopa um XML interno no wrapper de download do eSocial."""
    inner_str = inner_xml_bytes.decode("utf-8")
    # Remove a declaração XML do inner se presente
    inner_str = re.sub(r'<\?xml[^?]*\?>\s*', '', inner_str)

    recibo_ns = NS_RECIBO
    wrapper = f'''<?xml version="1.0" encoding="UTF-8"?>
<download xmlns="{NS_DOWNLOAD}">
  <retornoProcessamentoDownload>
    <evento>
      {inner_str}
    </evento>
    <recibo>
      <eSocial xmlns="{recibo_ns}">
        <retornoEvento>
          <processamento>
            <cdResposta>201</cdResposta>
            <descResposta>Sucesso</descResposta>
          </processamento>
          <recibo>
            <nrRecibo>{nr_recibo}</nrRecibo>
          </recibo>
        </retornoEvento>
      </eSocial>
    </recibo>
  </retornoProcessamentoDownload>
</download>'''
    return wrapper.encode("utf-8")


def _write_xml(tmpdir: str, filename: str, xml_bytes: bytes) -> str:
    """Escreve XML no diretório temporário e retorna caminho."""
    path = os.path.join(tmpdir, filename)
    with open(path, "wb") as f:
        f.write(xml_bytes)
    return path


@pytest.fixture
def tmpdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ── Testes de detecção de tipo ──────────────────────────────────────────────

class TestDetectEventType:
    def test_s1200(self):
        assert _detect_event_type("CPF86223928564.S-1200.xml") == "S-1200"

    def test_s1210(self):
        assert _detect_event_type("CPF86223928564.S-1210.xml") == "S-1210"

    def test_s1010(self):
        assert _detect_event_type("rub_350.S-1010.xml") == "S-1010"

    def test_sem_tipo(self):
        assert _detect_event_type("arquivo.xml") is None

    def test_case_insensitive(self):
        assert _detect_event_type("evento.S-1200.XML") == "S-1200"


# ── Testes de XML helpers ───────────────────────────────────────────────────

class TestXmlHelpers:
    def test_child_text(self):
        el = etree.fromstring("<root><nome>teste</nome></root>")
        assert _child_text(el, "nome") == "teste"

    def test_child_text_missing(self):
        el = etree.fromstring("<root><nome>teste</nome></root>")
        assert _child_text(el, "outro") is None

    def test_xdirect(self):
        el = etree.fromstring("<root><a>1</a><a>2</a><b>3</b></root>")
        assert len(_xdirect(el, "a")) == 2

    def test_xdirect_first(self):
        el = etree.fromstring("<root><a>1</a><a>2</a></root>")
        result = _xdirect_first(el, "a")
        assert result.text == "1"

    def test_xdirect_first_missing(self):
        el = etree.fromstring("<root><a>1</a></root>")
        assert _xdirect_first(el, "b") is None


# ── Testes de navegação no wrapper download ─────────────────────────────────

class TestNavigateToInner:
    def test_wrapper_download(self):
        """Navega wrapper de download e encontra inner eSocial."""
        inner_xml = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        wrapped = _wrap_in_download(inner_xml, "1.2.3456")
        root = etree.fromstring(wrapped)
        inner, recibo = _navigate_to_inner(root)
        assert inner is not None
        assert recibo is not None

    def test_xml_direto_sem_wrapper(self):
        """XML sem wrapper de download — detecção direta."""
        inner_xml = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        root = etree.fromstring(inner_xml)
        inner, recibo = _navigate_to_inner(root)
        assert inner is not None
        assert recibo is None


# ── Testes de round-trip S-1200 ─────────────────────────────────────────────

class TestExtrairS1200:
    def test_roundtrip_minimo(self):
        """Gera S-1200 mínimo → parseia → compara dm_devs."""
        xml_bytes = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        dm_devs = extrair_s1200(root)

        assert len(dm_devs) == 1
        dm = dm_devs[0]
        assert dm["ideDmDev"] == "00005236"
        assert dm["codCateg"] == "101"
        assert "infoPerApur" in dm

        estabs = dm["infoPerApur"]["ideEstabLot"]
        assert len(estabs) == 1
        assert estabs[0]["tpInsc"] == "1"
        assert estabs[0]["nrInsc"] == "05969071000110"
        assert estabs[0]["codLotacao"] == "00335-001-02"

        remuns = estabs[0]["remunPerApur"]
        assert len(remuns) == 1
        assert remuns[0]["matricula"] == "007-001-046914"

        itens = remuns[0]["itensRemun"]
        assert len(itens) == 1
        assert itens[0]["codRubr"] == "350"
        assert itens[0]["ideTabRubr"] == "1"
        assert itens[0]["vrRubr"] == "1602.51"
        assert itens[0]["indApurIR"] == "0"

    def test_roundtrip_multi_itens(self):
        """Gera S-1200 com múltiplos itensRemun → parseia → verifica todos."""
        xml_bytes = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MULTI, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        dm_devs = extrair_s1200(root)

        itens = dm_devs[0]["infoPerApur"]["ideEstabLot"][0]["remunPerApur"][0]["itensRemun"]
        assert len(itens) == 2
        assert itens[0]["codRubr"] == "350"
        assert itens[1]["codRubr"] == "9201"
        assert itens[1]["qtdRubr"] == "30"
        assert itens[1]["fatorRubr"] == "2"

    def test_roundtrip_com_info_per_ant(self):
        """S-1200 com infoPerAnt (períodos anteriores)."""
        dm_devs_ant = [
            {
                "ideDmDev": "ANT001",
                "codCateg": "101",
                "infoPerAnt": {
                    "ideADC": [
                        {
                            "tpAcConv": "A",
                            "dsc": "Acordo coletivo 2026",
                            "compAcConv": "2026-01",
                            "remunSuc": "N",
                            "idePeriodo": [
                                {
                                    "perRef": "2026-01",
                                    "ideEstabLot": [
                                        {
                                            "tpInsc": "1",
                                            "nrInsc": "05969071000110",
                                            "codLotacao": "00335-001-02",
                                            "remunPerAnt": [
                                                {
                                                    "matricula": "007-001-046914",
                                                    "itensRemun": [
                                                        {
                                                            "codRubr": "500",
                                                            "ideTabRubr": "1",
                                                            "vrRubr": "300.00",
                                                        }
                                                    ],
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
        xml_bytes = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, dm_devs_ant, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        dm_devs = extrair_s1200(root)

        assert len(dm_devs) == 1
        assert "infoPerAnt" in dm_devs[0]
        ant = dm_devs[0]["infoPerAnt"]
        assert len(ant["ideADC"]) == 1
        adc = ant["ideADC"][0]
        assert adc["tpAcConv"] == "A"
        assert adc["dsc"] == "Acordo coletivo 2026"
        assert adc["compAcConv"] == "2026-01"
        assert len(adc["idePeriodo"]) == 1
        per = adc["idePeriodo"][0]
        assert per["perRef"] == "2026-01"
        assert len(per["ideEstabLot"]) == 1
        remun_ant = per["ideEstabLot"][0]["remunPerAnt"]
        assert len(remun_ant) == 1
        assert remun_ant[0]["itensRemun"][0]["codRubr"] == "500"

    def test_sem_dmdev(self):
        """XML sem dmDev retorna lista vazia."""
        root = etree.fromstring('<root><a>b</a></root>')
        assert extrair_s1200(root) == []


# ── Testes de round-trip S-1210 ─────────────────────────────────────────────

class TestExtrairS1210:
    def test_roundtrip_minimo(self):
        """Gera S-1210 mínimo → parseia → compara info_pgtos."""
        xml_bytes = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MINIMO, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        pgtos = extrair_s1210(root)

        assert len(pgtos) == 1
        assert pgtos[0]["dtPgto"] == "2026-02-05"
        assert pgtos[0]["tpPgto"] == "1"
        assert pgtos[0]["ideDmDev"] == "00005236"
        assert pgtos[0]["vrLiq"] == "1200.50"

    def test_roundtrip_multi_pgtos(self):
        """S-1210 com múltiplos infoPgto."""
        xml_bytes = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MULTI, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        pgtos = extrair_s1210(root)

        assert len(pgtos) == 2
        assert pgtos[0]["tpPgto"] == "1"
        assert pgtos[1]["tpPgto"] == "3"
        assert pgtos[1]["ideDmDev"] == "00005237"
        assert pgtos[0].get("perRef") == "2026-02"

    def test_sem_info_pgto(self):
        """XML sem infoPgto retorna lista vazia."""
        root = etree.fromstring('<root><a>b</a></root>')
        assert extrair_s1210(root) == []


class TestExtrairIRComplem:
    def test_com_ir_complem(self):
        """S-1210 com infoIRComplem + dedDepen."""
        ir_complem = {
            "infoIRCR": [
                {
                    "tpCR": "593656",
                    "vrCR": "150.00",
                    "dedDepen": [
                        {
                            "tpRend": "12",
                            "cpfDep": "12345678901",
                            "vlrDedDep": "189.59",
                        }
                    ],
                }
            ]
        }
        xml_bytes = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MINIMO, "2026-02",
            info_ir_complem=ir_complem,
        )
        root = etree.fromstring(xml_bytes)
        result = extrair_s1210_ir_complem(root)

        assert result is not None
        assert len(result["infoIRCR"]) == 1
        cr = result["infoIRCR"][0]
        assert cr["tpCR"] == "593656"
        assert cr["vrCR"] == "150.00"
        assert len(cr["dedDepen"]) == 1
        dep = cr["dedDepen"][0]
        assert dep["tpRend"] == "12"
        assert dep["cpfDep"] == "12345678901"
        assert dep["vlrDedDep"] == "189.59"

    def test_sem_ir_complem(self):
        """S-1210 sem infoIRComplem retorna None."""
        xml_bytes = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MINIMO, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        assert extrair_s1210_ir_complem(root) is None


# ── Testes de metadados ─────────────────────────────────────────────────────

class TestExtrairMetadados:
    def test_cpf_e_per_apur(self):
        """Extrai CPF e perApur do XML gerado."""
        xml_bytes = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        root = etree.fromstring(xml_bytes)
        meta = _extrair_metadados(root, None)
        assert meta["cpf"] == "86223928564"
        assert meta["per_apur"] == "2026-02"
        assert meta["ind_retif"] == "1"
        assert meta["id_evento"] is not None
        assert meta["id_evento"].startswith("ID")
        assert meta["nr_recibo"] is None

    def test_com_recibo(self):
        """Extrai nr_recibo quando recibo_inner fornecido."""
        xml_bytes = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        wrapped = _wrap_in_download(xml_bytes, "9.8.7654")
        root = etree.fromstring(wrapped)
        inner, recibo = _navigate_to_inner(root)
        meta = _extrair_metadados(inner, recibo)
        assert meta["nr_recibo"] == "9.8.7654"


# ── Testes de parse_xml_completo ────────────────────────────────────────────

class TestParseXmlCompleto:
    def test_s1200_completo(self, tmpdir):
        """Parseia arquivo S-1200 com wrapper de download."""
        inner = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        wrapped = _wrap_in_download(inner, "1.2.3456")
        path = _write_xml(tmpdir, "CPF86223928564.S-1200.xml", wrapped)

        resultado, erro = parse_xml_completo(path)
        assert erro is None
        assert resultado["tipo_evento"] == "S-1200"
        assert resultado["cpf"] == "86223928564"
        assert resultado["per_apur"] == "2026-02"
        assert resultado["nr_recibo"] == "1.2.3456"
        assert len(resultado["dm_devs"]) == 1
        assert resultado["dm_devs"][0]["ideDmDev"] == "00005236"

    def test_s1210_completo(self, tmpdir):
        """Parseia arquivo S-1210 com wrapper de download."""
        inner = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MINIMO, "2026-02"
        )
        wrapped = _wrap_in_download(inner, "4.5.6789")
        path = _write_xml(tmpdir, "CPF86223928564.S-1210.xml", wrapped)

        resultado, erro = parse_xml_completo(path)
        assert erro is None
        assert resultado["tipo_evento"] == "S-1210"
        assert resultado["cpf"] == "86223928564"
        assert resultado["nr_recibo"] == "4.5.6789"
        assert len(resultado["info_pgtos"]) == 1
        assert resultado["info_ir_complem"] is None

    def test_tipo_nao_detectado(self, tmpdir):
        """Arquivo sem padrão de tipo no nome."""
        path = _write_xml(tmpdir, "qualquer.xml", b"<root/>")
        resultado, erro = parse_xml_completo(path)
        assert resultado is None
        assert "não detectado" in erro

    def test_tipo_nao_suportado(self, tmpdir):
        """Arquivo S-1010 (não suportado pelo parser)."""
        path = _write_xml(tmpdir, "rub.S-1010.xml", b"<root/>")
        resultado, erro = parse_xml_completo(path)
        assert resultado is None
        assert "não suportado" in erro

    def test_xml_invalido(self, tmpdir):
        """XML mal-formado."""
        path = _write_xml(tmpdir, "bad.S-1200.xml", b"<<<not xml>>>")
        resultado, erro = parse_xml_completo(path)
        assert resultado is None
        assert "inválido" in erro


# ── Testes de parse_pasta ───────────────────────────────────────────────────

class TestParsePasta:
    def _popular_pasta(self, tmpdir: str, cpf: str = "86223928564"):
        """Cria XMLs de S-1200 e S-1210 na pasta."""
        inner_1200 = S1200XMLGenerator.gerar(
            EMPREGADOR, {"cpfTrab": cpf}, DM_DEV_MINIMO, "2026-02"
        )
        inner_1210 = S1210XMLGenerator.gerar(
            EMPREGADOR, {"cpfBenef": cpf}, INFO_PGTOS_MINIMO, "2026-02"
        )
        _write_xml(tmpdir, f"CPF{cpf}.S-1200.xml",
                    _wrap_in_download(inner_1200, "REC.1200"))
        _write_xml(tmpdir, f"CPF{cpf}.S-1210.xml",
                    _wrap_in_download(inner_1210, "REC.1210"))

    def test_parse_todos(self, tmpdir):
        self._popular_pasta(tmpdir)
        result = parse_pasta(tmpdir)
        assert len(result["eventos"]) == 2
        assert result["resumo"].get("S-1200") == 1
        assert result["resumo"].get("S-1210") == 1
        assert len(result["erros"]) == 0

    def test_filtro_tipo(self, tmpdir):
        self._popular_pasta(tmpdir)
        result = parse_pasta(tmpdir, tipos=["S-1200"])
        assert len(result["eventos"]) == 1
        assert result["eventos"][0]["tipo_evento"] == "S-1200"

    def test_filtro_cpf(self, tmpdir):
        self._popular_pasta(tmpdir, "86223928564")
        self._popular_pasta(tmpdir, "11122233344")
        result = parse_pasta(tmpdir, cpf_filtro="11122233344")
        assert all(e["cpf"] == "11122233344" for e in result["eventos"])

    def test_pasta_inexistente(self):
        result = parse_pasta("/caminho/inexistente/xyz")
        assert len(result["eventos"]) == 0
        assert len(result["erros"]) == 1

    def test_pasta_vazia(self, tmpdir):
        result = parse_pasta(tmpdir)
        assert len(result["eventos"]) == 0
        assert len(result["erros"]) == 0


# ── Testes de construir_input_pipeline ──────────────────────────────────────

class TestConstruirInputPipeline:
    CPF = "86223928564"
    PER = "2026-02"

    def _popular(self, tmpdir):
        inner_1200 = S1200XMLGenerator.gerar(
            EMPREGADOR, {"cpfTrab": self.CPF}, DM_DEV_MINIMO, self.PER
        )
        inner_1210 = S1210XMLGenerator.gerar(
            EMPREGADOR, {"cpfBenef": self.CPF}, INFO_PGTOS_MINIMO, self.PER
        )
        _write_xml(tmpdir, f"CPF{self.CPF}.S-1200.xml",
                    _wrap_in_download(inner_1200, "REC.1200"))
        _write_xml(tmpdir, f"CPF{self.CPF}.S-1210.xml",
                    _wrap_in_download(inner_1210, "REC.1210"))

    def test_input_pipeline_ok(self, tmpdir):
        self._popular(tmpdir)
        result, erro = construir_input_pipeline(tmpdir, self.CPF, self.PER)
        assert erro is None
        assert result["s1200_nr_recibo"] == "REC.1200"
        assert result["s1210_nr_recibo"] == "REC.1210"
        assert len(result["s1200_dm_devs"]) == 1
        assert len(result["s1210_info_pgtos"]) == 1
        assert result["s1200_dm_devs"][0]["ideDmDev"] == "00005236"

    def test_cpf_sem_s1200(self, tmpdir):
        """Sem S-1200 para o CPF."""
        inner_1210 = S1210XMLGenerator.gerar(
            EMPREGADOR, {"cpfBenef": self.CPF}, INFO_PGTOS_MINIMO, self.PER
        )
        _write_xml(tmpdir, f"CPF{self.CPF}.S-1210.xml",
                    _wrap_in_download(inner_1210, "REC.1210"))
        result, erro = construir_input_pipeline(tmpdir, self.CPF, self.PER)
        assert result is None
        assert "S-1200 não encontrado" in erro

    def test_cpf_sem_s1210(self, tmpdir):
        """Sem S-1210 para o CPF."""
        inner_1200 = S1200XMLGenerator.gerar(
            EMPREGADOR, {"cpfTrab": self.CPF}, DM_DEV_MINIMO, self.PER
        )
        _write_xml(tmpdir, f"CPF{self.CPF}.S-1200.xml",
                    _wrap_in_download(inner_1200, "REC.1200"))
        result, erro = construir_input_pipeline(tmpdir, self.CPF, self.PER)
        assert result is None
        assert "S-1210 não encontrado" in erro

    def test_periodo_errado(self, tmpdir):
        """CPF existe mas período não bate."""
        self._popular(tmpdir)
        result, erro = construir_input_pipeline(tmpdir, self.CPF, "2025-01")
        assert result is None
        assert "S-1200 não encontrado" in erro


# ── Teste de roundtrip completo (gerar → gravar → parsear → compara) ───────

class TestRoundtripCompleto:
    def test_s1200_gerar_parsear_comparar(self, tmpdir):
        """
        Gera S-1200 com gerador → wrapa como download →
        parseia com parser → verifica que dm_devs volta intacto.
        """
        orig_dm_devs = DM_DEV_MULTI
        xml_bytes = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, orig_dm_devs, "2026-02"
        )
        wrapped = _wrap_in_download(xml_bytes, "RT.1200")
        path = _write_xml(tmpdir, "CPF86223928564.S-1200.xml", wrapped)

        resultado, erro = parse_xml_completo(path)
        assert erro is None

        parsed_dm = resultado["dm_devs"]
        assert len(parsed_dm) == len(orig_dm_devs)

        for orig, parsed in zip(orig_dm_devs, parsed_dm):
            assert parsed["ideDmDev"] == orig["ideDmDev"]
            assert parsed["codCateg"] == orig["codCateg"]
            orig_estabs = orig["infoPerApur"]["ideEstabLot"]
            parsed_estabs = parsed["infoPerApur"]["ideEstabLot"]
            assert len(parsed_estabs) == len(orig_estabs)

            for oe, pe in zip(orig_estabs, parsed_estabs):
                assert pe["codLotacao"] == oe["codLotacao"]
                assert len(pe["remunPerApur"]) == len(oe["remunPerApur"])

                for or_, pr in zip(oe["remunPerApur"], pe["remunPerApur"]):
                    assert pr["matricula"] == or_["matricula"]
                    assert len(pr["itensRemun"]) == len(or_["itensRemun"])

                    for oi, pi in zip(or_["itensRemun"], pr["itensRemun"]):
                        assert pi["codRubr"] == oi["codRubr"]
                        assert pi["vrRubr"] == oi["vrRubr"]

    def test_s1210_gerar_parsear_comparar(self, tmpdir):
        """
        Gera S-1210 → wrapa → parseia → verifica info_pgtos intacto.
        """
        ir_complem = {
            "infoIRCR": [
                {
                    "tpCR": "593656",
                    "vrCR": "99.00",
                    "dedDepen": [
                        {
                            "tpRend": "12",
                            "cpfDep": "99988877766",
                            "vlrDedDep": "189.59",
                        }
                    ],
                }
            ]
        }
        xml_bytes = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MULTI, "2026-02",
            info_ir_complem=ir_complem,
        )
        wrapped = _wrap_in_download(xml_bytes, "RT.1210")
        path = _write_xml(tmpdir, "CPF86223928564.S-1210.xml", wrapped)

        resultado, erro = parse_xml_completo(path)
        assert erro is None

        assert len(resultado["info_pgtos"]) == len(INFO_PGTOS_MULTI)
        for orig, parsed in zip(INFO_PGTOS_MULTI, resultado["info_pgtos"]):
            assert parsed["dtPgto"] == orig["dtPgto"]
            assert parsed["tpPgto"] == orig["tpPgto"]
            assert parsed["vrLiq"] == orig["vrLiq"]

        assert resultado["info_ir_complem"] is not None
        assert resultado["info_ir_complem"]["infoIRCR"][0]["tpCR"] == "593656"

    def test_input_pipeline_alimenta_gerador(self, tmpdir):
        """
        Gera XMLs → parseia → monta input_pipeline → usa para re-gerar
        (verifica que o formato do parser é compatível com o gerador).
        """
        inner_1200 = S1200XMLGenerator.gerar(
            EMPREGADOR, TRABALHADOR, DM_DEV_MINIMO, "2026-02"
        )
        inner_1210 = S1210XMLGenerator.gerar(
            EMPREGADOR, BENEFICIARIO, INFO_PGTOS_MINIMO, "2026-02"
        )
        _write_xml(tmpdir, "CPF86223928564.S-1200.xml",
                    _wrap_in_download(inner_1200, "REC.1200"))
        _write_xml(tmpdir, "CPF86223928564.S-1210.xml",
                    _wrap_in_download(inner_1210, "REC.1210"))

        pipeline_input, erro = construir_input_pipeline(
            tmpdir, "86223928564", "2026-02"
        )
        assert erro is None

        # Re-gerar S-1200 com dm_devs extraído
        xml_retif = S1200XMLGenerator.gerar_retificacao(
            EMPREGADOR, TRABALHADOR,
            dm_devs=pipeline_input["s1200_dm_devs"],
            per_apur="2026-02",
            nr_recibo=pipeline_input["s1200_nr_recibo"],
        )
        # Deve gerar XML válido
        root = etree.fromstring(xml_retif)
        assert root.tag.endswith("eSocial")

        # Re-gerar S-1210 com info_pgtos extraído
        xml_retif_1210 = S1210XMLGenerator.gerar_retificacao(
            EMPREGADOR, BENEFICIARIO,
            info_pgtos=pipeline_input["s1210_info_pgtos"],
            per_apur="2026-02",
            nr_recibo=pipeline_input["s1210_nr_recibo"],
            info_ir_complem=pipeline_input.get("s1210_info_ir_complem"),
        )
        root_1210 = etree.fromstring(xml_retif_1210)
        assert root_1210.tag.endswith("eSocial")
