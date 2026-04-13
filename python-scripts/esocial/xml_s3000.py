"""
Gerador de XML S-3000 (evtExclusao) — Exclusão de Eventos

Finalidade: Excluir um evento periódico (S-1200, S-1210, etc.) ou não periódico
            já processado pelo eSocial, usando o nrRecEvt (número do recibo).

Estrutura:
  eSocial > evtExclusao
    ideEvento (tpAmb, procEmi, verProc)
    ideEmpregador (tpInsc, nrInsc)
    infoExclusao
      tpEvento (ex: "S-1210")
      nrRecEvt (recibo do evento a excluir)
      ideTrabalhador (cpfTrab) — obrigatório para eventos com trabalhador
      ideFolhaPagto (indApuracao, perApur) — obrigatório para periódicos

Namespace: v_S_01_03_00
"""

from lxml import etree
from datetime import datetime, timezone

NS = "http://www.esocial.gov.br/schema/evt/evtExclusao/v_S_01_03_00"
NSMAP = {None: NS}


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


class S3000XMLGenerator:
    """Gera XML S-3000 evtExclusao (Exclusão de Eventos)"""

    # Eventos periódicos que exigem ideFolhaPagto
    EVENTOS_PERIODICOS = {"S-1200", "S-1202", "S-1207", "S-1210", "S-1260",
                          "S-1270", "S-1280", "S-1298", "S-1299"}

    # Eventos que exigem ideTrabalhador
    EVENTOS_COM_TRABALHADOR = {"S-1200", "S-1202", "S-1207", "S-1210",
                                "S-2190", "S-2200", "S-2205", "S-2206",
                                "S-2210", "S-2220", "S-2230", "S-2240",
                                "S-2299", "S-2300", "S-2306", "S-2399",
                                "S-2400", "S-2405", "S-2410", "S-2416",
                                "S-2418", "S-2420", "S-2500", "S-2501"}

    @staticmethod
    def gerar(
        empregador: dict,
        tp_evento: str,
        nr_rec_evt: str,
        cpf_trab: str = None,
        per_apur: str = None,
        ind_apuracao: str = "1",
        seq: int = 1,
        tp_amb: str = "2",
    ) -> bytes:
        """
        Gera XML S-3000 para exclusão de um evento.

        Args:
            empregador: dict com tpInsc e nrInsc
            tp_evento: tipo do evento a excluir (ex: "S-1210")
            nr_rec_evt: número do recibo do evento a excluir
            cpf_trab: CPF do trabalhador (obrigatório para eventos com trab.)
            per_apur: período de apuração (obrigatório para eventos periódicos)
            ind_apuracao: "1" = mensal, "2" = 13º salário
            seq: sequencial para ID
            tp_amb: "1" = produção, "2" = homologação

        Returns:
            XML como bytes (UTF-8)
        """
        if tp_amb not in ("1", "2"):
            raise ValueError(f"tpAmb inválido: {tp_amb}")

        if not nr_rec_evt:
            raise ValueError("nrRecEvt obrigatório para exclusão")

        if tp_evento in S3000XMLGenerator.EVENTOS_COM_TRABALHADOR and not cpf_trab:
            raise ValueError(f"cpfTrab obrigatório para exclusão de {tp_evento}")

        if tp_evento in S3000XMLGenerator.EVENTOS_PERIODICOS and not per_apur:
            raise ValueError(f"perApur obrigatório para exclusão de {tp_evento}")

        tp_insc = int(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]

        evt_id = _gerar_id(tp_insc, nr_insc, seq)

        # Root
        root = etree.Element(f"{{{NS}}}eSocial", nsmap=NSMAP)
        evt = _sub(root, "evtExclusao")
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

        # infoExclusao
        info_exc = _sub(evt, "infoExclusao")
        _sub(info_exc, "tpEvento", tp_evento)
        _sub(info_exc, "nrRecEvt", nr_rec_evt)

        # ideTrabalhador (se evento exige)
        if tp_evento in S3000XMLGenerator.EVENTOS_COM_TRABALHADOR and cpf_trab:
            ide_trab = _sub(info_exc, "ideTrabalhador")
            _sub(ide_trab, "cpfTrab", cpf_trab)

        # ideFolhaPagto (se evento periódico — apenas perApur)
        if tp_evento in S3000XMLGenerator.EVENTOS_PERIODICOS and per_apur:
            ide_folha = _sub(info_exc, "ideFolhaPagto")
            _sub(ide_folha, "perApur", per_apur)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")
