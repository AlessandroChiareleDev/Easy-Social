from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
from app import db, esocial_client, storage, tenant  # noqa: E402
from app.envio_teste_100 import _ler_xml_evento  # noqa: E402
from app.xml_diff import eventos_iguais  # noqa: E402
from app.xml_extractor import extrair_s1210  # noqa: E402
from app.xml_s1210 import S1210XMLGenerator  # noqa: E402
from app.xml_s1298 import S1298XMLGenerator  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
CNPJ = "09445502000109"
CNPJ_RAIZ = CNPJ[:8]
AMBIENTE = "producao"
TP_AMB = "1"
GRUPO = 3
CFG_LOTE_MAX = 40
POLL_TENTATIVAS = 12
POLL_INTERVALO_S = 8
LEGACY_CONFIRM_TOKEN = "CORRIGIR_FEVEREIRO_2025_JAQUE"

DEFAULT_CERT = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"
SENHA_TXT = Path(r"C:\Users\xandao\Downloads\Senha solucoes.txt")
AUDIT_DIR = ROOT / "relatorio_ana" / "AUDITORIA_RESPOSTAS_JAQUE_PLANO_PENSAO_2025"
VALID_RESPONSES_CSV = AUDIT_DIR / "respostas_validas_final.csv"
MISSING_CSV = AUDIT_DIR / "faltantes_final.csv"
OUT_BASE = ROOT / "relatorio_ana" / "CORRECAO_JAQUE_PLANO_PENSAO_2025"
LOCAL_ZIP_ROOTS = [
    Path.home() / "Downloads" / "todos os meses 2025 SOLUCOES",
    Path.home() / "Downloads",
]


def text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def ascii_fold(value: Any) -> str:
    raw = text(value).lower()
    return "".join(ch for ch in unicodedata.normalize("NFKD", raw) if not unicodedata.combining(ch))


def digits(value: Any) -> str:
    return re.sub(r"\D", "", text(value))


def cpf11(value: Any) -> str:
    only_digits = digits(value)
    return only_digits.zfill(11)[-11:] if only_digits else ""


def cnpj14(value: Any) -> str:
    only_digits = digits(value)
    return only_digits.zfill(14)[-14:] if only_digits else ""


def money(value: Any) -> Decimal:
    if value is None or text(value) == "":
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    if isinstance(value, int):
        return Decimal(value).quantize(Decimal("0.01"))
    if isinstance(value, float):
        return Decimal(str(value)).quantize(Decimal("0.01"))
    raw = text(value).replace("R$", "").replace(" ", "")
    raw = re.sub(r"[^0-9,.-]", "", raw)
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def money_str(value: Any) -> str:
    return f"{money(value):.2f}"


def normalize_tp_rend(value: Any) -> str:
    raw = ascii_fold(value)
    only_digits = digits(value)
    if only_digits in {"11", "12", "13", "14", "18"}:
        return only_digits
    if "mensal" in raw or raw in {"mes", "m"}:
        return "11"
    if "13" in raw or "decimo" in raw:
        return "12"
    return raw


def read_password() -> str:
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if senha.strip():
        return senha.strip()
    if SENHA_TXT.exists():
        senha = SENHA_TXT.read_text(encoding="utf-8", errors="ignore").strip()
    if not senha:
        raise RuntimeError(f"senha do certificado nao encontrada: {SENHA_TXT}")
    return senha


def month_dir(per_apur: str) -> Path:
    return OUT_BASE / per_apur


def xml_dir(per_apur: str) -> Path:
    return month_dir(per_apur) / "xml_unsigned"


def manifest_path(per_apur: str) -> Path:
    return month_dir(per_apur) / f"manifest_correcao_jaque_{per_apur}.json"


def confirm_token(per_apur: str) -> str:
    return f"CORRIGIR_{per_apur.replace('-', '_')}_JAQUE"


