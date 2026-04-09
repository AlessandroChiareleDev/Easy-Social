"""
Gerador de XML S-1010 (evtTabRubrica) — modos inclusão e alteração
Namespace: v_S_01_03_00
Ambiente: Homologação (tpAmb=2) — exclusivamente
"""

from lxml import etree
from datetime import datetime, timezone

NS = "http://www.esocial.gov.br/schema/evt/evtTabRubrica/v_S_01_03_00"
NSMAP = {None: NS}

# Tabela 04 — codIncCP (INSS)
VALID_COD_INC_CP = {
    0, 1, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25, 26,
    31, 32, 34, 35, 51, 61, 91, 92, 93, 94, 95, 96, 97, 98,
}

# Tabela 21 — codIncIRRF
VALID_COD_INC_IRRF = {
    0, 1, 9, 11, 12, 13, 14, 15, 31, 32, 33, 34, 35,
    41, 42, 43, 44, 46, 47, 48, 51, 52, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67, 68, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
    81, 82, 83, 91, 92, 93, 94, 95, 702, 703, 704,
}

# Tabela 22 — codIncFGTS
VALID_COD_INC_FGTS = {0, 11, 12, 21, 91, 92, 93}


def _sub(parent, tag, text=None):
    el = etree.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def _gerar_id(tp_insc: int, nr_insc: str, seq: int = 1) -> str:
    now = datetime.now(timezone.utc)
    nr_insc_padded = nr_insc.ljust(14, "0")[:14]
    ts = now.strftime("%Y%m%d%H%M%S")
    return f"ID{tp_insc}{nr_insc_padded}{ts}{seq:05d}"


def _validar_incidencias(rubrica: dict):
    cod_cp = int(rubrica["codIncCP"])
    if cod_cp not in VALID_COD_INC_CP:
        raise ValueError(f"codIncCP={cod_cp} inválido. Valores válidos: {sorted(VALID_COD_INC_CP)}")

    cod_irrf = int(rubrica["codIncIRRF"])
    if cod_irrf not in VALID_COD_INC_IRRF:
        raise ValueError(f"codIncIRRF={cod_irrf} inválido. Valores válidos: {sorted(VALID_COD_INC_IRRF)}")

    cod_fgts = int(rubrica["codIncFGTS"])
    if cod_fgts not in VALID_COD_INC_FGTS:
        raise ValueError(f"codIncFGTS={cod_fgts} inválido. Valores válidos: {sorted(VALID_COD_INC_FGTS)}")


