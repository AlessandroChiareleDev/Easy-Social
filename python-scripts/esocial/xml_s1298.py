"""
Gerador de XML S-1298 (evtReabreEvPer) — Reabertura de Eventos Periódicos
Namespace: v_S_01_03_00
Finalidade: Reabrir folha de período já fechado (S-1299) para permitir
            retificações de S-1200/S-1210 naquele mês.

Referências:
  - RESPOSTAS_SANDRO_CALL_02-04-2026.md §2, §4.1
  - PESQUISA_RETIFICACAO_S1210_S5002.md §3
  - MAPA_PROBLEMAS_02-04-2026.md §7.1
  - Evento real importado no Explorador (perApur=2026-02, recibo=1.1.0000000038945334564)
"""

from lxml import etree
from datetime import datetime, timezone

NS = "http://www.esocial.gov.br/schema/evt/evtReabreEvPer/v_S_01_03_00"
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


class S1298XMLGenerator:
    """Gera XML S-1298 evtReabreEvPer (Reabertura de Eventos Periódicos)"""

    AMBIENTES_VALIDOS = {"1", "2"}  # 1=Produção, 2=Homologação
    IND_APURACAO_VALIDOS = {"1", "2"}  # 1=Mensal, 2=Décimo terceiro

    @staticmethod
    def gerar(
        empregador: dict,
        per_apur: str,
        ind_apuracao: str = "1",
        seq: int = 1,
        tp_amb: str = "2",
    ) -> bytes:
        """
        Gera XML S-1298 para reabertura de um período.

        Args:
            empregador: dict com tpInsc e nrInsc (CNPJ raiz 8 dígitos)
            per_apur: período de apuração (AAAA-MM, ex: "2025-01")
            ind_apuracao: "1" = mensal, "2" = 13º salário
            seq: sequencial para ID do evento
            tp_amb: "1" = produção, "2" = homologação

        Returns:
            XML como bytes (UTF-8)

        Raises:
            ValueError: se parâmetros inválidos
        """
        if tp_amb not in S1298XMLGenerator.AMBIENTES_VALIDOS:
            raise ValueError(f"tpAmb inválido: {tp_amb}. Use '1' (produção) ou '2' (homologação)")

        if ind_apuracao not in S1298XMLGenerator.IND_APURACAO_VALIDOS:
            raise ValueError(f"indApuracao inválido: {ind_apuracao}. Use '1' (mensal) ou '2' (13º)")

        if not per_apur or len(per_apur) != 7 or per_apur[4] != "-":
            raise ValueError(f"perApur inválido: {per_apur}. Formato esperado: AAAA-MM")

        tp_insc = int(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]  # CNPJ raiz — Regra 646

        evt_id = _gerar_id(tp_insc, nr_insc, seq)

        # Root
        root = etree.Element(f"{{{NS}}}eSocial", nsmap=NSMAP)
        evt = _sub(root, "evtReabreEvPer")
        evt.set("Id", evt_id)

        # ideEvento
        ide_evento = _sub(evt, "ideEvento")
        _sub(ide_evento, "indApuracao", ind_apuracao)
        _sub(ide_evento, "perApur", per_apur)
        _sub(ide_evento, "tpAmb", tp_amb)
        _sub(ide_evento, "procEmi", "1")
        _sub(ide_evento, "verProc", "EasySocial_1.0")

        # ideEmpregador
        ide_emp = _sub(evt, "ideEmpregador")
        _sub(ide_emp, "tpInsc", str(tp_insc))
        _sub(ide_emp, "nrInsc", nr_insc)

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    @staticmethod
    def gerar_lote(
        empregador: dict,
        periodos: list[str],
        ind_apuracao: str = "1",
        tp_amb: str = "2",
    ) -> list[bytes]:
        """
        Gera lote de XMLs S-1298 para múltiplos períodos.

        Args:
            empregador: dict com tpInsc e nrInsc
            periodos: lista de perApur (ex: ["2025-01", "2025-02", ...])
            ind_apuracao: "1" = mensal, "2" = 13º salário
            tp_amb: "1" ou "2"

        Returns:
            Lista de XMLs como bytes

        Raises:
            ValueError: se lote > 50
        """
        if len(periodos) > 50:
            raise ValueError(f"Lote máximo: 50 eventos. Recebido: {len(periodos)}")

        return [
            S1298XMLGenerator.gerar(
                empregador, per_apur, ind_apuracao, seq=i, tp_amb=tp_amb
            )
            for i, per_apur in enumerate(periodos, start=1)
        ]
