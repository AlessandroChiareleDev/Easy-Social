"""
Gerador de XML S-1200 (evtRemun) — Remuneração do Trabalhador Vinculado ao RGPS
Namespace: v_S_01_03_00
Finalidade: Informar remuneração de cada trabalhador no período de apuração.
            Suporta indRetif=1 (original) e indRetif=2 (retificação).
"""

from lxml import etree
from datetime import datetime, timezone

NS = "http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00"
NSMAP = {None: NS}


def _sub(parent, tag, text=None):
    """Cria SubElement com namespace qualificado."""
    el = etree.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = str(text)
    return el


def _gerar_id(tp_insc: int, nr_insc: str, seq: int = 1) -> str:
    now = datetime.now(timezone.utc)
    nr_insc_padded = nr_insc.ljust(14, "0")[:14]
    ts = now.strftime("%Y%m%d%H%M%S")
    return f"ID{tp_insc}{nr_insc_padded}{ts}{seq:05d}"


def _build_itens_remun(parent, itens: list[dict]):
    """Monta lista de <itensRemun> dentro de remunPerApur ou remunPerAnt."""
    for item in itens:
        it = _sub(parent, "itensRemun")
        _sub(it, "codRubr", item["codRubr"])
        _sub(it, "ideTabRubr", item["ideTabRubr"])
        if item.get("qtdRubr"):
            _sub(it, "qtdRubr", item["qtdRubr"])
        if item.get("fatorRubr"):
            _sub(it, "fatorRubr", item["fatorRubr"])
        _sub(it, "vrRubr", item["vrRubr"])
        if item.get("indApurIR") is not None:
            _sub(it, "indApurIR", item["indApurIR"])
        if item.get("descFolha"):
            df = item["descFolha"]
            desc = _sub(it, "descFolha")
            _sub(desc, "tpDesc", df["tpDesc"])
            if df.get("instFinanc"):
                _sub(desc, "instFinanc", df["instFinanc"])
            if df.get("nrDoc"):
                _sub(desc, "nrDoc", df["nrDoc"])


def _build_info_ag_nocivo(parent, info: dict):
    """Monta <infoAgNocivo> se presente."""
    if info:
        ag = _sub(parent, "infoAgNocivo")
        _sub(ag, "grauExp", info["grauExp"])


def _build_remun_per_apur(parent, remun_list: list[dict]):
    """Monta <remunPerApur> dentro de <ideEstabLot>."""
    for remun in remun_list:
        rpa = _sub(parent, "remunPerApur")
        _sub(rpa, "matricula", remun["matricula"])
        if remun.get("indSimples"):
            _sub(rpa, "indSimples", remun["indSimples"])
        _build_itens_remun(rpa, remun["itensRemun"])
        _build_info_ag_nocivo(rpa, remun.get("infoAgNocivo"))


def _build_ide_estab_lot(parent, estab_list: list[dict], remun_tag: str):
    """Monta lista de <ideEstabLot>."""
    for estab in estab_list:
        ie = _sub(parent, "ideEstabLot")
        _sub(ie, "tpInsc", estab["tpInsc"])
        _sub(ie, "nrInsc", estab["nrInsc"])
        _sub(ie, "codLotacao", estab["codLotacao"])
        if remun_tag == "remunPerApur":
            _build_remun_per_apur(ie, estab["remunPerApur"])
        else:
            _build_remun_per_ant(ie, estab["remunPerAnt"])


def _build_remun_per_ant(parent, remun_list: list[dict]):
    """Monta <remunPerAnt> dentro de <ideEstabLot> (período anterior)."""
    for remun in remun_list:
        rpa = _sub(parent, "remunPerAnt")
        _sub(rpa, "matricula", remun["matricula"])
        _build_itens_remun(rpa, remun["itensRemun"])
        _build_info_ag_nocivo(rpa, remun.get("infoAgNocivo"))


def _build_info_per_apur(dm_dev_el, info: dict):
    """Monta <infoPerApur> com ideEstabLot lista."""
    ipa = _sub(dm_dev_el, "infoPerApur")
    _build_ide_estab_lot(ipa, info["ideEstabLot"], "remunPerApur")