class S1010XMLGenerator:
    """Gera XML S-1010 evtTabRubrica nos modos inclusão e alteração"""

    AMBIENTES_VALIDOS = {"1", "2"}  # 1=Produção, 2=Homologação

    @staticmethod
    def _gerar_dados_rubrica(dados_parent, rubrica: dict):
        """Gera o bloco dadosRubrica (comum a inclusão e alteração)."""
        dados = _sub(dados_parent, "dadosRubrica")
        _sub(dados, "dscRubr", str(rubrica["dscRubr"])[:100])
        _sub(dados, "natRubr", str(int(rubrica["natRubr"])))
        _sub(dados, "tpRubr", str(int(rubrica["tpRubr"])))
        _sub(dados, "codIncCP", f"{int(rubrica['codIncCP']):02d}")
        _sub(dados, "codIncIRRF", f"{int(rubrica['codIncIRRF']):02d}")
        _sub(dados, "codIncFGTS", f"{int(rubrica['codIncFGTS']):02d}")
        _sub(dados, "codIncPisPasep", f"{int(rubrica.get('codIncPisPasep', 0)):02d}")
        if rubrica.get("tetoRemun"):
            _sub(dados, "tetoRemun", str(rubrica["tetoRemun"]))
        if rubrica.get("observacao"):
            _sub(dados, "observacao", str(rubrica["observacao"])[:255])
        return dados

    @staticmethod
    def _gerar_base(empregador: dict, rubrica: dict, seq: int = 1, tp_amb: str = "2"):
        """Gera a estrutura base do evento (root, evt, ideRubrica)."""
        if tp_amb not in S1010XMLGenerator.AMBIENTES_VALIDOS:
            raise ValueError(f"tpAmb inválido: {tp_amb}. Use '1' (produção) ou '2' (homologação)")
        _validar_incidencias(rubrica)

        tp_insc = int(empregador["tpInsc"])
        nr_insc_raw = str(empregador["nrInsc"])
        nr_insc = nr_insc_raw[:8]  # CNPJ raiz — Regra 646

        evt_id = _gerar_id(tp_insc, nr_insc, seq)

        root = etree.Element(f"{{{NS}}}eSocial", nsmap=NSMAP)
        evt = _sub(root, "evtTabRubrica")
        evt.set("Id", evt_id)

        # ideEvento
        ide_evento = _sub(evt, "ideEvento")
        _sub(ide_evento, "tpAmb", tp_amb)
        _sub(ide_evento, "procEmi", "1")
        _sub(ide_evento, "verProc", "EasySocial_1.0")

        # ideEmpregador
        ide_emp = _sub(evt, "ideEmpregador")
        _sub(ide_emp, "tpInsc", str(tp_insc))
        _sub(ide_emp, "nrInsc", nr_insc)

        return root, evt

    @staticmethod
    def gerar_inclusao(empregador: dict, rubrica: dict, seq: int = 1, tp_amb: str = "2") -> bytes:
        """Gera XML S-1010 no modo inclusão."""
        root, evt = S1010XMLGenerator._gerar_base(empregador, rubrica, seq, tp_amb=tp_amb)

        info_rubrica = _sub(evt, "infoRubrica")
        inclusao = _sub(info_rubrica, "inclusao")

        # ideRubrica
        ide_rubrica = _sub(inclusao, "ideRubrica")
        _sub(ide_rubrica, "codRubr", str(rubrica["codRubr"]))
        _sub(ide_rubrica, "ideTabRubr", str(rubrica.get("ideTabRubr", "1")))
        _sub(ide_rubrica, "iniValid", str(rubrica["iniValid"]))
        if rubrica.get("fimValid"):
            _sub(ide_rubrica, "fimValid", str(rubrica["fimValid"]))

        # dadosRubrica
        S1010XMLGenerator._gerar_dados_rubrica(inclusao, rubrica)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    @staticmethod
    def gerar_alteracao(empregador: dict, rubrica: dict, seq: int = 1, tp_amb: str = "2") -> bytes:
        """Gera XML S-1010 no modo alteração."""
        root, evt = S1010XMLGenerator._gerar_base(empregador, rubrica, seq, tp_amb=tp_amb)

        # infoRubrica > alteracao
        info_rubrica = _sub(evt, "infoRubrica")
        alteracao = _sub(info_rubrica, "alteracao")

        # ideRubrica
        ide_rubrica = _sub(alteracao, "ideRubrica")
        _sub(ide_rubrica, "codRubr", str(rubrica["codRubr"]))
        _sub(ide_rubrica, "ideTabRubr", str(rubrica.get("ideTabRubr", "1")))
        _sub(ide_rubrica, "iniValid", str(rubrica["iniValid"]))
        if rubrica.get("fimValid"):
            _sub(ide_rubrica, "fimValid", str(rubrica["fimValid"]))

        # dadosRubrica
        S1010XMLGenerator._gerar_dados_rubrica(alteracao, rubrica)

        # novaValidade (opcional)
        if rubrica.get("novaIniValid"):
            nova = _sub(alteracao, "novaValidade")
            _sub(nova, "iniValid", str(rubrica["novaIniValid"]))
            if rubrica.get("novaFimValid"):
                _sub(nova, "fimValid", str(rubrica["novaFimValid"]))

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    @staticmethod
    def gerar_lote_alteracao(empregador: dict, rubricas: list[dict], tp_amb: str = "2") -> list[bytes]:
        if len(rubricas) > 50:
            raise ValueError("Lote máximo: 50 eventos. Recebido: " + str(len(rubricas)))
        return [
            S1010XMLGenerator.gerar_alteracao(empregador, rub, seq=i, tp_amb=tp_amb)
            for i, rub in enumerate(rubricas, start=1)
        ]