def load_respostas_validas(per_apur: str) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]], list[dict[str, Any]]]:
    plan_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    pensao_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    rows: list[dict[str, Any]] = []
    with VALID_RESPONSES_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if text(row.get("per_apur")) != per_apur:
                continue
            cpf = cpf11(row.get("cpf"))
            tipo = text(row.get("tipo")).upper()
            if not cpf or tipo not in {"PLANO", "PENSAO"}:
                continue
            data = json.loads(row.get("data_json") or "{}")
            if tipo == "PLANO":
                plan_map[cpf].append(
                    {
                        "cnpjOper": cnpj14(data.get("cnpj_operadora")),
                        "regANS": digits(data.get("registro_ans")),
                        "vlrSaudeTit": money_str(data.get("valor_titular")),
                    }
                )
            else:
                pensoes = []
                for item in data.get("beneficiarios") or []:
                    cpf_dep = cpf11(item.get("cpf_beneficiario"))
                    tp_rend = normalize_tp_rend(item.get("tipo_rendimento"))
                    valor = money_str(item.get("valor_deduzido"))
                    if cpf_dep and tp_rend:
                        pensoes.append({"tpRend": tp_rend, "cpfDep": cpf_dep, "vlrDedPenAlim": valor})
                if pensoes:
                    pensao_map[cpf].extend(pensoes)
            rows.append({**row, "cpf": cpf, "tipo": tipo, "data": data})
    return dict(plan_map), dict(pensao_map), rows


def load_missing(per_apur: str) -> list[dict[str, str]]:
    if not MISSING_CSV.exists():
        return []
    out: list[dict[str, str]] = []
    with MISSING_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if text(row.get("per_apur")) == per_apur:
                out.append({**row, "cpf": cpf11(row.get("cpf")), "tipo": text(row.get("tipo")).upper()})
    return out


def safe_rollback(conn) -> None:
    try:
        conn.rollback()
    except Exception:
        pass


def find_local_zip(zip_name: str | None) -> Path | None:
    if not zip_name:
        return None
    for root in LOCAL_ZIP_ROOTS:
        candidate = root / zip_name
        if candidate.exists():
            return candidate
    for root in LOCAL_ZIP_ROOTS:
        if not root.exists():
            continue
        for candidate in root.glob("*.zip"):
            if candidate.name == zip_name:
                return candidate
    return None


def read_xml_event(conn, row: dict[str, Any]) -> bytes:
    xml_bytes = row.get("xml_bytes")
    if xml_bytes is not None:
        return bytes(xml_bytes)

    entry = row.get("xml_entry_name")
    local_zip = find_local_zip(row.get("zip_nome"))
    if local_zip and entry:
        try:
            with zipfile.ZipFile(local_zip, mode="r") as zip_file:
                return zip_file.read(entry)
        except Exception:
            pass

    if row.get("xml_oid") is not None:
        try:
            return _ler_xml_evento(conn, row)
        except Exception:
            safe_rollback(conn)

    if entry and row.get("zip_conteudo_oid") and row.get("zip_tamanho_bytes"):
        try:
            reader = storage.LargeObjectReader(conn, int(row["zip_conteudo_oid"]), int(row["zip_tamanho_bytes"]))
            try:
                with zipfile.ZipFile(reader, mode="r") as zip_file:
                    return zip_file.read(entry)
            finally:
                try:
                    reader.close()
                except Exception:
                    pass
        except Exception:
            safe_rollback(conn)

    raise RuntimeError(f"XML indisponivel para cpf={row.get('cpf')} evento={row.get('id')}")


