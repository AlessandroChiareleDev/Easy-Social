"""
Parser de XMLs do eSocial — Extrai payload COMPLETO de S-1200 e S-1210.

O explorador_routes.py importa eventos mas guarda apenas resumo.
Este módulo extrai a estrutura COMPLETA (dm_devs, info_pgtos) para
alimentar o pipeline de retificação (pipeline_correcao.py).

Suporta:
  - Arquivo individual (.xml)
  - Pasta com múltiplos XMLs
  - Formato de download eSocial (wrapper retornoProcessamentoDownload)
"""

import os
import re
from typing import Optional
from lxml import etree

NS_DOWNLOAD = "http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0"

# ── XPath helpers (namespace-agnostic) ──────────────────────────────────────

_xpath_cache: dict = {}


def _get_xpath(local_name: str):
    if local_name not in _xpath_cache:
        _xpath_cache[local_name] = etree.XPath(f'.//*[local-name()="{local_name}"]')
    return _xpath_cache[local_name]


def _xtext(el, local_name: str) -> Optional[str]:
    """Texto do primeiro descendente com local-name (namespace-agnostic)."""
    hits = _get_xpath(local_name)(el)
    if hits and hits[0].text:
        return hits[0].text.strip()
    return None


def _xall(el, local_name: str) -> list:
    """Todos os descendentes com local-name."""
    return _get_xpath(local_name)(el)


def _xdirect(parent, local_name: str) -> list:
    """Filhos DIRETOS com local-name (não recursivo)."""
    return [c for c in parent if etree.QName(c.tag).localname == local_name]


def _xdirect_first(parent, local_name: str):
    """Primeiro filho direto com local-name, ou None."""
    for c in parent:
        if etree.QName(c.tag).localname == local_name:
            return c
    return None


def _child_text(parent, local_name: str) -> Optional[str]:
    """Texto de um filho direto (não recursivo)."""
    el = _xdirect_first(parent, local_name)
    if el is not None and el.text:
        return el.text.strip()
    return None


# ── Detecção de tipo de evento ──────────────────────────────────────────────

def _detect_event_type(filename: str) -> Optional[str]:
    m = re.search(r'\.(S-\d+)\.xml$', filename, re.IGNORECASE)
    return m.group(1).upper() if m else None


# ── Navegação no XML de download eSocial ────────────────────────────────────

def _navigate_to_inner(root) -> tuple:
    """
    Navega pela estrutura de wrapper do download eSocial.
    Returns: (inner_esocial, recibo_inner) ou (None, None)
    """
    evento_wrapper = root.find(
        f'{{{NS_DOWNLOAD}}}retornoProcessamentoDownload/{{{NS_DOWNLOAD}}}evento'
    )
    recibo_wrapper = root.find(
        f'{{{NS_DOWNLOAD}}}retornoProcessamentoDownload/{{{NS_DOWNLOAD}}}recibo'
    )

    if evento_wrapper is None:
        # Pode ser XML direto (sem wrapper de download)
        # Tentar encontrar evtRemun ou evtPgtos diretamente
        for tag in ["evtRemun", "evtPgtos"]:
            hits = _xall(root, tag)
            if hits:
                return root, None
        return None, None

    inner_esocial = None
    for child in evento_wrapper:
        if 'eSocial' in child.tag:
            inner_esocial = child
            break

    recibo_inner = None
    if recibo_wrapper is not None:
        for child in recibo_wrapper:
            if 'eSocial' in child.tag:
                recibo_inner = child
                break

    return inner_esocial, recibo_inner


# ── S-1200: Extrair dm_devs completo ────────────────────────────────────────

def _extract_itens_remun(remun_el) -> list[dict]:
    """Extrai lista de itensRemun de um remunPerApur/remunPerAnt."""
    itens = []
    for item in _xdirect(remun_el, "itensRemun"):
        it = {
            "codRubr": _child_text(item, "codRubr"),
            "ideTabRubr": _child_text(item, "ideTabRubr") or "1",
            "vrRubr": _child_text(item, "vrRubr"),
        }
        # Campos opcionais
        qtd = _child_text(item, "qtdRubr")
        if qtd:
            it["qtdRubr"] = qtd
        fator = _child_text(item, "fatorRubr")
        if fator:
            it["fatorRubr"] = fator
        ind = _child_text(item, "indApurIR")
        if ind is not None:
            it["indApurIR"] = ind

        # descFolha (sub-estrutura opcional)
        desc_folha = _xdirect_first(item, "descFolha")
        if desc_folha is not None:
            df = {"tpDesc": _child_text(desc_folha, "tpDesc")}
            inst = _child_text(desc_folha, "instFinanc")
            if inst:
                df["instFinanc"] = inst
            nr_doc = _child_text(desc_folha, "nrDoc")
            if nr_doc:
                df["nrDoc"] = nr_doc
            it["descFolha"] = df

        if it["codRubr"]:
            itens.append(it)
    return itens


