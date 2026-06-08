from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sys
import warnings
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import psycopg2.extras
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, pkcs12
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
V2_BACKEND = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
sys.path.insert(0, str(V2_BACKEND))

from app import db  # noqa: E402
from app.envio_s1298 import _load_certificado  # noqa: E402
from app.envio_teste_100 import _ler_xml_evento  # noqa: E402
from app.xml_extractor import extrair_s1210  # noqa: E402
from app.xml_s1210 import S1210XMLGenerator  # noqa: E402
from app.xml_signer import _patch_signxml_legacy_ec_names  # noqa: E402

_patch_signxml_legacy_ec_names()

from signxml import XMLSigner, methods  # noqa: E402

EMPRESA_ID = 3
ERRORS_CSV = ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "erros_s1210_objetiva_2025-01.csv"
OUT_DIR = ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "xmls_janeiro_70_corrigidos"
PLAN_DIR = OUT_DIR / "01_plano_saude_retificacao"
REC459_DIR = OUT_DIR / "02_recibo_459_inclusao"

RUBRICAS = {
    "516": {"operadora": "SB SAUDE", "cnpjOper": "28633372000174", "regANS": "421154"},
    "605": {"operadora": "SB SAUDE", "cnpjOper": "28633372000174", "regANS": "421154"},
    "775": {"operadora": "SB SAUDE", "cnpjOper": "28633372000174", "regANS": "421154"},
    "619": {"operadora": "NEW LEADER", "cnpjOper": "02127779000136", "regANS": "364592"},
    "774": {"operadora": "NEW LEADER", "cnpjOper": "02127779000136", "regANS": "364592"},
}


def norm_cpf(value: str) -> str:
    return re.sub(r"\D", "", str(value or "")).zfill(11)[-11:]


def fmt_money(value: float) -> str:
    return f"{float(value):.2f}"


def child_text(element: etree._Element, name: str) -> str:
    values = element.xpath(f'./*[local-name()="{name}"]/text()')
    return values[0] if values else ""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_s1200_rubricas(xml_bytes: bytes, needed_dm: set[str]) -> dict[str, list[dict]]:
    root = etree.fromstring(xml_bytes)
    found: dict[str, list[dict]] = {}
    for dm_dev in root.xpath('//*[local-name()="dmDev"]'):
        ide_dm_dev = child_text(dm_dev, "ideDmDev")
        if ide_dm_dev not in needed_dm or ide_dm_dev in found:
            continue

        rubricas = []
        for item in dm_dev.xpath('.//*[local-name()="itensRemun"]'):
            cod_rubr = child_text(item, "codRubr")
            if cod_rubr not in RUBRICAS:
                continue

            valor = float((child_text(item, "vrRubr") or "0").replace(",", "."))
            if abs(valor) < 0.0001:
                continue

            rubricas.append(
                {
                    "codRubr": cod_rubr,
                    "vrRubr": fmt_money(valor),
                    "ideTabRubr": child_text(item, "ideTabRubr"),
                    **RUBRICAS[cod_rubr],
                }
            )
        found[ide_dm_dev] = rubricas
    return found


def build_plan_saude(rubricas: list[dict]) -> list[dict]:
    totals: dict[tuple[str, str, str], float] = defaultdict(float)
    for rubrica in rubricas:
        key = (rubrica["operadora"], rubrica["cnpjOper"], rubrica["regANS"])
        totals[key] += float(rubrica["vrRubr"])

    return [
        {"cnpjOper": cnpj, "regANS": ans, "vlrSaudeTit": fmt_money(total)}
        for (_operadora, cnpj, ans), total in sorted(totals.items())
    ]