def load_current_rows(per_apur: str, cpfs: list[str]) -> dict[str, dict[str, Any]]:
    if not cpfs:
        return {}
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH scope AS (
                    SELECT DISTINCT ON (ev.cpf)
                           ev.id, ev.cpf, ev.nr_recibo, ev.id_evento,
                           ev.xml_oid, ev.xml_bytes, ev.xml_size_bytes,
                           ev.xml_entry_name, ev.zip_id,
                           z.conteudo_oid AS zip_conteudo_oid,
                           z.tamanho_bytes AS zip_tamanho_bytes,
                           z.nome_arquivo_original AS zip_nome,
                           ev.dt_processamento
                      FROM explorador_eventos ev
                      JOIN empresa_zips_brutos z ON z.id = ev.zip_id
                     WHERE z.empresa_id = %s
                       AND ev.tipo_evento = 'S-1210'
                       AND ev.per_apur = %s
                       AND ev.retificado_por_id IS NULL
                       AND ev.cpf = ANY(%s)
                       AND (ev.xml_oid IS NOT NULL OR ev.xml_bytes IS NOT NULL)
                     ORDER BY ev.cpf ASC, ev.dt_processamento DESC NULLS LAST, ev.id DESC
                ), latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.nr_recibo_anterior, it.nr_recibo_novo,
                           it.criado_em, it.id AS item_id, te.id AS envio_id
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf = ANY(%s)
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT scope.*, latest.status AS item_status, latest.erro_codigo,
                       latest.erro_mensagem, latest.nr_recibo_anterior,
                       latest.nr_recibo_novo, latest.criado_em AS ultimo_item_em,
                       latest.item_id, latest.envio_id
                  FROM scope
                  LEFT JOIN latest ON latest.cpf = scope.cpf
                 ORDER BY scope.cpf
                """,
                (internal_empresa_id, per_apur, cpfs, internal_empresa_id, per_apur, cpfs),
            )
            return {cpf11(row["cpf"]): dict(row) for row in cursor.fetchall()}
    finally:
        conn.close()


def count_ir(info_ir: dict | None) -> dict[str, int]:
    out = {"infoIRCR": 0, "dedDepen": 0, "penAlim": 0}
    if not info_ir:
        return out
    for item in info_ir.get("infoIRCR") or []:
        out["infoIRCR"] += 1
        out["dedDepen"] += len(item.get("dedDepen") or [])
        out["penAlim"] += len(item.get("penAlim") or [])
    return out


def merge_pensao(info_ir: dict | None, pensoes: list[dict[str, str]]) -> tuple[dict | None, str | None]:
    if not pensoes:
        return info_ir, None
    if not info_ir or not info_ir.get("infoIRCR"):
        return None, "Sem infoIRCR no S-1210 atual; nao ha tpCR para inserir penAlim com seguranca"
    out = json.loads(json.dumps(info_ir, ensure_ascii=False))
    irs = out.get("infoIRCR") or []
    if len(irs) != 1:
        return None, f"S-1210 tem {len(irs)} infoIRCR; precisa decisao manual de qual tpCR recebe penAlim"
    irs[0]["penAlim"] = pensoes
    return out, None


def generate_manifest(per_apur: str) -> dict[str, Any]:
    out_dir = month_dir(per_apur)
    unsigned_dir = xml_dir(per_apur)
    out_dir.mkdir(parents=True, exist_ok=True)
    unsigned_dir.mkdir(parents=True, exist_ok=True)
    for old_xml in unsigned_dir.glob("*.xml"):
        old_xml.unlink()

    plan_map, pensao_map, response_rows = load_respostas_validas(per_apur)
    missing = load_missing(per_apur)
    target_cpfs = sorted(set(plan_map) | set(pensao_map))
    current_rows = load_current_rows(per_apur, target_cpfs)

    generated: list[dict[str, Any]] = []
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        for seq, cpf in enumerate(target_cpfs, start=1):
            row = current_rows.get(cpf)
            record: dict[str, Any] = {
                "cpf": cpf,
                "has_plano": cpf in plan_map,
                "has_pensao": cpf in pensao_map,
                "generated": False,
                "xml": "",
                "plan_entries": len(plan_map.get(cpf, [])),
                "pensao_entries": len(pensao_map.get(cpf, [])),
            }
            if not row:
                record["reason"] = "CPF sem evento S-1210 ativo local com XML"
                generated.append(record)
                continue
            record.update(
                {
                    "evento_id": row.get("id"),
                    "item_id": row.get("item_id"),
                    "envio_id": row.get("envio_id"),
                    "codigo": row.get("erro_codigo"),
                    "status": row.get("item_status"),
                    "erro_mensagem": row.get("erro_mensagem"),
                }
            )
            if row.get("item_status") == "sucesso":
                record["reason"] = "Ultimo status local ja e sucesso"
                generated.append(record)
                continue
            if str(row.get("erro_codigo") or "") == "202":
                record["reason"] = "Ultimo retorno e 202/aviso; nao e erro real a corrigir aqui"
                generated.append(record)
                continue
            try:
                xml_old = read_xml_event(conn, row)
                campos = extrair_s1210(xml_old)
                if campos.get("per_apur") != per_apur:
                    raise RuntimeError(f"perApur do XML divergente: {campos.get('per_apur')}")
                if cpf11(campos.get("beneficiario", {}).get("cpfBenef")) != cpf:
                    raise RuntimeError("cpfBenef do XML diverge do alvo")

                info_ir = campos.get("info_ir_complem")
                info_ir_before = count_ir(info_ir)
                if cpf in pensao_map:
                    info_ir, warning = merge_pensao(info_ir, pensao_map[cpf])
                    if warning:
                        record["reason"] = warning
                        generated.append(record)
                        continue
                plan_saude = plan_map.get(cpf) if cpf in plan_map else campos.get("plan_saude")
                nr_recibo = row.get("nr_recibo") or campos.get("nr_recibo_atual")
                if not nr_recibo:
                    record["reason"] = "Sem nrRecibo ativo para retificar"
                    generated.append(record)
                    continue
                xml_new = S1210XMLGenerator.gerar(
                    empregador=campos["empregador"],
                    beneficiario=campos["beneficiario"],
                    info_pgtos=campos["info_pgtos"],
                    per_apur=per_apur,
                    ind_retif="2",
                    nr_recibo=nr_recibo,
                    info_ir_complem=info_ir,
                    plan_saude=plan_saude,
                    seq=seq,
                    tp_amb=TP_AMB,
                )
                if eventos_iguais(xml_old, xml_new):
                    record["reason"] = "XML novo ficou identico ao atual"
                    generated.append(record)
                    continue
                out_xml = unsigned_dir / f"S1210_{per_apur}_{cpf}_jaque_unsigned.xml"
                out_xml.write_bytes(xml_new)
                record.update(
                    {
                        "generated": True,
                        "xml": str(out_xml),
                        "reason": "OK",
                        "nr_recibo": nr_recibo,
                        "info_pgtos": len(campos.get("info_pgtos") or []),
                        "ir_before": info_ir_before,
                        "ir_after": count_ir(info_ir),
                    }
                )
                generated.append(record)
            except Exception as exc:
                record["reason"] = f"{type(exc).__name__}: {exc}"
                generated.append(record)
    finally:
        conn.close()

    generated_ok = [item for item in generated if item.get("generated")]
    blocked = [item for item in generated if not item.get("generated")]
    type_counts = Counter(row["tipo"] for row in response_rows)
    xml_type_counts = {
        "plano": sum(1 for item in generated_ok if item.get("has_plano")),
        "pensao": sum(1 for item in generated_ok if item.get("has_pensao")),
    }
    manifest = {
        "empresa_id": EMPRESA_ID,
        "per_apur": per_apur,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "respostas_validas_csv": str(VALID_RESPONSES_CSV),
        "faltantes_csv": str(MISSING_CSV),
        "out_dir": str(out_dir),
        "response_rows": len(response_rows),
        "response_type_counts": dict(type_counts),
        "target_cpfs": len(target_cpfs),
        "xmls_generated": len(generated_ok),
        "xml_type_counts": xml_type_counts,
        "blocked_count": len(blocked),
        "missing_valid_responses": missing,
        "targets": generated,
    }
    manifest_path(per_apur).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    with (out_dir / f"preflight_correcao_jaque_{per_apur}.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "cpf", "has_plano", "has_pensao", "generated", "reason", "status", "codigo",
            "nr_recibo", "info_pgtos", "plan_entries", "pensao_entries", "xml",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(generated)
    return manifest


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    items = []
    for item in manifest.get("targets") or []:
        if not item.get("generated"):
            continue
        root = etree.fromstring(Path(item["xml"]).read_bytes())
        items.append(
            {
                "cpf": item["cpf"],
                "indRetif": root.xpath('string(//*[local-name()="indRetif"])'),
                "nrRecibo": root.xpath('string(//*[local-name()="nrRecibo"])'),
                "perApur": root.xpath('string(//*[local-name()="perApur"])'),
                "planSaude": len(root.xpath('//*[local-name()="planSaude"]')),
                "penAlim": len(root.xpath('//*[local-name()="penAlim"]')),
                "infoIRCR": len(root.xpath('//*[local-name()="infoIRCR"]')),
                "signature": bool(root.xpath('//*[local-name()="Signature"]')),
            }
        )
    wrong = [item for item in items if item["indRetif"] != "2" or item["perApur"] != manifest["per_apur"] or item["signature"]]
    return {"total_validated": len(items), "wrong": wrong, "sample": items[:10]}


def _create_timeline_envio(conn, per_apur: str, total: int, manifest: Path) -> tuple[int, int]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_empresa_id, per_apur),
        )
        mes = cursor.fetchone()
        if not mes:
            raise RuntimeError(f"timeline_mes nao existe para empresa={EMPRESA_ID} per_apur={per_apur}")
        mes_id = int(mes["id"])
        cursor.execute("SELECT COALESCE(MAX(sequencia), 0) + 1 AS prox FROM timeline_envio WHERE timeline_mes_id=%s", (mes_id,))
        sequencia = int(cursor.fetchone()["prox"])
        cursor.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status, iniciado_em,
               total_tentados, total_sucesso, total_erro, resumo)
            VALUES
              (%s, %s, 'envio_massa', 'em_andamento', now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (
                mes_id,
                sequencia,
                total,
                psycopg2.extras.Json(
                    {
                        "rotulo": "correcao_jaque_plano_pensao",
                        "empresa_id_externo": EMPRESA_ID,
                        "per_apur": per_apur,
                        "ambiente": AMBIENTE,
                        "origem": str(manifest),
                        "total_xmls_locais": total,
                    }
                ),
            ),
        )
        envio_id = int(cursor.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


def sign_targets(targets: list[dict[str, Any]], cert_path: Path, senha: str) -> list[dict[str, Any]]:
    pfx_data = cert_path.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in targets:
        unsigned_xml = Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        id_evento = esocial_client._extrair_id(xml_assinado)
        if not id_evento:
            raise RuntimeError(f"Id nao encontrado apos assinatura para CPF {item['cpf']}")
        if id_evento in seen_ids:
            raise RuntimeError(f"Id duplicado apos assinatura: {id_evento}")
        seen_ids.add(id_evento)
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": id_evento})
    return signed


def persist_reabertura(
    *,
    per_apur: str,
    id_evento: str,
    xml_assinado: bytes,
    envio: dict[str, Any],
    consulta: dict[str, Any] | None,
    open_ok: bool,
    origem: str,
) -> dict[str, Any]:
    evento = None
    for item in (consulta or {}).get("eventos") or []:
        if item.get("id_evento") == id_evento:
            evento = item
            break
    if evento is None and (consulta or {}).get("eventos"):
        evento = (consulta or {}).get("eventos")[0]

    codigo = (evento or {}).get("codigo") or envio.get("codigo_resposta")
    descricao = (evento or {}).get("descricao") or envio.get("descricao")
    recibo = (evento or {}).get("nr_recibo")
    ocorrencias = (evento or {}).get("ocorrencias") or envio.get("ocorrencias") or []
    protocolo = envio.get("protocolo")
    xml_retorno = (evento or {}).get("xml_retorno")
    dados = {
        "origem": origem,
        "protocolo": protocolo,
        "codigo": codigo,
        "descricao": descricao,
        "ocorrencias": ocorrencias,
        "consulta": consulta,
        "envio": {
            "codigo_resposta": envio.get("codigo_resposta"),
            "descricao": envio.get("descricao"),
            "dh_recepcao": envio.get("dh_recepcao"),
            "http_status": envio.get("http_status"),
        },
        "xml_retorno": xml_retorno,
    }
    sha = hashlib.sha256(xml_assinado).hexdigest()
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS s1299_fechamento_status (
                  empresa_id    INT          NOT NULL,
                  per_apur      VARCHAR(7)   NOT NULL,
                  fechado       BOOLEAN      NOT NULL DEFAULT FALSE,
                  protocolo     VARCHAR(100),
                  nr_recibo     VARCHAR(100),
                  confirmado_em TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                  origem        VARCHAR(40)  DEFAULT 'sync',
                  PRIMARY KEY (empresa_id, per_apur)
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO explorador_eventos
                  (tipo_evento, cpf, per_apur, nr_recibo, id_evento,
                   dt_processamento, cd_resposta, arquivo_origem, dados_json,
                   xml_entry_name, xml_bytes, xml_size_bytes, xml_sha256)
                VALUES
                  ('S-1298', NULL, %s, %s, %s, NOW(), %s, %s, %s::jsonb,
                   %s, %s, %s, %s)
                ON CONFLICT (id_evento) WHERE id_evento IS NOT NULL DO UPDATE
                   SET nr_recibo = COALESCE(EXCLUDED.nr_recibo, explorador_eventos.nr_recibo),
                       dt_processamento = EXCLUDED.dt_processamento,
                       cd_resposta = EXCLUDED.cd_resposta,
                       arquivo_origem = EXCLUDED.arquivo_origem,
                       dados_json = EXCLUDED.dados_json,
                       xml_entry_name = EXCLUDED.xml_entry_name,
                       xml_bytes = EXCLUDED.xml_bytes,
                       xml_size_bytes = EXCLUDED.xml_size_bytes,
                       xml_sha256 = EXCLUDED.xml_sha256
                RETURNING id
                """,
                (
                    per_apur,
                    recibo,
                    id_evento,
                    codigo,
                    f"s1298_reabertura_{per_apur}_solucoes.xml",
                    json.dumps(dados, ensure_ascii=False, default=str),
                    f"s1298_reabertura_{per_apur}_solucoes.xml",
                    xml_assinado,
                    len(xml_assinado),
                    sha,
                ),
            )
            evento_db_id = int(cursor.fetchone()[0])
            if open_ok:
                cursor.execute(
                    """
                    INSERT INTO s1299_fechamento_status
                          (empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em)
                    VALUES (%s, %s, false, %s, %s, %s, NOW())
                    ON CONFLICT (empresa_id, per_apur) DO UPDATE
                       SET fechado = false,
                           protocolo = EXCLUDED.protocolo,
                           nr_recibo = COALESCE(EXCLUDED.nr_recibo, s1299_fechamento_status.nr_recibo),
                           origem = EXCLUDED.origem,
                           confirmado_em = NOW()
                    """,
                    (internal_empresa_id, per_apur, protocolo, recibo, origem),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {
        "evento_db_id": evento_db_id,
        "codigo": codigo,
        "descricao": descricao,
        "nr_recibo": recibo,
        "ocorrencias": ocorrencias,
        "open_ok": open_ok,
        "origem": origem,
    }


def is_already_open(evento: dict[str, Any] | None) -> bool:
    if not evento:
        return False
    parts = [evento.get("codigo"), evento.get("descricao")]
    for ocorrencia in evento.get("ocorrencias") or []:
        parts.extend([ocorrencia.get("codigo"), ocorrencia.get("descricao")])
    blob = ascii_fold(" | ".join(text(part) for part in parts))
    return "715" in blob or "ja esta aberta" in blob or "ja se encontra aberta" in blob


def enviar_reabertura(per_apur: str, cert_path: Path, senha: str) -> dict[str, Any]:
    empregador = {"tpInsc": 1, "nrInsc": CNPJ}
    xml_unsigned = S1298XMLGenerator.gerar(empregador, per_apur, ind_apuracao="1", tp_amb=TP_AMB)
    xml_assinado = S1010XMLSigner.assinar(xml_unsigned, cert_path.read_bytes(), senha)
    id_evento = esocial_client._extrair_id(xml_assinado)
    if not id_evento:
        raise RuntimeError("Id do S-1298 assinado nao encontrado")
    evento_lote = esocial_client.EventoLote(xml_bytes=xml_assinado, id_evento=id_evento)
    print(f"=> S-1298 abertura/reabertura {per_apur}: POST EnviarLoteEventos")
    envio = esocial_client.enviar_lote(
        [evento_lote],
        cert_path=str(cert_path),
        cert_password=senha,
        cnpj_empregador=CNPJ,
        ambiente=AMBIENTE,
        grupo=GRUPO,
    )
    print(
        "=> S-1298 retorno envio "
        f"http={envio.get('http_status')} cd={envio.get('codigo_resposta')} "
        f"desc={envio.get('descricao')} protocolo={envio.get('protocolo')}"
    )
    if not envio.get("sucesso"):
        persisted = persist_reabertura(
            per_apur=per_apur,
            id_evento=id_evento,
            xml_assinado=xml_assinado,
            envio=envio,
            consulta=None,
            open_ok=False,
            origem="s1298_envio_erro",
        )
        raise RuntimeError(f"S-1298 nao recebido pelo eSocial: {persisted}")

    consulta = None
    for tentativa in range(POLL_TENTATIVAS):
        time.sleep(POLL_INTERVALO_S)
        consulta = esocial_client.consultar_lote(
            envio["protocolo"],
            cert_path=str(cert_path),
            cert_password=senha,
            ambiente=AMBIENTE,
        )
        print(
            f"=> S-1298 poll {tentativa + 1}/{POLL_TENTATIVAS}: "
            f"cd_lote={consulta.get('codigo_lote')} eventos={len(consulta.get('eventos') or [])}"
        )
        if consulta.get("codigo_lote") == "201" and consulta.get("eventos"):
            break
        if consulta.get("codigo_lote") and consulta.get("codigo_lote") != "101":
            break

    evento = None
    for item in (consulta or {}).get("eventos") or []:
        if item.get("id_evento") == id_evento:
            evento = item
            break
    if evento is None and (consulta or {}).get("eventos"):
        evento = (consulta or {}).get("eventos")[0]

    codigo = str((evento or {}).get("codigo") or "")
    recibo = (evento or {}).get("nr_recibo")
    already_open = is_already_open(evento)
    open_ok = (codigo in {"201", "202"} and bool(recibo)) or already_open
    origem = "s1298_ja_aberto" if already_open else "s1298_envio"
    persisted = persist_reabertura(
        per_apur=per_apur,
        id_evento=id_evento,
        xml_assinado=xml_assinado,
        envio=envio,
        consulta=consulta,
        open_ok=open_ok,
        origem=origem,
    )
    if not open_ok:
        raise RuntimeError(f"S-1298 processado mas nao abriu periodo: {persisted}")
    print(f"=> S-1298 OK: codigo={persisted.get('codigo')} recibo={persisted.get('nr_recibo')} origem={origem}")
    return {"id_evento": id_evento, "envio": envio, "consulta": consulta, "persisted": persisted}


def execute_s1210(manifest: dict[str, Any], cert_path: Path, senha: str, reabertura: dict[str, Any]) -> dict[str, Any]:
    per_apur = manifest["per_apur"]
    targets = [item for item in manifest.get("targets") or [] if item.get("generated")]
    if not targets:
        raise RuntimeError("nenhum XML gerado para envio")
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_base.PER_APUR = per_apur
        envio_base.PREFLIGHT = manifest_path(per_apur)
        envio_base.CFG_GRUPO = GRUPO
        envio_base.POLL_TENTATIVAS = POLL_TENTATIVAS
        envio_base.POLL_INTERVALO_S = POLL_INTERVALO_S
        envio_base._verificar_estado_atual(conn_db, targets)
        signed = sign_targets(targets, cert_path, senha)
        print(f"=> S-1210 assinados localmente: {len(signed)} XMLs")
        envio_id, mes_id = _create_timeline_envio(conn_db, per_apur, len(signed), manifest_path(per_apur))
        print(f"=> timeline_envio criado id={envio_id} timeline_mes={mes_id}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        print(f"=> timeline_envio_item criados: {len(item_ids)}")
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        print("=> XMLs assinados gravados e vinculados aos items")

        sucesso_total = 0
        erro_total = 0
        protocolos: list[str] = []
        histograma: dict[str, int] = {}
        for index in range(0, len(signed), CFG_LOTE_MAX):
            lote = signed[index:index + CFG_LOTE_MAX]
            print(f"\n>> lote S-1210 {index // CFG_LOTE_MAX + 1} ({len(lote)} eventos)")
            resultado = envio_base._processar_lote(
                lote,
                item_ids,
                cert_path=cert_path,
                senha=senha,
                cnpj=CNPJ,
                conn_db=conn_db,
                conn_w=conn_w,
            )
            sucesso_total += int(resultado["sucesso"])
            erro_total += int(resultado["erro"])
            if resultado.get("protocolo"):
                protocolos.append(str(resultado["protocolo"]))
            for codigo, total in (resultado.get("histograma") or {}).items():
                histograma[codigo] = histograma.get(codigo, 0) + int(total)

        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso_total,
            erro=erro_total,
            resumo_extra={
                "rotulo_final": "correcao_jaque_plano_pensao",
                "per_apur": per_apur,
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "manifest": str(manifest_path(per_apur)),
                "reabertura": {
                    "codigo": reabertura.get("persisted", {}).get("codigo"),
                    "nr_recibo": reabertura.get("persisted", {}).get("nr_recibo"),
                    "origem": reabertura.get("persisted", {}).get("origem"),
                },
                "plan_xmls": manifest.get("xml_type_counts", {}).get("plano"),
                "pensao_xmls": manifest.get("xml_type_counts", {}).get("pensao"),
            },
        )
        print("\n=== RESUMO ENVIO CORRECAO JAQUE PLANO/PENSAO ===")
        print(f"per_apur  : {per_apur}")
        print(f"envio_id  : {envio_id}")
        print(f"protocolos: {protocolos}")
        print(f"sucesso   : {sucesso_total}")
        print(f"erro      : {erro_total}")
        print(f"histograma: {histograma}")
        return {
            "envio_id": envio_id,
            "sucesso": sucesso_total,
            "erro": erro_total,
            "protocolos": protocolos,
            "histograma": histograma,
        }
    except Exception:
        conn_db.rollback()
        conn_w.rollback()
        raise
    finally:
        conn_db.close()
        conn_w.close()


def latest_status_summary(per_apur: str, cpfs: list[str]) -> dict[str, Any]:
    if not cpfs:
        return {"total": 0, "by_status_codigo": {}, "rows": []}
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.nr_recibo_novo, it.id AS item_id, te.id AS envio_id, it.criado_em
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf = ANY(%s)
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT * FROM latest ORDER BY cpf
                """,
                (internal_empresa_id, per_apur, cpfs),
            )
            rows = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
    counts = Counter(f"{row.get('status')}|{row.get('erro_codigo') or ''}" for row in rows)
    return {"total": len(rows), "by_status_codigo": dict(counts), "rows": rows}


def dry_run(per_apur: str) -> dict[str, Any]:
    manifest = generate_manifest(per_apur)
    validation = validate_manifest(manifest)
    target_cpfs = [item["cpf"] for item in manifest.get("targets") or [] if item.get("generated")]
    latest = latest_status_summary(per_apur, target_cpfs)
    return {"ok": True, "dry_run": True, "manifest": str(manifest_path(per_apur)), "summary": manifest, "validation": validation, "latest": latest}


def execute(per_apur: str) -> dict[str, Any]:
    if not re.fullmatch(r"20\d{2}-\d{2}", per_apur):
        raise RuntimeError(f"per_apur invalido: {per_apur}")
    if not DEFAULT_CERT.exists():
        raise RuntimeError(f"certificado nao encontrado: {DEFAULT_CERT}")
    senha = read_password()
    manifest = generate_manifest(per_apur)
    validation = validate_manifest(manifest)
    if validation["wrong"]:
        raise RuntimeError(f"validacao dos XMLs falhou: {validation['wrong'][:5]}")
    if manifest["blocked_count"]:
        raise RuntimeError(f"ha XMLs bloqueados no preflight: {manifest['blocked_count']}")
    print(
        f"=> preflight {per_apur}: respostas={manifest['response_rows']} "
        f"cpfs={manifest['target_cpfs']} xmls={manifest['xmls_generated']} "
        f"faltantes={len(manifest['missing_valid_responses'])}"
    )
    reabertura = enviar_reabertura(per_apur, DEFAULT_CERT, senha)
    envio = execute_s1210(manifest, DEFAULT_CERT, senha, reabertura)
    target_cpfs = [item["cpf"] for item in manifest.get("targets") or [] if item.get("generated")]
    latest = latest_status_summary(per_apur, target_cpfs)
    result = {"ok": True, "per_apur": per_apur, "manifest": str(manifest_path(per_apur)), "reabertura": reabertura["persisted"], "envio": envio, "latest": latest}
    (month_dir(per_apur) / f"resultado_execucao_{per_apur}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-apur", default="2025-02")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()

    if not args.execute:
        print(json.dumps(dry_run(args.per_apur), ensure_ascii=False, indent=2, default=str))
        return 0
    expected_token = confirm_token(args.per_apur)
    valid_tokens = {expected_token}
    if args.per_apur == "2025-02":
        valid_tokens.add(LEGACY_CONFIRM_TOKEN)
    if args.confirmar not in valid_tokens:
        raise SystemExit(f"Para executar, use --confirmar {expected_token}")
    print(json.dumps(execute(args.per_apur), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())