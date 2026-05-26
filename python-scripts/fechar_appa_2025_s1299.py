from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python-scripts"))

from db_config import LOCAL_DB_CONFIG  # noqa: E402
from esocial.certificate_manager import CertificateManager  # noqa: E402
from esocial.esocial_client import ESocialClient  # noqa: E402
from esocial.soap_builder import SOAPEnvelopeBuilder  # noqa: E402
from esocial.xml_s1299 import S1299XMLGenerator  # noqa: E402
from esocial.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 1
EXPECTED_CNPJ = "05969071000110"
EXPECTED_CNPJ_RAIZ = EXPECTED_CNPJ[:8]
TP_AMB = "1"
IND_APURACAO = "1"
GRUPO = "3"
CONFIRM_TOKEN = "FECHAR_APPA_2025_S1299_TODOS"
MONTHS_2025 = [f"2025-{month:02d}" for month in range(1, 13)]
OUT_DIR = ROOT / "relatorio_ana" / "FECHAMENTO_APPA_2025"
MANIFEST = OUT_DIR / "manifest_fechamento_s1299_appa_2025.json"


def connect_local():
    return psycopg2.connect(**LOCAL_DB_CONFIG)


def ensure_tables(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS s1299_fechamento_status (
                empresa_id INT NOT NULL,
                per_apur VARCHAR(7) NOT NULL,
                fechado BOOLEAN NOT NULL DEFAULT FALSE,
                protocolo VARCHAR(100),
                nr_recibo VARCHAR(100),
                origem VARCHAR(80) DEFAULT 's1299_envio',
                confirmado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                detalhes JSONB,
                PRIMARY KEY (empresa_id, per_apur)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS esocial_envios (
                id SERIAL PRIMARY KEY,
                tipo_evento VARCHAR(10) NOT NULL DEFAULT 'S-1010',
                modo VARCHAR(20) NOT NULL DEFAULT 'alteracao',
                status VARCHAR(30) NOT NULL DEFAULT 'enviado',
                protocolo_envio VARCHAR(100),
                codigo_resposta VARCHAR(10),
                descricao_resposta TEXT,
                total_eventos INTEGER DEFAULT 0,
                rubrica_ids JSONB,
                xml_retorno TEXT,
                ocorrencias JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                ambiente VARCHAR(2) NOT NULL DEFAULT '2',
                ini_valid VARCHAR(10),
                rubrica_detalhes JSONB,
                xml_enviado TEXT,
                recibo_consulta JSONB,
                nr_recibo VARCHAR(100)
            )
            """
        )
    conn.commit()


def load_cert() -> tuple[str, bytes, str, str]:
    with connect_local() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT cnpj, titular, arquivo_path, senha_encrypted
                  FROM certificados_a1
                 WHERE ativo = TRUE
                 ORDER BY id DESC
                 LIMIT 1
                """
            )
            row = cursor.fetchone()
    if not row:
        raise RuntimeError("nenhum certificado A1 ativo no banco local")
    cnpj = str(row["cnpj"] or "")
    if cnpj != EXPECTED_CNPJ:
        raise RuntimeError(f"certificado ativo nao e APPA: cnpj={cnpj}")
    cert_path = Path(row["arquivo_path"])
    if not cert_path.exists():
        raise RuntimeError(f"certificado ativo nao encontrado em disco: {cert_path}")
    senha = CertificateManager.decrypt_password(row["senha_encrypted"])
    pfx_data = cert_path.read_bytes()
    CertificateManager.validate_pfx(pfx_data, senha)
    return cnpj, pfx_data, senha, str(row.get("titular") or "")


def event_id(xml_bytes: bytes) -> str:
    root = etree.fromstring(xml_bytes)
    value = root.xpath('string(//*[local-name()="evtFechaEvPer"]/@Id)')
    if not value:
        raise RuntimeError("Id do evtFechaEvPer nao encontrado")
    return value


def xml_info(xml_bytes: bytes) -> dict[str, Any]:
    root = etree.fromstring(xml_bytes)
    return {
        "id_evento": root.xpath('string(//*[local-name()="evtFechaEvPer"]/@Id)'),
        "per_apur": root.xpath('string(//*[local-name()="perApur"])'),
        "tp_amb": root.xpath('string(//*[local-name()="tpAmb"])'),
        "nr_insc": root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])'),
        "signed": bool(root.xpath('//*[local-name()="Signature"]')),
    }


