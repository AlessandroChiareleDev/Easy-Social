from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any

import psycopg2.extras


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
OUT_DIR = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN"
MANIFEST = OUT_DIR / "manifest_correcao_202_deddepen.json"
DEFAULT_CERT = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"


def _load_targets() -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        raise RuntimeError(f"manifesto nao encontrado: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    targets: list[dict[str, Any]] = []
    for item in data.get("targets") or []:
        xml_path = Path(item.get("xml") or "")
        if not xml_path.exists():
            raise RuntimeError(f"XML nao encontrado para CPF {item.get('cpf')}: {xml_path}")
        if not item.get("source_event_id") or not item.get("recibo_ativo"):
            raise RuntimeError(f"manifesto sem source_event_id/recibo_ativo para CPF {item.get('cpf')}")
        if item.get("recibo_fonte") == "front_s1210_cpfs_do_mes.nr_recibo_xml":
            raise RuntimeError(
                "manifesto usa nr_recibo_xml do S-1210 HEAD, fonte ja rejeitada pelo eSocial com 401/459; "
                f"gere novo manifesto com recibo ativo real para CPF {item.get('cpf')}"
            )
        if item.get("recibo_ativo") != item.get("source_recibo"):
            raise RuntimeError(f"recibo ativo diverge do source_recibo para CPF {item.get('cpf')}")
        targets.append({**item, "nr_recibo": item["recibo_ativo"]})
    if len(targets) != 35:
        raise RuntimeError(f"esperado 35 XMLs no manifesto; encontrado {len(targets)}")
    return sorted(targets, key=lambda row: row["cpf"])


def _preencher_evento_id_numerico(conn, targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    cpfs = [item["cpf"] for item in targets]
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT ev.id, ev.cpf, ev.nr_recibo, ev.id_evento
              FROM explorador_eventos ev
              JOIN empresa_zips_brutos z ON z.id = ev.zip_id
             WHERE z.empresa_id=%s
               AND ev.tipo_evento='S-1210'
               AND ev.per_apur=%s
               AND ev.cpf = ANY(%s)
            """,
            (internal_empresa_id, PER_APUR, cpfs),
        )
        rows = [dict(row) for row in cur.fetchall()]
    by_key = {(row["cpf"], row.get("nr_recibo"), row.get("id_evento")): int(row["id"]) for row in rows}
    by_cpf_recibo = {(row["cpf"], row.get("nr_recibo")): int(row["id"]) for row in rows}

    out: list[dict[str, Any]] = []
    missing: list[str] = []
    for item in targets:
        event_id = (
            by_key.get((item["cpf"], item.get("source_recibo"), item.get("source_event_id")))
            or by_cpf_recibo.get((item["cpf"], item.get("source_recibo")))
        )
        if not event_id:
            missing.append(item["cpf"])
            continue
        out.append({**item, "evento_id": event_id})
    if missing:
        raise RuntimeError("explorador_eventos.id nao encontrado para: " + ", ".join(missing[:20]))
    return out


def _criar_timeline_envio_202(conn, total: int) -> tuple[int, int]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id FROM timeline_mes WHERE empresa_id=%s AND per_apur=%s",
            (internal_empresa_id, PER_APUR),
        )
        mes = cur.fetchone()
        if not mes:
            raise RuntimeError(f"timeline_mes nao existe para empresa={EMPRESA_ID} per_apur={PER_APUR}")
        mes_id = int(mes["id"])
        cur.execute(
            "SELECT COALESCE(MAX(sequencia), 0)+1 AS prox FROM timeline_envio WHERE timeline_mes_id=%s",
            (mes_id,),
        )
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
                    "rotulo": "correcao_agosto_202_deddepen",
                    "empresa_id_externo": EMPRESA_ID,
                    "per_apur": PER_APUR,
                    "ambiente": "producao",
                    "origem": str(MANIFEST),
                    "total_xmls_locais": total,
                    "regra": "dedDepen 202/1863: dependentes reais julho_setembro; valor 189.59",
                }),
            ),
        )
        envio_id = int(cur.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


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


def rodar(*, cert_path: Path, senha: str, cnpj: str) -> dict[str, Any]:
    targets = _load_targets()
    if not cert_path.exists():
        raise RuntimeError(f"certificado nao encontrado: {cert_path}")
    print(f"=> alvos: {len(targets)} XMLs S-1210 retificacao 202/dedDepen {PER_APUR}")
    print(f"=> certificado: {cert_path}")
    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        targets = _preencher_evento_id_numerico(conn_db, targets)
        envio_base._verificar_estado_atual(conn_db, targets)
        print("=> estado atual conferido: nenhum alvo esta com ultimo status sucesso")
        signed = envio_base._assinar_targets(targets, cert_path, senha)
        print(f"=> assinados localmente: {len(signed)} XMLs")
        envio_id, mes_id = _criar_timeline_envio_202(conn_db, len(signed))
        print(f"=> timeline_envio criado id={envio_id} timeline_mes={mes_id}")
        item_ids = envio_base._criar_items(conn_db, envio_id, signed)
        print(f"=> timeline_envio_item criados: {len(item_ids)}")
        envio_base._persistir_xmls_assinados(conn_db, conn_w, signed, item_ids)
        print("=> XMLs assinados gravados e vinculados aos items")

        sucesso_total = 0
        erro_total = 0
        protocolos: list[str] = []
        histograma: dict[str, int] = {}
        for idx in range(0, len(signed), envio_base.CFG_LOTE_MAX):
            lote = signed[idx:idx + envio_base.CFG_LOTE_MAX]
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

        status = "concluido"
        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status=status,
            sucesso=sucesso_total,
            erro=erro_total,
            resumo_extra={
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "rotulo_final": "correcao_agosto_202_deddepen",
                "cpfs": [item["cpf"] for item in signed],
            },
        )
        items = _summarize_items(conn_db, envio_id)
        print("\n=== RESUMO ENVIO CORRECAO AGOSTO 202 DEDDEPEN ===")
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
    parser.add_argument("--cert", default=str(DEFAULT_CERT))
    parser.add_argument("--cnpj", default="09445502000109")
    parser.add_argument("--senha", default=os.getenv("ESOCIAL_CERT_SENHA") or "")
    args = parser.parse_args(argv)
    senha = args.senha
    if not senha:
        senha = getpass.getpass("Senha do certificado A1 SOLUCOES: ")
    if not senha:
        raise SystemExit("Senha nao informada")
    rodar(cert_path=Path(args.cert), senha=senha, cnpj=args.cnpj)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
