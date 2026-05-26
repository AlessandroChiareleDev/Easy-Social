from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
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

import corrigir_mes_respostas_jaque_plano_pensao as correcao_base  # noqa: E402
import operacao_20_05_solucoes as op  # noqa: E402
from app import db  # noqa: E402
from app.xml_diff import eventos_iguais  # noqa: E402
from app.xml_extractor import extrair_s1210  # noqa: E402
from app.xml_s1210 import S1210XMLGenerator  # noqa: E402


PER_APUR = "2025-04"
CONFIRM_TOKEN = "ABRIL_ORIGINAL_459"
OUT_DIR = op.OUT_BASE / "S1210_CORRECOES" / PER_APUR / "fallback_original_459"
XML_DIR = OUT_DIR / "xml_unsigned"
MANIFEST = OUT_DIR / "manifest_abril_original_459.json"


def load_plan_map() -> dict[str, list[dict[str, str]]]:
    parsed = op.parse_workbooks()
    plan_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in parsed[PER_APUR]["plano"]:
        plan_map[item["cpf"]].append(
            {
                "cnpjOper": item["cnpj_operadora"],
                "regANS": item["registro_ans"],
                "vlrSaudeTit": item["valor_titular"],
            }
        )
    return dict(plan_map)


def current_459_cpfs() -> list[str]:
    rows = op.audit_counts([PER_APUR])[PER_APUR]["rows"]
    return sorted(
        row["cpf"]
        for row in rows
        if row.get("erro_codigo") == "401" and "459" in str(row.get("erro_mensagem") or "")
    )


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in manifest.get("targets") or []:
        if not item.get("generated"):
            continue
        root = etree.fromstring(Path(item["xml"]).read_bytes())
        rows.append(
            {
                "cpf": item["cpf"],
                "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "planSaude": len(root.xpath('//*[local-name()="planSaude"]')),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [row for row in rows if row["indRetif"] != "1" or row["nrRecibo"] or row["perApur"] != PER_APUR or row["signature"] or row["planSaude"] < 1]
    return {"total": len(rows), "wrong": wrong, "sample": rows[:10]}


def generate_manifest() -> dict[str, Any]:
    op.configure_base()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    XML_DIR.mkdir(parents=True, exist_ok=True)
    for old_xml in XML_DIR.glob("*.xml"):
        old_xml.unlink()
    cpfs = current_459_cpfs()
    plan_map = load_plan_map()
    rows = correcao_base.load_current_rows(PER_APUR, cpfs)
    targets = []
    conn = db.connect(empresa_id=op.EMPRESA_ID)
    try:
        for seq, cpf in enumerate(cpfs, start=1):
            record: dict[str, Any] = {"cpf": cpf, "generated": False, "fallback": "original_sem_nrRecibo"}
            row = rows.get(cpf)
            if not row:
                record["reason"] = "sem XML fonte local"
                targets.append(record)
                continue
            if cpf not in plan_map:
                record["reason"] = "sem resposta de plano no XLSX"
                targets.append(record)
                continue
            try:
                xml_old = correcao_base.read_xml_event(conn, row)
                campos = extrair_s1210(xml_old)
                xml_new = S1210XMLGenerator.gerar(
                    empregador=campos["empregador"],
                    beneficiario=campos["beneficiario"],
                    info_pgtos=campos["info_pgtos"],
                    per_apur=PER_APUR,
                    ind_retif="1",
                    nr_recibo=None,
                    info_ir_complem=campos.get("info_ir_complem"),
                    plan_saude=plan_map[cpf],
                    seq=seq,
                    tp_amb=correcao_base.TP_AMB,
                )
                if eventos_iguais(xml_old, xml_new):
                    record["reason"] = "XML original novo ficou identico ao fonte"
                    targets.append(record)
                    continue
                out_xml = XML_DIR / f"S1210_{PER_APUR}_{cpf}_original_plansaude_unsigned.xml"
                out_xml.write_bytes(xml_new)
                record.update(
                    {
                        "generated": True,
                        "xml": str(out_xml),
                        "evento_id": row.get("id"),
                        "nr_recibo": None,
                        "status": row.get("item_status"),
                        "erro_codigo": row.get("erro_codigo"),
                        "erro_mensagem": row.get("erro_mensagem"),
                        "has_plano": True,
                        "has_pensao": False,
                    }
                )
                targets.append(record)
            except Exception as exc:
                record["reason"] = f"{type(exc).__name__}: {exc}"
                targets.append(record)
    finally:
        conn.close()
    manifest = {
        "empresa_id": op.EMPRESA_ID,
        "per_apur": PER_APUR,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "regra": "fallback para 401/459: enviar S-1210 original com planSaude, sem nrRecibo",
        "out_dir": str(OUT_DIR),
        "target_cpfs": len(cpfs),
        "xmls_generated": sum(1 for item in targets if item.get("generated")),
        "blocked_count": sum(1 for item in targets if not item.get("generated")),
        "xml_type_counts": {"plano_original_459": sum(1 for item in targets if item.get("generated"))},
        "targets": targets,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    with (OUT_DIR / "preflight_abril_original_459.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["cpf", "generated", "reason", "xml"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(targets)
    return manifest


def execute() -> dict[str, Any]:
    manifest = generate_manifest()
    validation = validate_manifest(manifest)
    if validation["wrong"]:
        raise RuntimeError(f"validacao falhou: {validation['wrong'][:5]}")
    result = op.execute_s1210_manifest(manifest, MANIFEST)
    after = op.audit_counts([PER_APUR])[PER_APUR]
    closing = None
    if after["erros"] == 0:
        closing = op.close_month(PER_APUR, True)
    output = {"manifest": str(MANIFEST), "validation": validation, "execute": result, "after": after, "closing": closing}
    (OUT_DIR / "resultado_abril_original_459.json").write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()
    if not args.execute:
        manifest = generate_manifest()
        print(json.dumps({"manifest": manifest, "validation": validate_manifest(manifest)}, ensure_ascii=False, indent=2, default=str))
        return 0
    if args.confirmar != CONFIRM_TOKEN:
        raise SystemExit(f"Para executar, use --confirmar {CONFIRM_TOKEN}")
    print(json.dumps(execute(), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())