def make_signer():
    cert = _load_certificado(EMPRESA_ID, None)
    pfx_data = Path(cert["cert_path"]).read_bytes()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data,
            cert["senha"].encode(),
            backend=default_backend(),
        )
    if certificate is None:
        raise RuntimeError("Certificado A1 sem certificado publico")

    cert_pem = certificate.public_bytes(Encoding.PEM)
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )

    def sign_xml(xml_bytes: bytes) -> bytes:
        root = etree.fromstring(xml_bytes)
        evento = next((child for child in root if "evt" in child.tag.lower()), None)
        if evento is not None:
            event_id = evento.get("Id") or evento.get("id")
            if event_id and evento.get("id") and not evento.get("Id"):
                del evento.attrib["id"]
                evento.set("Id", event_id)
        signed_root = signer.sign(root, key=private_key, cert=cert_pem)
        return etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8")

    return sign_xml


def load_errors() -> tuple[list[dict], list[dict], list[dict]]:
    with ERRORS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        errors = list(csv.DictReader(handle, delimiter=";"))
    for error in errors:
        error["cpf_norm"] = norm_cpf(error["cpf"])

    plan_errors = [error for error in errors if error["categoria"] == "plano_saude_coletivo_obrigatorio"]
    rec459_errors = [error for error in errors if error["categoria"] != "plano_saude_coletivo_obrigatorio"]
    if len(errors) != 70 or len(plan_errors) != 69 or len(rec459_errors) != 1:
        raise RuntimeError(
            f"CSV inesperado: total={len(errors)} plano={len(plan_errors)} rec459={len(rec459_errors)}"
        )
    return errors, plan_errors, rec459_errors


def validate_manifest(manifest: list[dict]) -> None:
    if len(manifest) != 70:
        raise RuntimeError(f"Esperava 70 XMLs, gerou {len(manifest)}")
    if sum(1 for item in manifest if item["acao"].startswith("retificacao")) != 69:
        raise RuntimeError("Quantidade de retificacoes de plano diferente de 69")
    if sum(1 for item in manifest if item["acao"].startswith("inclusao")) != 1:
        raise RuntimeError("Quantidade de inclusoes 459 diferente de 1")
    if any(item["signature_count"] != 1 for item in manifest):
        raise RuntimeError("Algum XML nao tem exatamente uma assinatura")
    for item in manifest:
        if item["acao"].startswith("retificacao"):
            if item["indRetif"] != "2" or not item["nrRecibo_no_xml"] or not item["planSaude"]:
                raise RuntimeError(f"Retificacao invalida para {item['cpf']}")
        else:
            if item["indRetif"] != "1" or item["nrRecibo_no_xml"]:
                raise RuntimeError(f"Inclusao 459 invalida para {item['cpf']}")