def _extract_info_ag_nocivo(remun_el) -> Optional[dict]:
    """Extrai infoAgNocivo se presente."""
    ag = _xdirect_first(remun_el, "infoAgNocivo")
    if ag is not None:
        grau = _child_text(ag, "grauExp")
        if grau:
            return {"grauExp": grau}
    return None


def _extract_remun_per_apur(estab_el) -> list[dict]:
    """Extrai lista de remunPerApur de um ideEstabLot."""
    remuns = []
    for rpa in _xdirect(estab_el, "remunPerApur"):
        remun = {
            "matricula": _child_text(rpa, "matricula") or "",
            "itensRemun": _extract_itens_remun(rpa),
        }
        ind_simples = _child_text(rpa, "indSimples")
        if ind_simples:
            remun["indSimples"] = ind_simples
        ag = _extract_info_ag_nocivo(rpa)
        if ag:
            remun["infoAgNocivo"] = ag
        remuns.append(remun)
    return remuns


def _extract_remun_per_ant(estab_el) -> list[dict]:
    """Extrai lista de remunPerAnt de um ideEstabLot (períodos anteriores)."""
    remuns = []
    for rpa in _xdirect(estab_el, "remunPerAnt"):
        remun = {
            "matricula": _child_text(rpa, "matricula") or "",
            "itensRemun": _extract_itens_remun(rpa),
        }
        ag = _extract_info_ag_nocivo(rpa)
        if ag:
            remun["infoAgNocivo"] = ag
        remuns.append(remun)
    return remuns


def _extract_ide_estab_lot(parent_el, remun_tag: str) -> list[dict]:
    """Extrai lista de ideEstabLot."""
    estabs = []
    for ie in _xdirect(parent_el, "ideEstabLot"):
        estab = {
            "tpInsc": _child_text(ie, "tpInsc") or "1",
            "nrInsc": _child_text(ie, "nrInsc") or "",
            "codLotacao": _child_text(ie, "codLotacao") or "",
        }
        if remun_tag == "remunPerApur":
            estab["remunPerApur"] = _extract_remun_per_apur(ie)
        else:
            estab["remunPerAnt"] = _extract_remun_per_ant(ie)
        estabs.append(estab)
    return estabs


def _extract_info_per_apur(dm_dev_el) -> Optional[dict]:
    """Extrai infoPerApur completo de um dmDev."""
    ipa = _xdirect_first(dm_dev_el, "infoPerApur")
    if ipa is None:
        return None
    return {"ideEstabLot": _extract_ide_estab_lot(ipa, "remunPerApur")}


def _extract_info_per_ant(dm_dev_el) -> Optional[dict]:
    """Extrai infoPerAnt completo de um dmDev (períodos anteriores)."""
    ipant = _xdirect_first(dm_dev_el, "infoPerAnt")
    if ipant is None:
        return None

    ide_adcs = []
    for adc in _xdirect(ipant, "ideADC"):
        adc_data = {
            "tpAcConv": _child_text(adc, "tpAcConv") or "",
            "dsc": _child_text(adc, "dsc") or "",
        }
        comp = _child_text(adc, "compAcConv")
        if comp:
            adc_data["compAcConv"] = comp
        dt = _child_text(adc, "dtEfAcConv")
        if dt:
            adc_data["dtEfAcConv"] = dt
        remun_suc = _child_text(adc, "remunSuc")
        adc_data["remunSuc"] = remun_suc or "N"

        periodos = []
        for ip in _xdirect(adc, "idePeriodo"):
            periodo = {
                "perRef": _child_text(ip, "perRef") or "",
                "ideEstabLot": _extract_ide_estab_lot(ip, "remunPerAnt"),
            }
            periodos.append(periodo)
        adc_data["idePeriodo"] = periodos
        ide_adcs.append(adc_data)

    return {"ideADC": ide_adcs}


