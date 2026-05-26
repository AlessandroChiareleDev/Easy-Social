import hashlib
import json
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN"
REPORT_PATH = BASE_DIR / "resolvedor_quinzenais_dtpgto_agosto_202_deddepen.json"
OUT_DIR = BASE_DIR / "xml_reenvio_original_agosto_202_from_zip"
EVENT_DIR = BASE_DIR / "xml_reenvio_original_agosto_202_evento_assinado_from_zip"
MANIFEST_PATH = BASE_DIR / "manifest_reenvio_original_agosto_202.json"
ZIP_DIR = Path.home() / "Downloads" / "todos os meses 2025 SOLUCOES"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_output_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in OUT_DIR.glob("*_S1210_2025-08_*_original_202.xml"):
        file_path.unlink()
    EVENT_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in EVENT_DIR.glob("*_S1210_2025-08_*_evento_assinado_original_202.xml"):
        file_path.unlink()


def extract_signed_event_bytes(download_xml: bytes) -> bytes:
    marker = b'<evento><eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtPgtos/'
    start_marker = download_xml.find(marker)
    if start_marker < 0:
        raise RuntimeError("evento S-1210 assinado nao encontrado no retorno de download")
    start = start_marker + len(b"<evento>")
    end_marker = b"</eSocial></evento><recibo>"
    end = download_xml.find(end_marker, start)
    if end < 0:
        raise RuntimeError("fim do evento S-1210 assinado nao encontrado no retorno de download")
    return download_xml[start:end + len(b"</eSocial>")]


def has_event(record: dict, key: str) -> bool:
    event = record.get(key)
    return isinstance(event, dict) and bool(event.get("zip")) and bool(event.get("entry"))


def real_cpfs(record: dict, prefix: str) -> list[str]:
    cpfs: set[str] = set()
    for group in record.get("grupos") or []:
        for cpf in group.get(f"{prefix}_cpfs", []) or []:
            if cpf and cpf != "00000000000":
                cpfs.add(cpf)
    return sorted(cpfs)


def context_counts(records: list[dict]) -> dict:
    counts: Counter[str] = Counter()
    missing_adjacent: list[str] = []
    for record in records:
        target = record.get("target") or {}
        if target.get("cdResposta") == "202":
            counts["target_cdResposta_202"] += 1
        if target.get("zip") and target.get("entry"):
            counts["target_original_xml_local"] += 1

        julho = has_event(record, "julho")
        setembro = has_event(record, "setembro")
        if julho:
            counts["julho_event"] += 1
        if setembro:
            counts["setembro_event"] += 1
        if julho or setembro:
            counts["any_adjacent_event"] += 1
        if julho and setembro:
            counts["both_adjacent_events"] += 1
        else:
            missing_adjacent.append(record["cpf"])

        adjacent_real = bool(real_cpfs(record, "julho") or real_cpfs(record, "setembro"))
        if adjacent_real:
            counts["adjacent_real_cpfs"] += 1
        elif julho or setembro:
            counts["adjacent_only_zero_or_no_real_cpfs"] += 1

        if real_cpfs(record, "target"):
            counts["target_original_real_cpfs"] += 1

        counts[f"resolver_status_{record.get('status')}"] += 1

    return {"counts": dict(counts), "missing_adjacent_cpfs": missing_adjacent}