def _build_info_per_ant(dm_dev_el, info: dict):
    """Monta <infoPerAnt> com ideADC lista."""
    ipant = _sub(dm_dev_el, "infoPerAnt")
    for adc in info["ideADC"]:
        ide_adc = _sub(ipant, "ideADC")
        _sub(ide_adc, "tpAcConv", adc["tpAcConv"])
        if adc.get("compAcConv"):
            _sub(ide_adc, "compAcConv", adc["compAcConv"])
        if adc.get("dtEfAcConv"):
            _sub(ide_adc, "dtEfAcConv", adc["dtEfAcConv"])
        _sub(ide_adc, "dsc", adc["dsc"])
        _sub(ide_adc, "remunSuc", adc.get("remunSuc", "N"))

        for periodo in adc["idePeriodo"]:
            ip = _sub(ide_adc, "idePeriodo")
            _sub(ip, "perRef", periodo["perRef"])
            _build_ide_estab_lot(ip, periodo["ideEstabLot"], "remunPerAnt")


class S1200XMLGenerator:
    """Gera XML S-1200 evtRemun (Remuneração do Trabalhador)"""

    AMBIENTES_VALIDOS = {"1", "2"}
    IND_APURACAO_VALIDOS = {"1", "2"}
    IND_RETIF_VALIDOS = {"1", "2"}

    @staticmethod
    def gerar(
        empregador: dict,
        trabalhador: dict,
        dm_devs: list[dict],
        per_apur: str,
        ind_retif: str = "1",
        nr_recibo: str = None,
        ind_apuracao: str = "1",
        seq: int = 1,
        tp_amb: str = "2",
    ) -> bytes:
        """
        Gera XML S-1200 para remuneração de um trabalhador.

        Args:
            empregador: dict com tpInsc e nrInsc (CNPJ raiz 8 dígitos)
            trabalhador: dict com cpfTrab (CPF 11 dígitos)
            dm_devs: lista de demonstrativos — cada um com:
                - ideDmDev: identificador do demonstrativo
                - codCateg: código da categoria do trabalhador
                - infoPerApur: {ideEstabLot: [{tpInsc, nrInsc, codLotacao,
                    remunPerApur: [{matricula, itensRemun: [{codRubr,
                    ideTabRubr, vrRubr, indApurIR, qtdRubr?, fatorRubr?,
                    descFolha?}], infoAgNocivo?}]}]}
                - infoPerAnt: (opcional) para diferenças de períodos anteriores
            per_apur: período de apuração (AAAA-MM)
            ind_retif: "1" = original, "2" = retificação
            nr_recibo: nrRecibo do evento original (obrigatório se indRetif=2)
            ind_apuracao: "1" = mensal, "2" = 13º salário
            seq: sequencial para ID do evento
            tp_amb: "1" = produção, "2" = homologação

        Returns:
            XML como bytes (UTF-8)
        """
        # --- Validações ---
        if tp_amb not in S1200XMLGenerator.AMBIENTES_VALIDOS:
            raise ValueError(f"tpAmb inválido: {tp_amb}. Use '1' (produção) ou '2' (homologação)")
        if ind_apuracao not in S1200XMLGenerator.IND_APURACAO_VALIDOS:
            raise ValueError(f"indApuracao inválido: {ind_apuracao}. Use '1' (mensal) ou '2' (13º)")
        if ind_retif not in S1200XMLGenerator.IND_RETIF_VALIDOS:
            raise ValueError(f"indRetif inválido: {ind_retif}. Use '1' (original) ou '2' (retificação)")
        if not per_apur or len(per_apur) != 7 or per_apur[4] != "-":
            raise ValueError(f"perApur inválido: {per_apur}. Formato esperado: AAAA-MM")
        if ind_retif == "2" and not nr_recibo:
            raise ValueError("nrRecibo é obrigatório quando indRetif=2 (retificação)")

        cpf = str(trabalhador.get("cpfTrab", ""))
        if not cpf or len(cpf) != 11 or not cpf.isdigit():
            raise ValueError(f"cpfTrab inválido: '{cpf}'. Deve ter 11 dígitos numéricos")
        if not dm_devs:
            raise ValueError("dm_devs não pode ser vazio — pelo menos um demonstrativo é obrigatório")

        tp_insc = int(empregador["tpInsc"])
        nr_insc = str(empregador["nrInsc"])[:8]

        evt_id = _gerar_id(tp_insc, nr_insc, seq)

        # --- Root ---
        root = etree.Element(f"{{{NS}}}eSocial", nsmap=NSMAP)
        evt = _sub(root, "evtRemun")
        evt.set("Id", evt_id)

        # --- ideEvento ---
        ide_evento = _sub(evt, "ideEvento")
        _sub(ide_evento, "indRetif", ind_retif)
        if ind_retif == "2":
            _sub(ide_evento, "nrRecibo", nr_recibo)
        _sub(ide_evento, "indApuracao", ind_apuracao)
        _sub(ide_evento, "perApur", per_apur)
        _sub(ide_evento, "tpAmb", tp_amb)
        _sub(ide_evento, "procEmi", "1")
        _sub(ide_evento, "verProc", "EasySocial_1.0")

        # --- ideEmpregador ---
        ide_emp = _sub(evt, "ideEmpregador")
        _sub(ide_emp, "tpInsc", str(tp_insc))
        _sub(ide_emp, "nrInsc", nr_insc)

        # --- ideTrabalhador ---
        ide_trab = _sub(evt, "ideTrabalhador")
        _sub(ide_trab, "cpfTrab", cpf)

        # --- dmDev (um ou mais demonstrativos) ---
        for dm in dm_devs:
            dm_el = _sub(evt, "dmDev")
            _sub(dm_el, "ideDmDev", dm["ideDmDev"])
            if dm.get("codCateg"):
                _sub(dm_el, "codCateg", dm["codCateg"])
            if dm.get("infoPerApur"):
                _build_info_per_apur(dm_el, dm["infoPerApur"])
            if dm.get("infoPerAnt"):
                _build_info_per_ant(dm_el, dm["infoPerAnt"])

        return etree.tostring(root, xml_declaration=True, encoding="UTF-8")

    @staticmethod
    def gerar_retificacao(
        empregador: dict,
        trabalhador: dict,
        dm_devs: list[dict],
        per_apur: str,
        nr_recibo: str,
        ind_apuracao: str = "1",
        seq: int = 1,
        tp_amb: str = "2",
    ) -> bytes:
        """Atalho para gerar S-1200 de retificação (indRetif=2)."""
        return S1200XMLGenerator.gerar(
            empregador=empregador,
            trabalhador=trabalhador,
            dm_devs=dm_devs,
            per_apur=per_apur,
            ind_retif="2",
            nr_recibo=nr_recibo,
            ind_apuracao=ind_apuracao,
            seq=seq,
            tp_amb=tp_amb,
        )

    @staticmethod
    def gerar_lote(
        empregador: dict,
        eventos: list[dict],
        tp_amb: str = "2",
    ) -> list[bytes]:
        """
        Gera lote de XMLs S-1200 para múltiplos trabalhadores.

        Args:
            empregador: dict com tpInsc e nrInsc
            eventos: lista de dicts, cada um com:
                - trabalhador: {cpfTrab}
                - dm_devs: lista de demonstrativos
                - per_apur: período de apuração
                - ind_retif: "1" ou "2" (default "1")
                - nr_recibo: obrigatório se indRetif=2
                - ind_apuracao: "1" ou "2" (default "1")
            tp_amb: "1" = produção, "2" = homologação

        Returns:
            Lista de XMLs como bytes (UTF-8)
        """
        if len(eventos) > 50:
            raise ValueError(f"Lote máximo: 50 eventos. Recebido: {len(eventos)}")

        return [
            S1200XMLGenerator.gerar(
                empregador=empregador,
                trabalhador=ev["trabalhador"],
                dm_devs=ev["dm_devs"],
                per_apur=ev["per_apur"],
                ind_retif=ev.get("ind_retif", "1"),
                nr_recibo=ev.get("nr_recibo"),
                ind_apuracao=ev.get("ind_apuracao", "1"),
                seq=i,
                tp_amb=tp_amb,
            )
            for i, ev in enumerate(eventos, start=1)
        ]
