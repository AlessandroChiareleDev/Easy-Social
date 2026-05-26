from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2.extras
from lxml import etree


ROOT = Path(r"C:\Users\xandao\Documents\GitHub\Easy-Social")
BACKEND_V2 = Path(r"C:\Users\xandao\Documents\GitHub\Easy-eSocial-v2\backend")
if str(BACKEND_V2) not in sys.path:
    sys.path.insert(0, str(BACKEND_V2))

from app import db, esocial_client, tenant  # noqa: E402
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
CNPJ = "09445502000109"
CNPJ_RAIZ = CNPJ[:8]
AMBIENTE = "producao"
TP_AMB = "1"
GRUPO = 3
CONFIRM_TOKEN = "FECHAR_AGOSTO_SOLUCOES_S1299"
CERT_PATH = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"
SENHA_TXT = Path(r"C:\Users\xandao\Downloads\Senha solucoes.txt")
OUT_DIR = ROOT / "relatorio_ana" / "FECHAMENTO_AGOSTO_SOLUCOES"
XML_UNSIGNED = OUT_DIR / "S1299_2025-08_SOLUCOES_unsigned.xml"
XML_SIGNED = OUT_DIR / "S1299_2025-08_SOLUCOES_signed.xml"
MANIFEST = OUT_DIR / "manifest_fechamento_s1299_agosto_solucoes.json"
POLL_TENTATIVAS = 12
POLL_INTERVALO_S = 8

NS = "http://www.esocial.gov.br/schema/evt/evtFechaEvPer/v_S_01_03_00"
NSMAP = {None: NS}


def qname(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def sub(parent: etree._Element, tag: str, text: Any | None = None) -> etree._Element:
    node = etree.SubElement(parent, qname(tag))
    if text is not None:
        node.text = str(text)
    return node


def gerar_id(tp_insc: int, nr_insc: str, seq: int = 1) -> str:
    nr_insc_padded = str(nr_insc).ljust(14, "0")[:14]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"ID{tp_insc}{nr_insc_padded}{timestamp}{seq:05d}"


def gerar_s1299() -> bytes:
    root = etree.Element(qname("eSocial"), nsmap=NSMAP)
    evt = sub(root, "evtFechaEvPer")
    evt.set("Id", gerar_id(1, CNPJ_RAIZ))

    ide_evento = sub(evt, "ideEvento")
    sub(ide_evento, "indApuracao", "1")
    sub(ide_evento, "perApur", PER_APUR)
    sub(ide_evento, "tpAmb", TP_AMB)
    sub(ide_evento, "procEmi", "1")
    sub(ide_evento, "verProc", "EasySocial_1.0")

    ide_empregador = sub(evt, "ideEmpregador")
    sub(ide_empregador, "tpInsc", "1")
    sub(ide_empregador, "nrInsc", CNPJ_RAIZ)

    info_fech = sub(evt, "infoFech")
    sub(info_fech, "evtRemun", "S")
    sub(info_fech, "evtPgtos", "S")
    sub(info_fech, "evtComProd", "N")
    sub(info_fech, "evtContratAvNP", "N")
    sub(info_fech, "evtInfoComplPer", "N")

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def read_password() -> str:
    senha = os.getenv("ESOCIAL_CERT_SENHA") or ""
    if senha.strip():
        return senha.strip()
    if SENHA_TXT.exists():
        senha = SENHA_TXT.read_text(encoding="utf-8", errors="ignore").strip()
    if not senha:
        raise RuntimeError(f"senha do certificado nao encontrada: {SENHA_TXT}")
    return senha


def validate_xml(xml_bytes: bytes, *, signed: bool = False) -> dict[str, Any]:
    root = etree.fromstring(xml_bytes)
    event_id = esocial_client._extrair_id(xml_bytes)
    per_apur = root.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="perApur"])').strip()
    tp_amb = root.xpath('string(//*[local-name()="ideEvento"]/*[local-name()="tpAmb"])').strip()
    nr_insc = root.xpath('string(//*[local-name()="ideEmpregador"]/*[local-name()="nrInsc"])').strip()
    info = {
        "id_evento": event_id,
        "per_apur": per_apur,
        "tp_amb": tp_amb,
        "nr_insc": nr_insc,
        "signed": bool(root.xpath('//*[local-name()="Signature"]')),
        "size_bytes": len(xml_bytes),
    }
    if not event_id or len(event_id) != 36:
        raise RuntimeError(f"Id do S-1299 invalido: {event_id}")
    if per_apur != PER_APUR:
        raise RuntimeError(f"perApur divergente: {per_apur}")
    if tp_amb != TP_AMB:
        raise RuntimeError(f"tpAmb divergente: {tp_amb}")
    if nr_insc != CNPJ_RAIZ:
        raise RuntimeError(f"nrInsc divergente: {nr_insc}")
    if signed and not info["signed"]:
        raise RuntimeError("XML assinado sem Signature")
    return info