def extract_originals() -> dict:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    records = report["records"]
    clean_output_dir()

    targets: list[dict] = []
    failures: list[dict] = []
    for sequence, record in enumerate(records, start=1):
        cpf = record["cpf"]
        target = record.get("target") or {}
        zip_name = target.get("zip")
        entry_name = target.get("entry")
        if not zip_name or not entry_name:
            failures.append({"cpf": cpf, "erro": "target_sem_zip_ou_entry"})
            continue

        zip_path = ZIP_DIR / zip_name
        output_path = OUT_DIR / f"{sequence:03d}_S1210_2025-08_{cpf}_original_202.xml"
        event_output_path = EVENT_DIR / f"{sequence:03d}_S1210_2025-08_{cpf}_evento_assinado_original_202.xml"
        try:
            with zipfile.ZipFile(zip_path) as archive:
                download_xml = archive.read(entry_name)
            output_path.write_bytes(download_xml)
            signed_event_xml = extract_signed_event_bytes(download_xml)
            event_output_path.write_bytes(signed_event_xml)
            source_digest = sha256_bytes(download_xml)
        except Exception as exc:
            failures.append({"cpf": cpf, "zip": str(zip_path), "entry": entry_name, "erro": f"{type(exc).__name__}: {exc}"})
            continue

        output_digest = sha256_bytes(output_path.read_bytes())
        signed_event_digest = sha256_bytes(event_output_path.read_bytes())
        targets.append({
            "cpf": cpf,
            "xml": str(output_path),
            "evento_assinado_xml": str(event_output_path),
            "sha256": output_digest,
            "evento_assinado_sha256": signed_event_digest,
            "byte_identical_to_zip_entry": output_digest == source_digest,
            "evento_assinado_extraido_literalmente_do_zip": signed_event_xml in download_xml,
            "source_zip": str(zip_path),
            "source_entry": entry_name,
            "source_event_id": target.get("id_evento"),
            "source_indRetif": target.get("indRetif"),
            "source_nrRecibo": target.get("nrRecibo"),
            "source_cdResposta": target.get("cdResposta"),
            "source_protocolo": target.get("protocolo"),
            "source_dhProcessamento": target.get("dhProcessamento"),
            "dtPgtos": target.get("dtPgtos") or [],
            "perRefs": target.get("perRefs") or [],
            "status_resolvedor": record.get("status"),
            "julho_event": has_event(record, "julho"),
            "setembro_event": has_event(record, "setembro"),
            "julho_real_cpfs": real_cpfs(record, "julho"),
            "setembro_real_cpfs": real_cpfs(record, "setembro"),
            "target_real_cpfs": real_cpfs(record, "target"),
            "observacao": "XML original extraido do ZIP local sem alteracao de conteudo; envio exige autorizacao explicita.",
        })

    context = context_counts(records)
    manifest = {
        "empresa_id": report.get("empresa_id"),
        "per_apur": report.get("per_apur"),
        "dtPgto_target": report.get("dtPgto_target"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sem_consulta_esocial": True,
        "sem_alteracao_xml": True,
        "fonte_relatorio": str(REPORT_PATH),
        "xml_dir": str(OUT_DIR),
        "evento_assinado_xml_dir": str(EVENT_DIR),
        "total_alvos_202": len(records),
        "total_xmls_originais_extraidos": len(targets),
        "total_eventos_assinados_extraidos": len(targets),
        "total_falhas": len(failures),
        "total_hashes_identicos": sum(1 for item in targets if item["byte_identical_to_zip_entry"]),
        "total_eventos_assinados_literalmente_extraidos": sum(1 for item in targets if item["evento_assinado_extraido_literalmente_do_zip"]),
        "contexto_contagens": context["counts"],
        "cpfs_sem_ambos_meses_adjacentes": context["missing_adjacent_cpfs"],
        "failures": failures,
        "targets": targets,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    manifest = extract_originals()
    print("PREPARAR_REENVIO_ORIGINAL_AGOSTO_202_SOLUCOES_OK")
    print(json.dumps({
        "total_alvos_202": manifest["total_alvos_202"],
        "total_xmls_originais_extraidos": manifest["total_xmls_originais_extraidos"],
        "total_eventos_assinados_extraidos": manifest["total_eventos_assinados_extraidos"],
        "total_hashes_identicos": manifest["total_hashes_identicos"],
        "total_eventos_assinados_literalmente_extraidos": manifest["total_eventos_assinados_literalmente_extraidos"],
        "total_falhas": manifest["total_falhas"],
        "contexto_contagens": manifest["contexto_contagens"],
        "cpfs_sem_ambos_meses_adjacentes": manifest["cpfs_sem_ambos_meses_adjacentes"],
        "manifest": str(MANIFEST_PATH),
        "xml_dir": str(OUT_DIR),
        "evento_assinado_xml_dir": str(EVENT_DIR),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()