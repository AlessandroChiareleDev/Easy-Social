from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
PYTHON_SCRIPTS = ROOT / "python-scripts"
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
sys.path.insert(0, str(PYTHON_SCRIPTS))
sys.path.insert(0, str(V2_BACKEND))

from app.envio_s1298 import _load_certificado  # noqa: E402
from esocial.esocial_client import ESocialClient  # noqa: E402
from esocial.soap_builder import SOAPEnvelopeBuilder  # noqa: E402

EMPRESA_ID = 3
CPF_PILOTO = "10477639828"
XML_PATH = (
    ROOT
    / "relatorio_ana"
    / "OBJETIVA_JAN_MAI_2025"
    / "xmls_janeiro_70_corrigidos"
    / "01_plano_saude_retificacao"
    / f"S1210_2025-01_{CPF_PILOTO}_plano_saude_retificacao_assinado.xml"
)
OUT_DIR = (
    ROOT
    / "relatorio_ana"
    / "OBJETIVA_JAN_MAI_2025"
    / "xmls_janeiro_70_corrigidos"
    / "retorno_envio_piloto"
    / CPF_PILOTO
)
RESULT_PATH = OUT_DIR / "resultado_envio_piloto.json"


def xpath_text(root: etree._Element, name: str) -> str:
    return root.xpath(f'string(//*[local-name()="{name}"])')


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["ESOCIAL_DUMP_XML_DIR"] = str(OUT_DIR / "xml_bruto")

    xml_assinado = XML_PATH.read_bytes()
    root = etree.fromstring(xml_assinado)
    cpf_xml = xpath_text(root, "cpfBenef")
    if cpf_xml != CPF_PILOTO:
        raise RuntimeError(f"XML piloto errado: esperado {CPF_PILOTO}, achou {cpf_xml}")

    assinatura_count = len(root.xpath('//*[local-name()="Signature"]'))
    if assinatura_count != 1:
        raise RuntimeError(f"XML piloto sem assinatura unica: Signature={assinatura_count}")

    cert = _load_certificado(EMPRESA_ID, None)
    pfx_data = Path(cert["cert_path"]).read_bytes()
    empregador = {"tpInsc": 1, "nrInsc": cert["cnpj"]}

    soap = SOAPEnvelopeBuilder.montar_envio([xml_assinado], empregador, empregador.copy(), grupo="3")
    envio = ESocialClient.enviar_lote(
        soap,
        pfx_data,
        cert["senha"],
        url=SOAPEnvelopeBuilder.url_envio(producao=True),
    )

    resultado = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "empresa": "OBJETIVA",
        "empresa_id": EMPRESA_ID,
        "cpf": CPF_PILOTO,
        "xml_path": str(XML_PATH.relative_to(ROOT)).replace("\\", "/"),
        "ambiente": "producao",
        "grupo": "3",
        "precheck_xml": {
            "cpfBenef": cpf_xml,
            "indRetif": xpath_text(root, "indRetif"),
            "nrRecibo": xpath_text(root, "nrRecibo"),
            "dtPgto": [node.text for node in root.xpath('//*[local-name()="dtPgto"]')],
            "planSaude_count": len(root.xpath('//*[local-name()="planSaude"]')),
            "signature_count": assinatura_count,
        },
        "envio": envio,
        "consultas": [],
        "resultado_final": None,
    }

    protocolo = envio.get("protocolo")
    if envio.get("sucesso") and protocolo:
        for attempt in range(1, 16):
            time.sleep(5)
            consulta = ESocialClient.consultar_lote(
                protocolo,
                pfx_data,
                cert["senha"],
                url=SOAPEnvelopeBuilder.url_consulta(producao=True),
            )
            consulta_sem_xml = {key: value for key, value in consulta.items() if key != "xml_resposta"}
            consulta_sem_xml["tentativa"] = attempt
            resultado["consultas"].append(consulta_sem_xml)

            eventos = consulta.get("eventos") or []
            if eventos:
                evento = eventos[0]
                resultado["resultado_final"] = {
                    "processado": True,
                    "codigo_resposta": evento.get("codigo_resposta"),
                    "descricao": evento.get("descricao"),
                    "nr_recibo": evento.get("nr_recibo"),
                    "ocorrencias": evento.get("ocorrencias") or [],
                }
                break
            if consulta.get("codigo_resposta") not in ("101", None):
                resultado["resultado_final"] = {
                    "processado": False,
                    "codigo_resposta": consulta.get("codigo_resposta"),
                    "descricao": consulta.get("descricao"),
                    "ocorrencias": [],
                }
                break

        if resultado["resultado_final"] is None:
            resultado["resultado_final"] = {
                "processado": False,
                "codigo_resposta": "101",
                "descricao": "Lote ainda em processamento apos 15 consultas",
                "ocorrencias": [],
            }
    else:
        resultado["resultado_final"] = {
            "processado": False,
            "codigo_resposta": envio.get("codigo_resposta"),
            "descricao": envio.get("descricao") or envio.get("erro"),
            "ocorrencias": envio.get("ocorrencias") or [],
        }

    RESULT_PATH.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()