def extrair_s1200(inner_esocial) -> list[dict]:
    """
    Extrai dm_devs COMPLETO de um evento S-1200.
    Retorna no formato EXATO que S1200XMLGenerator.gerar() espera.
    """
    dm_devs = []
    for dm in _xall(inner_esocial, "dmDev"):
        dev = {
            "ideDmDev": _child_text(dm, "ideDmDev") or "",
            "codCateg": _child_text(dm, "codCateg") or "",
        }

        info_apur = _extract_info_per_apur(dm)
        if info_apur:
            dev["infoPerApur"] = info_apur

        info_ant = _extract_info_per_ant(dm)
        if info_ant:
            dev["infoPerAnt"] = info_ant

        dm_devs.append(dev)
    return dm_devs


# ── S-1210: Extrair info_pgtos completo ─────────────────────────────────────

def extrair_s1210(inner_esocial) -> list[dict]:
    """
    Extrai info_pgtos COMPLETO de um evento S-1210.
    Retorna no formato EXATO que S1210XMLGenerator.gerar() espera.
    """
    pgtos = []
    for info in _xall(inner_esocial, "infoPgto"):
        pgto = {
            "dtPgto": _child_text(info, "dtPgto") or "",
            "tpPgto": _child_text(info, "tpPgto") or "",
            "ideDmDev": _child_text(info, "ideDmDev") or "",
            "vrLiq": _child_text(info, "vrLiq") or "0",
        }
        per_ref = _child_text(info, "perRef")
        if per_ref:
            pgto["perRef"] = per_ref
        pgtos.append(pgto)
    return pgtos


def extrair_s1210_ir_complem(inner_esocial) -> Optional[dict]:
    """Extrai infoIRComplem de um evento S-1210, se existir."""
    irc = _xall(inner_esocial, "infoIRComplem")
    if not irc:
        return None

    info_ircrs = []
    for ircr in _xdirect(irc[0], "infoIRCR"):
        cr = {"tpCR": _child_text(ircr, "tpCR") or ""}
        vr_cr = _child_text(ircr, "vrCR")
        if vr_cr:
            cr["vrCR"] = vr_cr

        deps = []
        for dd in _xdirect(ircr, "dedDepen"):
            dep = {
                "tpRend": _child_text(dd, "tpRend") or "",
                "cpfDep": _child_text(dd, "cpfDep") or "",
                "vlrDedDep": _child_text(dd, "vlrDedDep") or "0",
            }
            deps.append(dep)
        if deps:
            cr["dedDepen"] = deps
        info_ircrs.append(cr)

    return {"infoIRCR": info_ircrs} if info_ircrs else None


# ── Extração de metadados comuns ────────────────────────────────────────────

def _extrair_metadados(inner_esocial, recibo_inner) -> dict:
    """Extrai CPF, per_apur, nr_recibo, id_evento do XML."""
    cpf = None
    for tag in ["cpfTrab", "cpfBenef"]:
        cpf = _xtext(inner_esocial, tag)
        if cpf:
            break

    nr_recibo = None
    if recibo_inner is not None:
        nr_recibo = _xtext(recibo_inner, "nrRecibo")

    id_evento = None
    for el in inner_esocial.iter():
        evt_id = el.get("Id")
        if evt_id:
            id_evento = evt_id
            break

    return {
        "cpf": cpf,
        "per_apur": _xtext(inner_esocial, "perApur"),
        "nr_recibo": nr_recibo,
        "id_evento": id_evento,
        "ind_retif": _xtext(inner_esocial, "indRetif"),
    }


# ── Parser principal ────────────────────────────────────────────────────────

def parse_xml_completo(filepath: str) -> tuple[Optional[dict], Optional[str]]:
    """
    Abre um XML do download eSocial e extrai payload COMPLETO.

    Para S-1200: retorna dm_devs no formato exato do S1200XMLGenerator.gerar()
    Para S-1210: retorna info_pgtos no formato exato do S1210XMLGenerator.gerar()

    Returns:
        (resultado_dict, None) em sucesso
        (None, mensagem_erro) em falha
    """
    filename = os.path.basename(filepath)
    tipo_evento = _detect_event_type(filename)
    if not tipo_evento:
        return None, f"Tipo evento não detectado: {filename}"

    if tipo_evento not in ("S-1200", "S-1210"):
        return None, f"Tipo {tipo_evento} não suportado — apenas S-1200/S-1210"

    try:
        tree = etree.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        return None, f"XML inválido: {filename}: {e}"

    inner_esocial, recibo_inner = _navigate_to_inner(root)
    if inner_esocial is None:
        return None, f"Estrutura não reconhecida: {filename}"

    meta = _extrair_metadados(inner_esocial, recibo_inner)

    resultado = {
        "tipo_evento": tipo_evento,
        "arquivo": filename,
        **meta,
    }

    if tipo_evento == "S-1200":
        resultado["dm_devs"] = extrair_s1200(inner_esocial)
    elif tipo_evento == "S-1210":
        resultado["info_pgtos"] = extrair_s1210(inner_esocial)
        resultado["info_ir_complem"] = extrair_s1210_ir_complem(inner_esocial)

    return resultado, None


