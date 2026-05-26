from __future__ import annotations

import argparse
import getpass
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
from app import db, tenant  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
MANIFEST = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN" / "manifest_reenvio_original_agosto_202.json"
DEFAULT_CERT = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"
CONFIRM_TOKEN = "REENVIO_ORIGINAL_105"


def _xml_text(root: etree._Element, local_name: str) -> str:
    return str(root.xpath(f"string(//*[local-name()='{local_name}'])") or "").strip()


def _load_targets() -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        raise RuntimeError(f"manifesto nao encontrado: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not data.get("sem_alteracao_xml"):
        raise RuntimeError("manifesto nao marcado como sem_alteracao_xml")

    targets: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in data.get("targets") or []:
        cpf = str(item.get("cpf") or "")
        event_path = Path(item.get("evento_assinado_xml") or "")
        if not cpf or not event_path.exists():
            raise RuntimeError(f"target invalido ou evento assinado nao encontrado: cpf={cpf} path={event_path}")

        xml_bytes = event_path.read_bytes()
        if b"retornoProcessamentoDownload" in xml_bytes or b"<recibo>" in xml_bytes:
            raise RuntimeError(f"evento_assinado_xml contem wrapper/recibo, nao e payload de envio: {event_path}")
        root = etree.fromstring(xml_bytes)
        event_ids = root.xpath("//*[local-name()='evtPgtos']/@Id")
        id_evento = str(event_ids[0]) if event_ids else ""
        if not id_evento:
            raise RuntimeError(f"Id evtPgtos nao encontrado para CPF {cpf}")
        if id_evento in seen_ids:
            raise RuntimeError(f"Id duplicado no manifesto: {id_evento}")
        seen_ids.add(id_evento)

        validations = {
            "cpfBenef": _xml_text(root, "cpfBenef"),
            "indRetif": _xml_text(root, "indRetif"),
            "perApur": _xml_text(root, "perApur"),
        }
        if validations["cpfBenef"] != cpf:
            raise RuntimeError(f"CPF divergente em {event_path}: {validations['cpfBenef']} != {cpf}")
        if validations["indRetif"] != "1":
            raise RuntimeError(f"evento original deveria ser indRetif=1 para CPF {cpf}; veio {validations['indRetif']}")
        if validations["perApur"] != PER_APUR:
            raise RuntimeError(f"perApur divergente para CPF {cpf}: {validations['perApur']}")
        if id_evento != item.get("source_event_id"):
            raise RuntimeError(f"Id divergente para CPF {cpf}: {id_evento} != {item.get('source_event_id')}")
        if not root.xpath("//*[local-name()='Signature']"):
            raise RuntimeError(f"evento assinado sem Signature para CPF {cpf}")
        if item.get("source_cdResposta") != "202":
            raise RuntimeError(f"target nao e cdResposta=202 para CPF {cpf}: {item.get('source_cdResposta')}")

        targets.append({
            **item,
            "xml_assinado": xml_bytes,
            "id_evento_assinado": id_evento,
            "nr_recibo": item.get("source_nrRecibo"),
        })

    if len(targets) != 105:
        raise RuntimeError(f"esperado 105 eventos originais; encontrado {len(targets)}")
    return sorted(targets, key=lambda row: row["cpf"])


def _criar_timeline_envio_reenvio(conn, total: int) -> tuple[int, int]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s", (internal_empresa_id, PER_APUR))
        mes = cur.fetchone()
        if not mes:
            raise RuntimeError(f"timeline_mes nao existe para empresa={EMPRESA_ID} per_apur={PER_APUR}")
        mes_id = int(mes["id"])
        cur.execute("SELECT COALESCE(MAX(sequencia), 0)+1 AS prox FROM timeline_envio WHERE timeline_mes_id=%s", (mes_id,))
        sequencia = int(cur.fetchone()["prox"])
        cur.execute(
            """
            INSERT INTO timeline_envio
              (timeline_mes_id, sequencia, tipo, status,
               iniciado_em, total_tentados, total_sucesso, total_erro, resumo)
            VALUES
              (%s, %s, 'envio_massa', 'em_andamento',
               now(), %s, 0, 0, %s)
            RETURNING id
            """,
            (
                mes_id,
                sequencia,
                total,
                psycopg2.extras.Json({
                    "rotulo": "reenvio_original_agosto_202_deddepen_105",
                    "empresa_id_externo": EMPRESA_ID,
                    "per_apur": PER_APUR,
                    "ambiente": "producao",
                    "origem": str(MANIFEST),
                    "total_xmls_locais": total,
                    "regra": "reenvio literal dos eventos S-1210 originais cdResposta=202; sem retificacao e sem alteracao de XML",
                }),
            ),
        )
        envio_id = int(cur.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


def _criar_items_reenvio(conn, envio_id: int, targets: list[dict[str, Any]]) -> dict[str, int]:
    item_ids: dict[str, int] = {}
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for item in targets:
            cur.execute(
                """
                INSERT INTO timeline_envio_item
                  (timeline_envio_id, cpf, tipo_evento, status,
                   versao_anterior_id, nr_recibo_anterior, xml_enviado_oid)
                VALUES (%s, %s, 'S-1210', 'pendente', NULL, %s, NULL)
                RETURNING id
                """,
                (envio_id, item["cpf"], item.get("source_nrRecibo")),
            )
            item_ids[item["cpf"]] = int(cur.fetchone()["id"])
    conn.commit()
    return item_ids


def _summarize_items(conn, envio_id: int) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT cpf, status, erro_codigo, erro_mensagem,
                   nr_recibo_anterior, nr_recibo_novo
              FROM timeline_envio_item
             WHERE timeline_envio_id=%s
             ORDER BY cpf
            """,
            (envio_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def dry_run() -> dict[str, Any]:
    targets = _load_targets()
    return {
        "ok": True,
        "dry_run": True,
        "total": len(targets),
        "manifest": str(MANIFEST),
        "primeiro_cpf": targets[0]["cpf"],
        "ultimo_cpf": targets[-1]["cpf"],
        "regra": "105 eventos S-1210 originais ja assinados, indRetif=1, cdResposta=202, sem alteracao de XML",
    }


def rodar(*, cert_path: Path, senha: str, cnpj: str) -> dict[str, Any]:
    raise RuntimeError(
        "Rotina desativada: este sender enviaria os originais com indRetif=1. "
        "Para a missao atual use enviar_retificacao_espelho_agosto_202_solucoes.py "
        "(indRetif=2 + nrRecibo, mantendo o conteudo do XML original)."
    )
    targets = _load_targets()
    if not cert_path.exists():
        raise RuntimeError(f"certificado nao encontrado: {cert_path}")
    print(f"=> alvos: {len(targets)} XMLs S-1210 originais 202 {PER_APUR}")
    print("=> modo: reenvio literal, sem reassinar e sem alterar XML")
    print(f"=> certificado transporte: {cert_path}")

    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_id, mes_id = _criar_timeline_envio_reenvio(conn_db, len(targets))
        print(f"=> timeline_envio criado id={envio_id} timeline_mes={mes_id}")
        item_ids = _criar_items_reenvio(conn_db, envio_id, targets)
        print(f"=> timeline_envio_item criados: {len(item_ids)}")
        envio_base._persistir_xmls_assinados(conn_db, conn_w, targets, item_ids)
        print("=> XMLs originais assinados gravados e vinculados aos items")

        sucesso_total = 0
        erro_total = 0
        protocolos: list[str] = []
        histograma: dict[str, int] = {}
        for idx in range(0, len(targets), envio_base.CFG_LOTE_MAX):
            lote = targets[idx:idx + envio_base.CFG_LOTE_MAX]
            print(f"\n>> lote {idx // envio_base.CFG_LOTE_MAX + 1} ({len(lote)} eventos)")
            resultado = envio_base._processar_lote(
                lote,
                item_ids,
                cert_path=cert_path,
                senha=senha,
                cnpj=cnpj,
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
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "rotulo_final": "reenvio_original_agosto_202_deddepen_105",
                "manifest": str(MANIFEST),
                "cpfs": [item["cpf"] for item in targets],
            },
        )
        items = _summarize_items(conn_db, envio_id)
        print("\n=== RESUMO REENVIO ORIGINAL AGOSTO 202 ===")
        print(f"envio_id  : {envio_id}")
        print(f"protocolos: {protocolos}")
        print(f"sucesso   : {sucesso_total}")
        print(f"erro      : {erro_total}")
        print(f"histograma: {histograma}")
        return {
            "ok": True,
            "envio_id": envio_id,
            "sucesso": sucesso_total,
            "erro": erro_total,
            "protocolos": protocolos,
            "histograma": histograma,
            "items": items,
        }
    except Exception:
        conn_db.rollback()
        conn_w.rollback()
        raise
    finally:
        conn_db.close()
        conn_w.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="envia para producao; sem isso roda apenas validacao local")
    parser.add_argument("--confirmar", default="", help=f"para executar, informe {CONFIRM_TOKEN}")
    parser.add_argument("--cert", default=str(DEFAULT_CERT))
    parser.add_argument("--cnpj", default="09445502000109")
    parser.add_argument("--senha", default=os.getenv("ESOCIAL_CERT_SENHA") or "")
    args = parser.parse_args(argv)

    if not args.execute:
        print(json.dumps(dry_run(), ensure_ascii=False, indent=2))
        return 0
    if args.confirmar != CONFIRM_TOKEN:
        raise SystemExit(f"Para enviar em producao, rode com --confirmar {CONFIRM_TOKEN}")

    senha = args.senha
    if not senha:
        senha = getpass.getpass("Senha do certificado A1 SOLUCOES: ")
    if not senha:
        raise SystemExit("Senha nao informada")
    rodar(cert_path=Path(args.cert), senha=senha, cnpj=args.cnpj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())