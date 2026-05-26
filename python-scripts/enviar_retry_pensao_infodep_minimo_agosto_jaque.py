from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

import enviar_correcao_agosto_jaque as envio_base  # noqa: E402
from app import db, esocial_client  # noqa: E402
from app.xml_s1210 import NS, _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_JAQUE"
PREFLIGHT = OUT_DIR / "preflight_correcao_agosto_jaque.json"
RETRY_DIR = OUT_DIR / "xml_retry_pensao_infodep_minimo"


def _q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def _novo_xml_infodep(xml_bytes: bytes) -> tuple[bytes, str, list[str]]:
    root = etree.fromstring(xml_bytes)
    evt = root.xpath('//*[local-name()="evtPgtos"]')
    if not evt:
        raise RuntimeError("evtPgtos nao encontrado")
    evt = evt[0]
    tp_insc = int(root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])') or "1")
    nr_insc = root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])')
    new_id = _gerar_id(tp_insc, nr_insc)
    evt.set("Id", new_id)

    info_ir = root.xpath('//*[local-name()="infoIRComplem"]')
    if not info_ir:
        raise RuntimeError("infoIRComplem nao encontrado")
    info_ir = info_ir[0]

    cpf_deps: list[str] = []
    for pen in root.xpath('//*[local-name()="penAlim"]'):
        cpf = pen.xpath('string(./*[local-name()="cpfDep"])')
        if not cpf or cpf == "00000000000":
            raise RuntimeError(f"cpfDep invalido em penAlim: {cpf!r}")
        cpf_deps.append(cpf)
    if not cpf_deps:
        raise RuntimeError("penAlim nao encontrado")

    for existing in info_ir.xpath('./*[local-name()="infoDep"]'):
        info_ir.remove(existing)
    first_ircr = info_ir.xpath('./*[local-name()="infoIRCR"]')
    insert_index = info_ir.index(first_ircr[0]) if first_ircr else len(info_ir)
    for offset, cpf in enumerate(dict.fromkeys(cpf_deps)):
        info_dep = etree.Element(_q("infoDep"))
        cpf_node = etree.SubElement(info_dep, _q("cpfDep"))
        cpf_node.text = cpf
        info_ir.insert(insert_index + offset, info_dep)

    if root.xpath('//*[local-name()="dedDepen"]/*[local-name()="cpfDep" and text()="00000000000"]'):
        raise RuntimeError("Abortado: cpf zero apareceu em dedDepen")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8"), new_id, cpf_deps


def _load_pensao_targets() -> list[dict[str, Any]]:
    summary = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    targets = [item for item in summary.get("generated", []) if item.get("generated") and item.get("has_pensao")]
    if len(targets) != 4:
        raise RuntimeError(f"esperado 4 targets de pensao; encontrado {len(targets)}")
    return sorted(targets, key=lambda item: item["cpf"])


def _preparar_assinados(targets: list[dict[str, Any]], senha: str) -> list[dict[str, Any]]:
    RETRY_DIR.mkdir(parents=True, exist_ok=True)
    pfx_data = envio_base.DEFAULT_CERT.read_bytes()
    signed: list[dict[str, Any]] = []
    for item in targets:
        unsigned, new_id, cpf_deps = _novo_xml_infodep(Path(item["xml"]).read_bytes())
        retry_path = RETRY_DIR / f"S1210_{envio_base.PER_APUR}_{item['cpf']}_penAlim_infoDep_unsigned.xml"
        retry_path.write_bytes(unsigned)
        xml_assinado = S1010XMLSigner.assinar(unsigned, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if signed_id != new_id:
            raise RuntimeError(f"Id assinado difere do XML para CPF {item['cpf']}")
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id, "xml_retry": str(retry_path), "infoDep_cpfs": cpf_deps})
    return signed


def rodar() -> dict[str, Any]:
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if not senha:
        raise RuntimeError("ESOCIAL_CERT_SENHA nao definida")
    signed = _preparar_assinados(_load_pensao_targets(), senha)
    conn_db = db.connect(empresa_id=envio_base.EMPRESA_ID)
    conn_w = db.connect(empresa_id=envio_base.EMPRESA_ID)
    try:
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = envio_base._criar_timeline_envio(conn_db, len(signed))
        print(f"=> retry pensao infoDep minimo: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        resultado = envio_base._processar_lote(
            signed,
            item_ids,
            cert_path=envio_base.DEFAULT_CERT,
            senha=senha,
            cnpj="09445502000109",
            conn_db=conn_db,
            conn_w=conn_w,
        )
        sucesso = int(resultado["sucesso"])
        erro = int(resultado["erro"])
        histograma = dict(resultado.get("histograma") or {})
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso,
            erro=erro,
            resumo_extra={
                "rotulo_retry": "pensao_infodep_minimo_sem_deddepen",
                "protocolo": resultado.get("protocolo"),
                "histograma_erros": histograma,
                "cpfs": [item["cpf"] for item in signed],
            },
        )
        print("\n=== RESUMO RETRY PENSAO INFODEP MINIMO ===")
        print(f"envio_id  : {envio_id}")
        print(f"protocolo : {resultado.get('protocolo')}")
        print(f"sucesso   : {sucesso}")
        print(f"erro      : {erro}")
        print(f"histograma: {histograma}")
        return {"envio_id": envio_id, "sucesso": sucesso, "erro": erro, "histograma": histograma}
    finally:
        conn_db.close()
        conn_w.close()


if __name__ == "__main__":
    rodar()