def preflight_local() -> dict[str, Any]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.id AS item_id, it.timeline_envio_id AS envio_id
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf IS NOT NULL
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT status, COALESCE(erro_codigo, '') AS erro_codigo, COUNT(*) AS total
                  FROM latest
                 GROUP BY status, COALESCE(erro_codigo, '')
                 ORDER BY status, erro_codigo
                """,
                (internal_empresa_id, PER_APUR),
            )
            s1210_stats = [dict(row) for row in cursor.fetchall()]
            cursor.execute(
                """
                WITH latest AS (
                    SELECT DISTINCT ON (it.cpf)
                           it.cpf, it.status, it.erro_codigo, it.erro_mensagem,
                           it.id AS item_id, it.timeline_envio_id AS envio_id
                      FROM timeline_envio_item it
                      JOIN timeline_envio te ON te.id = it.timeline_envio_id
                      JOIN timeline_mes tm ON tm.id = te.timeline_mes_id
                     WHERE tm.empresa_id = %s
                       AND tm.per_apur = %s
                       AND it.tipo_evento = 'S-1210'
                       AND it.cpf IS NOT NULL
                     ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                )
                SELECT cpf, status, erro_codigo, erro_mensagem, item_id, envio_id
                  FROM latest
                      WHERE status <> 'sucesso'
                          OR COALESCE(erro_codigo, '') NOT IN ('', '202', '459_SEM_RECIBO')
                 ORDER BY cpf
                 LIMIT 20
                """,
                (internal_empresa_id, PER_APUR),
            )
            pendencias = [dict(row) for row in cursor.fetchall()]
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
                SELECT empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em
                  FROM s1299_fechamento_status
                 WHERE empresa_id = %s AND per_apur = %s
                """,
                (internal_empresa_id, PER_APUR),
            )
            fechamento_status = dict(cursor.fetchone() or {})
            cursor.execute(
                """
                SELECT tipo_evento, cd_resposta, COUNT(*) AS total, MAX(dt_processamento) AS ultimo
                  FROM explorador_eventos
                 WHERE per_apur = %s
                   AND tipo_evento IN ('S-1298', 'S-1299')
                 GROUP BY tipo_evento, cd_resposta
                 ORDER BY tipo_evento, cd_resposta
                """,
                (PER_APUR,),
            )
            eventos_periodo = [dict(row) for row in cursor.fetchall()]
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if pendencias:
        raise RuntimeError(f"existem pendencias S-1210 antes do fechamento: {pendencias[:5]}")
    if fechamento_status.get("fechado") is True:
        raise RuntimeError(
            f"periodo {PER_APUR} ja consta fechado: "
            f"protocolo={fechamento_status.get('protocolo')} "
            f"recibo={fechamento_status.get('nr_recibo')}"
        )
    if not CERT_PATH.exists():
        raise RuntimeError(f"certificado nao encontrado: {CERT_PATH}")
    if not (os.getenv("ESOCIAL_CERT_SENHA") or SENHA_TXT.exists()):
        raise RuntimeError(f"senha nao encontrada em env nem em {SENHA_TXT}")

    return {
        "empresa_id_externo": EMPRESA_ID,
        "empresa_id_interno": internal_empresa_id,
        "per_apur": PER_APUR,
        "s1210_stats": s1210_stats,
        "pendencias_s1210": len(pendencias),
        "fechamento_status_atual": fechamento_status,
        "eventos_s1298_s1299_periodo": eventos_periodo,
        "certificado_ok": True,
        "senha_ok": True,
    }