def main() -> None:
    errors, plan_errors, rec459_errors = load_errors()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    PLAN_DIR.mkdir(parents=True, exist_ok=True)
    REC459_DIR.mkdir(parents=True, exist_ok=True)

    sign_xml = make_signer()
    manifest = []

    conn = db.connect(empresa_id=EMPRESA_ID)
    lo_conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            recibos = [error["nr_recibo_anterior"] for error in errors]
            cursor.execute(
                """
                SELECT ev.*, z.conteudo_oid, z.tamanho_bytes
                  FROM explorador_eventos ev
                  JOIN empresa_zips_brutos z ON z.id = ev.zip_id
                 WHERE ev.tipo_evento = 'S-1210'
                   AND ev.per_apur = '2025-01'
                   AND ev.nr_recibo = ANY(%s)
                """,
                (recibos,),
            )
            s1210_by_rec = {row["nr_recibo"]: row for row in cursor.fetchall()}
            missing = [error["nr_recibo_anterior"] for error in errors if error["nr_recibo_anterior"] not in s1210_by_rec]
            if missing:
                raise RuntimeError("S-1210 base ausente: " + ", ".join(missing[:10]))

            campos_by_rec = {}
            needed_dm_by_cpf: dict[str, set[str]] = {}
            for error in plan_errors:
                campos = extrair_s1210(_ler_xml_evento(lo_conn, s1210_by_rec[error["nr_recibo_anterior"]]))
                campos_by_rec[error["nr_recibo_anterior"]] = campos
                needed_dm_by_cpf[error["cpf_norm"]] = {
                    info["ideDmDev"] for info in campos["info_pgtos"] if info.get("ideDmDev")
                }

            plan_cpfs = [error["cpf_norm"] for error in plan_errors]
            cursor.execute(
                """
                SELECT ev.*, z.conteudo_oid, z.tamanho_bytes
                  FROM explorador_eventos ev
                  JOIN empresa_zips_brutos z ON z.id = ev.zip_id
                 WHERE ev.tipo_evento = 'S-1200'
                   AND ev.cpf = ANY(%s)
                   AND ev.per_apur = ANY(%s)
                 ORDER BY ev.cpf, ev.dt_processamento DESC NULLS LAST, ev.id DESC
                """,
                (plan_cpfs, ["2024-12", "2025-01"]),
            )
            s1200_by_cpf = defaultdict(list)
            for row in cursor.fetchall():
                s1200_by_cpf[row["cpf"]].append(row)

            for index, error in enumerate(plan_errors, start=1):
                cpf = error["cpf_norm"]
                campos = campos_by_rec[error["nr_recibo_anterior"]]
                needed_dm = needed_dm_by_cpf[cpf]
                rubricas_by_dm: dict[str, list[dict]] = {}
                s1200_sources = []

                for s1200 in s1200_by_cpf.get(cpf, []):
                    remaining = needed_dm - set(rubricas_by_dm.keys())
                    if not remaining:
                        break
                    parsed = parse_s1200_rubricas(_ler_xml_evento(lo_conn, s1200), remaining)
                    for ide_dm_dev, rubricas in parsed.items():
                        if ide_dm_dev not in rubricas_by_dm:
                            rubricas_by_dm[ide_dm_dev] = rubricas
                            s1200_sources.append(
                                {
                                    "ideDmDev": ide_dm_dev,
                                    "s1200_recibo": s1200["nr_recibo"],
                                    "s1200_evento_id": s1200["id_evento"],
                                    "s1200_per_apur": s1200["per_apur"],
                                }
                            )

                all_rubricas = []
                for ide_dm_dev in sorted(needed_dm):
                    all_rubricas.extend(rubricas_by_dm.get(ide_dm_dev, []))
                plan_saude = build_plan_saude(all_rubricas)
                if not plan_saude:
                    raise RuntimeError(f"CPF {cpf} sem rubrica de plano nos dmDev {sorted(needed_dm)}")

                unsigned = S1210XMLGenerator.gerar(
                    empregador=campos["empregador"],
                    beneficiario=campos["beneficiario"],
                    info_pgtos=campos["info_pgtos"],
                    per_apur=campos["per_apur"],
                    ind_retif="2",
                    nr_recibo=error["nr_recibo_anterior"],
                    info_ir_complem=campos["info_ir_complem"],
                    plan_saude=plan_saude,
                    seq=index,
                    tp_amb="1",
                )
                signed = sign_xml(unsigned)
                out_path = PLAN_DIR / f"S1210_2025-01_{cpf}_plano_saude_retificacao_assinado.xml"
                out_path.write_bytes(signed)

                root = etree.fromstring(signed)
                manifest.append(
                    {
                        "cpf": cpf,
                        "categoria": error["categoria"],
                        "acao": "retificacao_indRetif_2_com_planSaude",
                        "xml_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                        "nr_recibo_anterior": error["nr_recibo_anterior"],
                        "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                        "nrRecibo_no_xml": root.xpath('string(//*[local-name()="nrRecibo"])'),
                        "dtPgto": [node.text for node in root.xpath('//*[local-name()="dtPgto"]')],
                        "ideDmDev": [node.text for node in root.xpath('//*[local-name()="ideDmDev"]')],
                        "planSaude": plan_saude,
                        "rubricas_usadas": all_rubricas,
                        "s1200_sources": s1200_sources,
                        "signature_count": len(root.xpath('//*[local-name()="Signature"]')),
                        "sha256": sha256(signed),
                        "bytes": len(signed),
                    }
                )
                if index % 10 == 0 or index == len(plan_errors):
                    print(f"retificacoes_assinadas={index}/69", flush=True)

            rec459 = rec459_errors[0]
            cpf = rec459["cpf_norm"]
            campos = extrair_s1210(_ler_xml_evento(lo_conn, s1210_by_rec[rec459["nr_recibo_anterior"]]))
            unsigned = S1210XMLGenerator.gerar(
                empregador=campos["empregador"],
                beneficiario=campos["beneficiario"],
                info_pgtos=campos["info_pgtos"],
                per_apur=campos["per_apur"],
                ind_retif="1",
                nr_recibo=None,
                info_ir_complem=campos["info_ir_complem"],
                plan_saude=campos["plan_saude"],
                seq=100,
                tp_amb="1",
            )
            signed = sign_xml(unsigned)
            out_path = REC459_DIR / f"S1210_2025-01_{cpf}_recibo459_inclusao_assinado.xml"
            out_path.write_bytes(signed)
            root = etree.fromstring(signed)
            manifest.append(
                {
                    "cpf": cpf,
                    "categoria": rec459["categoria"],
                    "acao": "inclusao_indRetif_1_sem_nrRecibo_para_evitar_459",
                    "xml_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                    "nr_recibo_rejeitado_459": rec459["nr_recibo_anterior"],
                    "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                    "nrRecibo_no_xml": root.xpath('string(//*[local-name()="nrRecibo"])'),
                    "dtPgto": [node.text for node in root.xpath('//*[local-name()="dtPgto"]')],
                    "ideDmDev": [node.text for node in root.xpath('//*[local-name()="ideDmDev"]')],
                    "planSaude": [],
                    "signature_count": len(root.xpath('//*[local-name()="Signature"]')),
                    "sha256": sha256(signed),
                    "bytes": len(signed),
                }
            )
    finally:
        conn.close()
        lo_conn.close()

    validate_manifest(manifest)

    manifest_path = OUT_DIR / "manifest_70_xmls_corrigidos.json"
    payload = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "empresa": "OBJETIVA",
        "empresa_id": EMPRESA_ID,
        "per_apur_s1210": "2025-01",
        "total_erros_csv": len(errors),
        "total_xmls_gerados": len(manifest),
        "retificacoes_plano_saude": 69,
        "inclusoes_recibo_459": 1,
        "regra_valor": "rubricas 516/605/619/774/775 dos dmDev locais ligados ao S-1210; dtPgto preservado do S-1210 original",
        "sem_chamada_esocial": True,
        "items": manifest,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = OUT_DIR / "OBJETIVA_2025-01_70_XMLS_CORRIGIDOS_ASSINADOS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for path in sorted(PLAN_DIR.glob("*.xml")) + sorted(REC459_DIR.glob("*.xml")) + [manifest_path]:
            zip_file.write(path, path.relative_to(OUT_DIR))

    print("OK xmls", len(manifest))
    print("plan", payload["retificacoes_plano_saude"], "rec459", payload["inclusoes_recibo_459"])
    print("zip", zip_path)
    print("signatures", dict(Counter(item["signature_count"] for item in manifest)))
    print(
        "plan_entries",
        dict(Counter(len(item.get("planSaude") or []) for item in manifest if item["acao"].startswith("retificacao"))),
    )
    print("rubricas", dict(Counter(rub["codRubr"] for item in manifest for rub in item.get("rubricas_usadas", []))))
    for sample_cpf in ("10477639828", "32540823890", "00820996777"):
        sample = next(item for item in manifest if item["cpf"] == sample_cpf)
        print("sample", sample_cpf, json.dumps(sample, ensure_ascii=False)[:1200])


if __name__ == "__main__":
    main()