def validate_xml(info: dict[str, Any], per_apur: str, signed: bool) -> None:
    if info["per_apur"] != per_apur:
        raise RuntimeError(f"perApur divergente: {info}")
    if info["tp_amb"] != TP_AMB:
        raise RuntimeError(f"tpAmb divergente: {info}")
    if info["nr_insc"] != EXPECTED_CNPJ_RAIZ:
        raise RuntimeError(f"nrInsc divergente: {info}")
    if signed and not info["signed"]:
        raise RuntimeError("XML assinado sem Signature")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    no_accents = unicodedata.normalize("NFKD", value)
    no_accents = "".join(char for char in no_accents if not unicodedata.combining(char))
    return no_accents.casefold()


def is_already_closed(result: dict[str, Any]) -> bool:
    chunks: list[str] = [result.get("descricao") or "", result.get("erro") or ""]
    for event in result.get("eventos") or []:
        chunks.append(event.get("descricao") or "")
        for occurrence in event.get("ocorrencias") or []:
            chunks.append(occurrence.get("descricao") or "")
    text = normalize_text("\n".join(chunks))
    if not text:
        return False
    if "fech" in text and ("ja existe" in text or "ja foi" in text or "existe" in text):
        return True
    if "periodo" in text and ("encerrado" in text or "fechado" in text):
        return True
    if "apuracao" in text and ("encerrad" in text or "fechad" in text):
        return True
    return False