def salvar_fechamento(
    *,
    id_evento: str,
    xml_assinado: bytes,
    protocolo: str | None,
    envio: dict[str, Any],
    consulta: dict[str, Any] | None,
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
    xml_retorno = (evento or {}).get("xml_retorno")
    aceito = str(codigo) in {"201", "202"} and bool(recibo)

    dados = {
        "origem": f"envio_s1299_{PER_APUR}_solucoes",
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

    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    sha = hashlib.sha256(xml_assinado).hexdigest()
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO explorador_eventos
                  (tipo_evento, cpf, per_apur, nr_recibo, id_evento,
                   dt_processamento, cd_resposta, arquivo_origem, dados_json,
                   xml_entry_name, xml_bytes, xml_size_bytes, xml_sha256)
                VALUES
                  ('S-1299', NULL, %s, %s, %s, NOW(), %s, %s, %s::jsonb,
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
                    PER_APUR,
                    recibo,
                    id_evento,
                    codigo,
                    f"s1299_fechamento_{PER_APUR}_solucoes.xml",
                    json.dumps(dados, ensure_ascii=False, default=str),
                    f"s1299_fechamento_{PER_APUR}_solucoes.xml",
                    xml_assinado,
                    len(xml_assinado),
                    sha,
                ),
            )
            evento_db_id = int(cursor.fetchone()[0])
            cursor.execute(
                """
                INSERT INTO s1299_fechamento_status
                      (empresa_id, per_apur, fechado, protocolo, nr_recibo, origem, confirmado_em)
                VALUES (%s, %s, %s, %s, %s, 's1299_envio', NOW())
                ON CONFLICT (empresa_id, per_apur) DO UPDATE
                   SET fechado = EXCLUDED.fechado,
                       protocolo = EXCLUDED.protocolo,
                       nr_recibo = COALESCE(EXCLUDED.nr_recibo, s1299_fechamento_status.nr_recibo),
                       origem = 's1299_envio',
                       confirmado_em = NOW()
                """,
                (internal_empresa_id, PER_APUR, aceito, protocolo, recibo),
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
        "aceito": aceito,
    }


def montar_xmls() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    xml_unsigned = gerar_s1299()
    unsigned_info = validate_xml(xml_unsigned)
    XML_UNSIGNED.write_bytes(xml_unsigned)
    senha = read_password()
    xml_signed = S1010XMLSigner.assinar(xml_unsigned, CERT_PATH.read_bytes(), senha)
    signed_info = validate_xml(xml_signed, signed=True)
    if signed_info["id_evento"] != unsigned_info["id_evento"]:
        raise RuntimeError(f"Id mudou apos assinatura: {unsigned_info['id_evento']} != {signed_info['id_evento']}")
    XML_SIGNED.write_bytes(xml_signed)
    return {
        "unsigned_xml": str(XML_UNSIGNED),
        "signed_xml": str(XML_SIGNED),
        "unsigned": unsigned_info,
        "signed": signed_info,
    }


def dry_run() -> dict[str, Any]:
    preflight = preflight_local()
    xmls = montar_xmls()
    manifest = {
        "ok": True,
        "dry_run": True,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "cnpj": CNPJ,
        "ambiente": AMBIENTE,
        "preflight": preflight,
        "xmls": xmls,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"ok": True, "dry_run": True, "manifest": str(MANIFEST), **xmls, "preflight": preflight}


def execute() -> dict[str, Any]:
    preflight = preflight_local()
    xmls = montar_xmls()
    xml_assinado = XML_SIGNED.read_bytes()
    id_evento = str(xmls["signed"]["id_evento"])
    senha = read_password()

    evento = esocial_client.EventoLote(xml_bytes=xml_assinado, id_evento=id_evento)
    print(f"=> S-1299 fechamento SOLUCOES {PER_APUR} producao Id={id_evento}")
    envio = esocial_client.enviar_lote(
        [evento],
        cert_path=str(CERT_PATH),
        cert_password=senha,
        cnpj_empregador=CNPJ,
        ambiente=AMBIENTE,
        grupo=GRUPO,
    )
    print(
        "-> POST "
        f"http={envio.get('http_status')} cd={envio.get('codigo_resposta')} "
        f"desc={envio.get('descricao')} protocolo={envio.get('protocolo')}"
    )
    if envio.get("ocorrencias"):
        for ocorrencia in envio["ocorrencias"]:
            print(f"   OC {ocorrencia.get('codigo')}: {str(ocorrencia.get('descricao') or '')[:240]}")
    if not envio.get("sucesso"):
        salvo = salvar_fechamento(
            id_evento=id_evento,
            xml_assinado=xml_assinado,
            protocolo=envio.get("protocolo"),
            envio=envio,
            consulta=None,
        )
        return {
            "ok": False,
            "stage": "envio_lote",
            "id_evento": id_evento,
            "envio": envio,
            "salvo": salvo,
            "preflight": preflight,
        }

    protocolo = envio.get("protocolo")
    consulta = None
    print(f"=> polling consultar_lote protocolo={protocolo}")
    for tentativa in range(1, POLL_TENTATIVAS + 1):
        time.sleep(POLL_INTERVALO_S)
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=str(CERT_PATH),
            cert_password=senha,
            ambiente=AMBIENTE,
        )
        codigo_lote = consulta.get("codigo_lote")
        eventos = consulta.get("eventos") or []
        print(f"   [{tentativa}/{POLL_TENTATIVAS}] cd_lote={codigo_lote} eventos={len(eventos)}")
        if codigo_lote == "201":
            break
        if codigo_lote and codigo_lote not in {"101", "104"}:
            break

    salvo = salvar_fechamento(
        id_evento=id_evento,
        xml_assinado=xml_assinado,
        protocolo=protocolo,
        envio=envio,
        consulta=consulta,
    )
    result = {
        "ok": bool(salvo.get("aceito")),
        "id_evento": id_evento,
        "protocolo": protocolo,
        "codigo": salvo.get("codigo"),
        "descricao": salvo.get("descricao"),
        "nr_recibo": salvo.get("nr_recibo"),
        "evento_db_id": salvo.get("evento_db_id"),
        "ocorrencias": salvo.get("ocorrencias"),
        "manifest": str(MANIFEST),
        "preflight": preflight,
    }
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "empresa_id": EMPRESA_ID,
        "per_apur": PER_APUR,
        "cnpj": CNPJ,
        "ambiente": AMBIENTE,
        "xmls": xmls,
        "resultado": result,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def poll_existing(protocolo: str) -> dict[str, Any]:
    if not MANIFEST.exists():
        raise RuntimeError(f"manifest nao encontrado: {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    resultado_anterior = manifest.get("resultado") or {}
    xmls = manifest.get("xmls") or {}
    signed_info = xmls.get("signed") or {}
    id_evento = str(resultado_anterior.get("id_evento") or signed_info.get("id_evento") or "")
    signed_path = Path(xmls.get("signed_xml") or XML_SIGNED)
    if not id_evento:
        raise RuntimeError("Id do evento nao encontrado no manifest")
    if not signed_path.exists():
        raise RuntimeError(f"XML assinado nao encontrado: {signed_path}")

    senha = read_password()
    consulta = None
    print(f"=> repoll S-1299 protocolo={protocolo} Id={id_evento}")
    for tentativa in range(1, POLL_TENTATIVAS + 1):
        time.sleep(POLL_INTERVALO_S)
        consulta = esocial_client.consultar_lote(
            protocolo,
            cert_path=str(CERT_PATH),
            cert_password=senha,
            ambiente=AMBIENTE,
        )
        codigo_lote = consulta.get("codigo_lote")
        eventos = consulta.get("eventos") or []
        print(f"   [{tentativa}/{POLL_TENTATIVAS}] cd_lote={codigo_lote} eventos={len(eventos)}")
        if codigo_lote == "201":
            break
        if codigo_lote and codigo_lote not in {"101", "104"}:
            break

    envio_fallback = {
        "codigo_resposta": resultado_anterior.get("codigo") or "201",
        "descricao": resultado_anterior.get("descricao") or "Lote Recebido com Sucesso.",
        "http_status": 200,
    }
    salvo = salvar_fechamento(
        id_evento=id_evento,
        xml_assinado=signed_path.read_bytes(),
        protocolo=protocolo,
        envio=envio_fallback,
        consulta=consulta,
    )
    result = {
        "ok": bool(salvo.get("aceito")),
        "id_evento": id_evento,
        "protocolo": protocolo,
        "codigo_lote": (consulta or {}).get("codigo_lote"),
        "descricao_lote": (consulta or {}).get("descricao_lote"),
        "codigo": salvo.get("codigo"),
        "descricao": salvo.get("descricao"),
        "nr_recibo": salvo.get("nr_recibo"),
        "evento_db_id": salvo.get("evento_db_id"),
        "ocorrencias": salvo.get("ocorrencias"),
        "manifest": str(MANIFEST),
    }
    manifest["resultado"] = result
    manifest["repoll_at"] = datetime.now().isoformat(timespec="seconds")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--poll-protocolo", default="")
    parser.add_argument("--confirmar", default="")
    args = parser.parse_args()
    if args.poll_protocolo:
        result = poll_existing(args.poll_protocolo)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result.get("ok") else 2
    if not args.execute:
        print(json.dumps(dry_run(), ensure_ascii=False, indent=2, default=str))
        return 0
    if args.confirmar != CONFIRM_TOKEN:
        raise SystemExit(f"Para executar, use --confirmar {CONFIRM_TOKEN}")
    result = execute()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())