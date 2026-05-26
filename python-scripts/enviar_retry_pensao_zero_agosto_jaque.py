from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import psycopg2.extras
from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(ROOT / "python-scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "python-scripts"))
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

import enviar_correcao_agosto_jaque as envio_base  # noqa: E402
from app import db, esocial_client  # noqa: E402
from app.xml_s1210 import _gerar_id  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_JAQUE"
PREFLIGHT = OUT_DIR / "preflight_correcao_agosto_jaque.json"
RETRY_DIR = OUT_DIR / "xml_retry_pensao_cpf_zero"
CPF_ZERO = "00000000000"


def _child_text(node, name: str) -> str:
    values = node.xpath(f'./*[local-name()="{name}"]/text()')
    return values[0] if values else ""


def _novo_xml_cpf_zero(xml_bytes: bytes) -> tuple[bytes, str]:
    root = etree.fromstring(xml_bytes)
    evt = root.xpath('//*[local-name()="evtPgtos"]')
    if not evt:
        raise RuntimeError("evtPgtos nao encontrado")
    evt = evt[0]
    tp_insc = int(root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="tpInsc"])') or "1")
    nr_insc = root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])')
    new_id = _gerar_id(tp_insc, nr_insc)
    evt.set("Id", new_id)
    pensoes = root.xpath('//*[local-name()="penAlim"]')
    if not pensoes:
        raise RuntimeError("penAlim nao encontrado")
    for pen in pensoes:
        cpf_nodes = pen.xpath('./*[local-name()="cpfDep"]')
        if not cpf_nodes:
            raise RuntimeError("penAlim sem cpfDep")
        cpf_nodes[0].text = CPF_ZERO
    if root.xpath('//*[local-name()="dedDepen"]/*[local-name()="cpfDep" and text()="00000000000"]'):
        raise RuntimeError("Abortado: cpf zero apareceu em dedDepen")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8"), new_id


def _load_pensao_targets() -> list[dict[str, Any]]:
    summary = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    targets = [item for item in summary.get("generated", []) if item.get("generated") and item.get("has_pensao")]
    if len(targets) != 4:
        raise RuntimeError(f"esperado 4 targets de pensao; encontrado {len(targets)}")
    return sorted(targets, key=lambda item: item["cpf"])


def _preparar_assinados(targets: list[dict[str, Any]], cert_path: Path, senha: str) -> list[dict[str, Any]]:
    RETRY_DIR.mkdir(parents=True, exist_ok=True)
    pfx_data = cert_path.read_bytes()
    signed: list[dict[str, Any]] = []
    for item in targets:
        unsigned_zero, new_id = _novo_xml_cpf_zero(Path(item["xml"]).read_bytes())
        retry_path = RETRY_DIR / f"S1210_{envio_base.PER_APUR}_{item['cpf']}_penAlim_cpf_zero_unsigned.xml"
        retry_path.write_bytes(unsigned_zero)
        xml_assinado = S1010XMLSigner.assinar(unsigned_zero, pfx_data, senha)
        signed_id = esocial_client._extrair_id(xml_assinado)
        if signed_id != new_id:
            raise RuntimeError(f"Id assinado difere do XML para CPF {item['cpf']}")
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": signed_id, "xml_retry": str(retry_path)})
    return signed


def rodar() -> dict[str, Any]:
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if not senha:
        raise RuntimeError("ESOCIAL_CERT_SENHA nao definida")
    targets = _load_pensao_targets()
    cert_path = envio_base.DEFAULT_CERT
    signed = _preparar_assinados(targets, cert_path, senha)
    conn_db = db.connect(empresa_id=envio_base.EMPRESA_ID)
    conn_w = db.connect(empresa_id=envio_base.EMPRESA_ID)
    try:
        envio_base._verificar_estado_atual(conn_db, signed)
        envio_id, mes_id = envio_base._criar_timeline_envio(conn_db, len(signed))
        print(f"=> retry pensao cpf zero: envio_id={envio_id} timeline_mes={mes_id} targets={len(signed)}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        resultado = envio_base._processar_lote(
            signed,
            item_ids,
            cert_path=cert_path,
            senha=senha,
            cnpj="09445502000109",
            conn_db=conn_db,
            conn_w=conn_w,
        )
        histograma: dict[str, int] = dict(resultado.get("histograma") or {})
        sucesso = int(resultado["sucesso"])
        erro = int(resultado["erro"])
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso,
            erro=erro,
            resumo_extra={
                "rotulo_retry": "pensao_cpf_zero_sem_infodep_deddepen",
                "protocolo": resultado.get("protocolo"),
                "histograma_erros": histograma,
                "cpfs": [item["cpf"] for item in signed],
            },
        )
        print("\n=== RESUMO RETRY PENSAO CPF ZERO ===")
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