# ── Parser de pasta inteira ─────────────────────────────────────────────────

def parse_pasta(
    pasta: str,
    tipos: list[str] = None,
    cpf_filtro: str = None,
) -> dict:
    """
    Varre pasta com XMLs do download eSocial e extrai payloads completos.

    Args:
        pasta: caminho da pasta com XMLs
        tipos: filtrar por tipos (ex: ["S-1200", "S-1210"]), None = todos
        cpf_filtro: filtrar por CPF específico (11 dígitos)

    Returns:
        dict com:
        - eventos: lista de resultados parseados
        - erros: lista de erros
        - resumo: contadores por tipo
    """
    if not os.path.isdir(pasta):
        return {"eventos": [], "erros": [f"Pasta não encontrada: {pasta}"], "resumo": {}}

    tipos_aceitos = set(tipos) if tipos else {"S-1200", "S-1210"}
    eventos = []
    erros = []
    resumo: dict[str, int] = {}

    for filename in os.listdir(pasta):
        if not filename.lower().endswith(".xml"):
            continue

        tipo = _detect_event_type(filename)
        if not tipo or tipo not in tipos_aceitos:
            continue

        filepath = os.path.join(pasta, filename)
        resultado, erro = parse_xml_completo(filepath)
        if erro:
            erros.append(erro)
            continue

        if cpf_filtro and resultado.get("cpf") != cpf_filtro:
            continue

        eventos.append(resultado)
        resumo[tipo] = resumo.get(tipo, 0) + 1

    return {"eventos": eventos, "erros": erros, "resumo": resumo}


# ── Construir input do pipeline a partir de XMLs ───────────────────────────

def construir_input_pipeline(
    pasta: str,
    cpf: str,
    per_apur: str,
) -> tuple[Optional[dict], Optional[str]]:
    """
    Busca na pasta os XMLs de S-1200 e S-1210 de um CPF/período específico
    e constrói o input completo para o pipeline de retificação.

    Returns:
        (pipeline_input_dict, None) em sucesso
        (None, mensagem_erro) em falha

    O dict retornado contém:
        - s1200_dm_devs: dm_devs do S-1200 original
        - s1200_nr_recibo: nr_recibo do S-1200 original
        - s1210_info_pgtos: info_pgtos do S-1210 original
        - s1210_nr_recibo: nr_recibo do S-1210 original
        - s1210_info_ir_complem: IR complement (se existir)
    """
    resultado = parse_pasta(pasta, tipos=["S-1200", "S-1210"], cpf_filtro=cpf)

    s1200_events = [
        e for e in resultado["eventos"]
        if e["tipo_evento"] == "S-1200" and e.get("per_apur") == per_apur
    ]
    s1210_events = [
        e for e in resultado["eventos"]
        if e["tipo_evento"] == "S-1210" and e.get("per_apur") == per_apur
    ]

    if not s1200_events:
        return None, f"S-1200 não encontrado para CPF {cpf} período {per_apur}"
    if not s1210_events:
        return None, f"S-1210 não encontrado para CPF {cpf} período {per_apur}"

    # Pegar o mais recente (último ind_retif ou maior nr_recibo)
    s1200 = sorted(
        s1200_events,
        key=lambda e: e.get("nr_recibo") or "",
        reverse=True,
    )[0]
    s1210 = sorted(
        s1210_events,
        key=lambda e: e.get("nr_recibo") or "",
        reverse=True,
    )[0]

    if not s1200.get("nr_recibo"):
        return None, f"S-1200 sem nr_recibo para CPF {cpf} período {per_apur}"
    if not s1210.get("nr_recibo"):
        return None, f"S-1210 sem nr_recibo para CPF {cpf} período {per_apur}"
    if not s1200.get("dm_devs"):
        return None, f"S-1200 sem dm_devs para CPF {cpf} período {per_apur}"
    if not s1210.get("info_pgtos"):
        return None, f"S-1210 sem info_pgtos para CPF {cpf} período {per_apur}"

    return {
        "s1200_dm_devs": s1200["dm_devs"],
        "s1200_nr_recibo": s1200["nr_recibo"],
        "s1210_info_pgtos": s1210["info_pgtos"],
        "s1210_nr_recibo": s1210["nr_recibo"],
        "s1210_info_ir_complem": s1210.get("info_ir_complem"),
    }, None