def current_status() -> dict[str, dict[str, Any]]:
    with connect_local() as conn:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em, detalhes
                  FROM s1299_fechamento_status
                 WHERE empresa_id = %s AND per_apur = ANY(%s)
                 ORDER BY per_apur
                """,
                (EMPRESA_ID, MONTHS_2025),
            )
            return {row["per_apur"]: dict(row) for row in cursor.fetchall()}


def persist_attempt(
    per_apur: str,
    protocolo: str | None,
    envio: dict[str, Any],
    consulta: dict[str, Any] | None,
    signed_xml: str,
    recibo: str | None,
    fechado: bool,
    origem: str,
) -> dict[str, Any]:
    detalhes = {
        "envio": envio,
        "consulta": consulta,
        "origem": origem,
        "persisted_at": datetime.now().isoformat(timespec="seconds"),
    }
    status = "aceito" if fechado else ("enviado" if envio.get("sucesso") else "erro")
    codigo = None
    descricao = None
    ocorrencias: list[Any] = []
    if consulta:
        codigo = consulta.get("codigo_resposta")
        descricao = consulta.get("descricao")
        for event in consulta.get("eventos") or []:
            ocorrencias.extend(event.get("ocorrencias") or [])
    if not codigo:
        codigo = envio.get("codigo_resposta")
    if not descricao:
        descricao = envio.get("descricao") or envio.get("erro")
    with connect_local() as conn:
        ensure_tables(conn)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO esocial_envios
                    (tipo_evento, modo, ambiente, ini_valid, status, protocolo_envio,
                     codigo_resposta, descricao_resposta, total_eventos, rubrica_ids,
                     xml_enviado, xml_retorno, ocorrencias, recibo_consulta, nr_recibo)
                VALUES
                    ('S-1299', 'fechamento', %s, %s, %s, %s, %s, %s, 1, %s::jsonb,
                     %s, %s, %s::jsonb, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    TP_AMB,
                    per_apur,
                    status,
                    protocolo,
                    codigo,
                    descricao,
                    json.dumps([per_apur], ensure_ascii=False),
                    signed_xml[:50000],
                    (consulta or {}).get("xml_resposta"),
                    json.dumps(ocorrencias, ensure_ascii=False),
                    json.dumps(consulta or {}, ensure_ascii=False),
                    recibo,
                ),
            )
            envio_id = cursor.fetchone()["id"]
            cursor.execute(
                """
                INSERT INTO s1299_fechamento_status
                    (empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em, detalhes)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s::jsonb)
                ON CONFLICT (empresa_id, per_apur) DO UPDATE
                   SET fechado = EXCLUDED.fechado,
                       protocolo = COALESCE(EXCLUDED.protocolo, s1299_fechamento_status.protocolo),
                       nr_recibo = COALESCE(EXCLUDED.nr_recibo, s1299_fechamento_status.nr_recibo),
                       origem = EXCLUDED.origem,
                       confirmado_em = NOW(),
                       detalhes = EXCLUDED.detalhes
                """,
                (
                    EMPRESA_ID,
                    per_apur,
                    fechado,
                    protocolo,
                    recibo,
                    origem,
                    json.dumps(detalhes, ensure_ascii=False),
                ),
            )
        conn.commit()
    return {"envio_id": envio_id, "fechado": fechado, "origem": origem}


def build_month_xml(per_apur: str, pfx_data: bytes, senha: str) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    month_dir = OUT_DIR / per_apur
    month_dir.mkdir(parents=True, exist_ok=True)
    empregador_xml = {"tpInsc": 1, "nrInsc": EXPECTED_CNPJ_RAIZ}
    unsigned = S1299XMLGenerator.gerar(
        empregador_xml,
        per_apur,
        ind_apuracao=IND_APURACAO,
        tp_amb=TP_AMB,
        seq=int(per_apur[-2:]),
    )
    unsigned_info = xml_info(unsigned)
    validate_xml(unsigned_info, per_apur, signed=False)
    signed = S1010XMLSigner.assinar(unsigned, pfx_data, senha)
    signed_info = xml_info(signed)
    validate_xml(signed_info, per_apur, signed=True)
    unsigned_path = month_dir / f"S1299_{per_apur}_APPA_unsigned.xml"
    signed_path = month_dir / f"S1299_{per_apur}_APPA_signed.xml"
    unsigned_path.write_bytes(unsigned)
    signed_path.write_bytes(signed)
    return {
        "per_apur": per_apur,
        "unsigned_xml": str(unsigned_path),
        "signed_xml": str(signed_path),
        "id_evento": signed_info["id_evento"],
        "signed_info": signed_info,
        "signed_bytes": signed,
    }


def poll_protocol(protocolo: str, pfx_data: bytes, senha: str, max_poll: int, poll_interval: int) -> dict[str, Any]:
    url_consulta = SOAPEnvelopeBuilder.url_consulta(producao=True)
    last_result: dict[str, Any] = {}
    for attempt in range(1, max_poll + 1):
        if attempt > 1:
            time.sleep(poll_interval)
        result = ESocialClient.consultar_lote(protocolo, pfx_data, senha, url=url_consulta)
        result["poll_attempt"] = attempt
        last_result = result
        print(f"   poll {attempt}/{max_poll}: lote={result.get('codigo_resposta')} {result.get('descricao') or ''}")
        if result.get("codigo_resposta") != "101":
            return result
    return last_result


def execute_month(per_apur: str, pfx_data: bytes, senha: str, args: argparse.Namespace) -> dict[str, Any]:
    status = current_status().get(per_apur)
    if status and status.get("fechado") is True and not args.force:
        return {"per_apur": per_apur, "skipped": True, "reason": "ja_marcado_fechado_local", "status": status}
    month = build_month_xml(per_apur, pfx_data, senha)
    if not args.execute:
        return {k: value for k, value in month.items() if k != "signed_bytes"} | {"dry_run": True}

    signed_xml = month["signed_bytes"]
    signed_text = signed_xml.decode("utf-8")
    empregador_soap = {"tpInsc": 1, "nrInsc": EXPECTED_CNPJ_RAIZ}
    transmissor_soap = {"tpInsc": 1, "nrInsc": EXPECTED_CNPJ}
    soap = SOAPEnvelopeBuilder.montar_envio([signed_xml], empregador_soap, transmissor_soap, grupo=GRUPO)
    url_envio = SOAPEnvelopeBuilder.url_envio(producao=True)
    print(f"=> Enviando S-1299 APPA {per_apur} Id={month['id_evento']}")
    envio = ESocialClient.enviar_lote(soap, pfx_data, senha, url=url_envio)
    protocolo = envio.get("protocolo")
    print(f"   envio: codigo={envio.get('codigo_resposta')} sucesso={envio.get('sucesso')} protocolo={protocolo}")
    consulta = None
    recibo = None
    fechado = False
    origem = "s1299_envio_erro"
    if protocolo:
        consulta = poll_protocol(protocolo, pfx_data, senha, args.max_poll, args.poll_interval)
        for event in consulta.get("eventos") or []:
            if event.get("nr_recibo"):
                recibo = event.get("nr_recibo")
                fechado = True
                origem = "s1299_envio_aceito"
                break
        if not fechado and is_already_closed(consulta):
            fechado = True
            origem = "s1299_ja_fechado_esocial"
    elif is_already_closed(envio):
        fechado = True
        origem = "s1299_ja_fechado_esocial_envio"
    persisted = persist_attempt(per_apur, protocolo, envio, consulta, signed_text, recibo, fechado, origem)
    return {
        "per_apur": per_apur,
        "id_evento": month["id_evento"],
        "protocolo": protocolo,
        "recibo": recibo,
        "fechado": fechado,
        "origem": origem,
        "envio_codigo": envio.get("codigo_resposta"),
        "consulta_codigo": (consulta or {}).get("codigo_resposta"),
        "persisted": persisted,
        "signed_xml": month["signed_xml"],
    }


def final_audit() -> dict[str, Any]:
    status = current_status()
    rows = [status.get(month) or {"per_apur": month, "fechado": False} for month in MONTHS_2025]
    return {
        "all_closed": all(bool(row.get("fechado")) for row in rows),
        "not_closed": [row["per_apur"] for row in rows if not bool(row.get("fechado"))],
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fecha S-1299 APPA 2025 em producao")
    parser.add_argument("--execute", action="store_true", help="envia de fato para producao")
    parser.add_argument("--confirmar", default="", help="token obrigatorio para envio")
    parser.add_argument("--month", action="append", choices=MONTHS_2025, help="limita a um ou mais meses")
    parser.add_argument("--force", action="store_true", help="reenvia mesmo se marcado fechado localmente")
    parser.add_argument("--max-poll", type=int, default=30)
    parser.add_argument("--poll-interval", type=int, default=8)
    args = parser.parse_args()

    if args.execute and args.confirmar != CONFIRM_TOKEN:
        raise RuntimeError(f"confirmacao invalida; use --confirmar {CONFIRM_TOKEN}")
    if args.execute:
        os.environ.setdefault("ESOCIAL_DUMP_XML_DIR", str(OUT_DIR / "xml_retorno_bruto"))

    cnpj, pfx_data, senha, titular = load_cert()
    months = args.month or MONTHS_2025
    results = []
    for per_apur in months:
        result = execute_month(per_apur, pfx_data, senha, args)
        results.append(result)
        print(json.dumps(result, ensure_ascii=False, default=str))

    audit = final_audit()
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "execute": args.execute,
        "empresa_id": EMPRESA_ID,
        "cnpj": cnpj,
        "titular": titular,
        "months": months,
        "results": results,
        "final_audit": audit,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=> manifest", MANIFEST)
    print("=> final_audit", json.dumps(audit, ensure_ascii=False, default=str))
    if args.execute and not audit["all_closed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()