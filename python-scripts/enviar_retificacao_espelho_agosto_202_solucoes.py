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
from app.xml_signer import S1010XMLSigner  # noqa: E402


EMPRESA_ID = 2
PER_APUR = "2025-08"
MANIFEST = ROOT / "relatorio_ana" / "CORRECAO_AGOSTO_202_DEDDEPEN" / "manifest_retificacao_espelho_agosto_202.json"
DEFAULT_CERT = ROOT / "_certificados_locais" / "SOLUCOES_SERVICOS_TERCEIRIZADOS_09445502000109.pfx"
CONFIRM_TOKEN = "RETIFICACAO_ESPELHO_105"
XLSX_RECEIPT_SOURCE = "RECIBOS_CORRETOS_35_SOLUCOES_AGOSTO_459.xlsx"


def _cpf_digits(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _xml_text(root: etree._Element, local_name: str) -> str:
    return str(root.xpath(f"string(//*[local-name()='{local_name}'])") or "").strip()


def _set_nr_recibo(xml_bytes: bytes, receipt: str) -> bytes:
    parser = etree.XMLParser(remove_blank_text=True, recover=False, huge_tree=True)
    root = etree.fromstring(xml_bytes, parser=parser)
    ide_evento = root.xpath('//*[local-name()="evtPgtos"]/*[local-name()="ideEvento"]')
    if not ide_evento:
        raise RuntimeError("ideEvento nao encontrado para aplicar override de nrRecibo")
    nodes = ide_evento[0].xpath('./*[local-name()="nrRecibo"]')
    if not nodes:
        raise RuntimeError("nrRecibo nao encontrado para aplicar override controlado")
    nodes[0].text = receipt
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=False)


def _load_targets(*, cpf: str | None = None, limit: int | None = None, allow_zip_receipts: bool = False, override_recibo: str | None = None, only_xlsx_receipts: bool = False) -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        raise RuntimeError(f"manifesto nao encontrado: {MANIFEST}")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("tipo") != "retificacao_espelho_dos_originais_202":
        raise RuntimeError(f"manifesto errado para esta rotina: tipo={data.get('tipo')}")

    targets: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in data.get("targets") or []:
        item_cpf = str(item.get("cpf") or "")
        xml_path = Path(item.get("xml") or "")
        if not item_cpf or not xml_path.exists():
            raise RuntimeError(f"target invalido ou XML nao encontrado: cpf={item_cpf} path={xml_path}")

        xml_bytes = xml_path.read_bytes()
        root = etree.fromstring(xml_bytes)
        event_ids = root.xpath("//*[local-name()='evtPgtos']/@Id")
        id_evento = str(event_ids[0]) if event_ids else ""
        if not id_evento:
            raise RuntimeError(f"Id evtPgtos nao encontrado para CPF {item_cpf}")
        if id_evento in seen_ids:
            raise RuntimeError(f"Id duplicado no manifesto: {id_evento}")
        seen_ids.add(id_evento)

        if _xml_text(root, "cpfBenef") != item_cpf:
            raise RuntimeError(f"CPF divergente em {xml_path}")
        if _xml_text(root, "indRetif") != "2":
            raise RuntimeError(f"XML de retificacao precisa indRetif=2 para CPF {item_cpf}")
        if _xml_text(root, "perApur") != PER_APUR:
            raise RuntimeError(f"perApur divergente para CPF {item_cpf}")
        if _xml_text(root, "nrRecibo") != item.get("nrRecibo"):
            raise RuntimeError(f"nrRecibo divergente para CPF {item_cpf}")
        if root.xpath("//*[local-name()='Signature']"):
            raise RuntimeError(f"XML unsigned ainda contem Signature antiga para CPF {item_cpf}")

        targets.append({
            **item,
            "evento_id": None,
            "nr_recibo": item["nrRecibo"],
        })

    targets = sorted(targets, key=lambda row: row["cpf"])
    if only_xlsx_receipts:
        targets = [item for item in targets if item.get("nrRecibo_fonte") == XLSX_RECEIPT_SOURCE]
        if len(targets) != 35:
            raise RuntimeError(f"esperado 35 alvos da planilha {XLSX_RECEIPT_SOURCE}; encontrado {len(targets)}")
    elif len(targets) != 105:
        raise RuntimeError(f"esperado 105 eventos de retificacao; encontrado {len(targets)}")
    selected_cpf = _cpf_digits(cpf)
    if selected_cpf:
        targets = [item for item in targets if item["cpf"] == selected_cpf]
        if not targets:
            raise RuntimeError(f"CPF nao encontrado no manifesto: {selected_cpf}")
    if limit is not None:
        if limit < 1:
            raise RuntimeError("limit deve ser >= 1")
        targets = targets[:limit]
    if not targets:
        raise RuntimeError("nenhum alvo selecionado")
    override_recibo = str(override_recibo or "").strip()
    if override_recibo:
        if not _cpf_digits(cpf) or len(targets) != 1:
            raise RuntimeError("--override-recibo exige --cpf e selecao de exatamente 1 alvo")
        if not override_recibo.startswith("1.1."):
            raise RuntimeError("--override-recibo deve ser um recibo eSocial iniciado por 1.1.")
        item = targets[0]
        item["nrRecibo_original_manifesto"] = item.get("nrRecibo")
        item["nrRecibo"] = override_recibo
        item["nr_recibo"] = override_recibo
        item["nrRecibo_fonte"] = "override_cli_usuario"
        item["xml_override_bytes"] = _set_nr_recibo(Path(item["xml"]).read_bytes(), override_recibo)
    zip_receipt_targets = [item["cpf"] for item in targets if str(item.get("nrRecibo_fonte") or "").startswith("source_nrRecibo_original_zip")]
    if zip_receipt_targets and not allow_zip_receipts:
        raise RuntimeError(
            "Abortado: alvo(s) usam recibo historico do ZIP, que falhou no teste 01987352190 com 401/459. "
            "Use --allow-zip-receipts apenas para teste controlado de poucos CPFs. CPFs: "
            + ", ".join(zip_receipt_targets[:20])
        )
    return targets


def _assinar_targets(targets: list[dict[str, Any]], cert_path: Path, senha: str) -> list[dict[str, Any]]:
    pfx_data = cert_path.read_bytes()
    signed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in targets:
        unsigned_xml = item.get("xml_override_bytes") or Path(item["xml"]).read_bytes()
        xml_assinado = S1010XMLSigner.assinar(unsigned_xml, pfx_data, senha)
        root = etree.fromstring(xml_assinado)
        event_ids = root.xpath("//*[local-name()='evtPgtos']/@Id")
        id_evento = str(event_ids[0]) if event_ids else ""
        if not id_evento:
            raise RuntimeError(f"Id nao encontrado apos assinatura para CPF {item['cpf']}")
        if id_evento in seen_ids:
            raise RuntimeError(f"Id duplicado apos assinatura: {id_evento}")
        seen_ids.add(id_evento)
        if _xml_text(root, "indRetif") != "2":
            raise RuntimeError(f"assinatura mudou indRetif para CPF {item['cpf']}")
        if not root.xpath("//*[local-name()='Signature']"):
            raise RuntimeError(f"assinatura nao inserida para CPF {item['cpf']}")
        signed.append({**item, "xml_assinado": xml_assinado, "id_evento_assinado": id_evento})
    return signed


def _criar_timeline_envio(conn, total: int) -> tuple[int, int]:
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
                    "rotulo": "retificacao_espelho_agosto_202_deddepen_105",
                    "empresa_id_externo": EMPRESA_ID,
                    "per_apur": PER_APUR,
                    "ambiente": "producao",
                    "origem": str(MANIFEST),
                    "total_xmls_locais": total,
                    "regra": "retificacao: base XML original 202, manter conteudo, indRetif=2 e nrRecibo",
                }),
            ),
        )
        envio_id = int(cur.fetchone()["id"])
    conn.commit()
    return envio_id, mes_id


def _latest_success_cpfs(cpfs: list[str]) -> list[str]:
    internal_empresa_id = tenant.internal_empresa_id(EMPRESA_ID)
    conn = db.connect(empresa_id=EMPRESA_ID)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (it.cpf)
                       it.cpf, it.status, it.criado_em, te.id AS envio_id
                  FROM timeline_envio_item it
                  JOIN timeline_envio te ON te.id=it.timeline_envio_id
                  JOIN timeline_mes tm ON tm.id=te.timeline_mes_id
                 WHERE tm.empresa_id=%s
                   AND tm.per_apur=%s
                   AND it.tipo_evento='S-1210'
                   AND it.cpf = ANY(%s)
                 ORDER BY it.cpf, it.criado_em DESC NULLS LAST, it.id DESC
                """,
                (internal_empresa_id, PER_APUR, cpfs),
            )
            return [str(row["cpf"]) for row in cur.fetchall() if row.get("status") == "sucesso"]
    finally:
        conn.close()


def _criar_items(conn, envio_id: int, signed: list[dict[str, Any]]) -> dict[str, int]:
    item_ids: dict[str, int] = {}
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for item in signed:
            cur.execute(
                """
                INSERT INTO timeline_envio_item
                  (timeline_envio_id, cpf, tipo_evento, status,
                   versao_anterior_id, nr_recibo_anterior, xml_enviado_oid)
                VALUES (%s, %s, 'S-1210', 'pendente', NULL, %s, NULL)
                RETURNING id
                """,
                (envio_id, item["cpf"], item["nr_recibo"]),
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


def dry_run(*, cpf: str | None = None, limit: int | None = None, allow_zip_receipts: bool = False, override_recibo: str | None = None, only_xlsx_receipts: bool = False) -> dict[str, Any]:
    targets = _load_targets(cpf=cpf, limit=limit, allow_zip_receipts=allow_zip_receipts, override_recibo=override_recibo, only_xlsx_receipts=only_xlsx_receipts)
    return {
        "ok": True,
        "dry_run": True,
        "total": len(targets),
        "manifest": str(MANIFEST),
        "primeiro_cpf": targets[0]["cpf"],
        "ultimo_cpf": targets[-1]["cpf"],
        "cpfs": [item["cpf"] for item in targets],
        "override_recibo": bool(override_recibo),
        "nr_recibos": [item["nr_recibo"] for item in targets],
        "only_xlsx_receipts": only_xlsx_receipts,
        "regra": "retificacao: XML original como base, indRetif=2, nrRecibo preenchido, conteúdo preservado",
    }


def rodar(*, cert_path: Path, senha: str, cnpj: str, cpf: str | None = None, limit: int | None = None, allow_zip_receipts: bool = False, override_recibo: str | None = None, allow_success_resend: bool = False, only_xlsx_receipts: bool = False) -> dict[str, Any]:
    targets = _load_targets(cpf=cpf, limit=limit, allow_zip_receipts=allow_zip_receipts, override_recibo=override_recibo, only_xlsx_receipts=only_xlsx_receipts)
    if not cert_path.exists():
        raise RuntimeError(f"certificado nao encontrado: {cert_path}")
    success_cpfs = _latest_success_cpfs([item["cpf"] for item in targets])
    if success_cpfs and not allow_success_resend:
        raise RuntimeError(
            "Abortado: ultimo status ja e sucesso para CPF(s): "
            + ", ".join(success_cpfs[:20])
            + ". Use --allow-success-resend somente para reteste manual controlado."
        )
    print(f"=> alvos: {len(targets)} XMLs S-1210 retificacao espelho 202 {PER_APUR}")
    print("=> modo: assinar XMLs unsigned de retificacao; conteudo vem do original")
    print(f"=> certificado: {cert_path}")
    signed = _assinar_targets(targets, cert_path, senha)
    print(f"=> assinados localmente: {len(signed)} XMLs")

    conn_db = db.connect(empresa_id=EMPRESA_ID)
    conn_w = db.connect(empresa_id=EMPRESA_ID)
    try:
        envio_id, mes_id = _criar_timeline_envio(conn_db, len(signed))
        print(f"=> timeline_envio criado id={envio_id} timeline_mes={mes_id}")
        item_ids = _criar_items(conn_db, envio_id, signed)
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

        envio_base._atualizar_envio(
            conn_db,
            envio_id,
            status="concluido",
            sucesso=sucesso_total,
            erro=erro_total,
            resumo_extra={
                "protocolos": protocolos,
                "histograma_erros": histograma,
                "rotulo_final": "retificacao_espelho_agosto_202_deddepen_105",
                "manifest": str(MANIFEST),
                "cpfs": [item["cpf"] for item in signed],
            },
        )
        items = _summarize_items(conn_db, envio_id)
        print("\n=== RESUMO RETIFICACAO ESPELHO AGOSTO 202 ===")
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
    parser.add_argument("--cpf", default="", help="envia somente este CPF")
    parser.add_argument("--limit", type=int, default=None, help="limita a quantidade de alvos selecionados")
    parser.add_argument("--allow-zip-receipts", action="store_true", help="permite teste com recibos historicos do ZIP")
    parser.add_argument("--override-recibo", default="", help="testa um CPF unico com este nrRecibo, sem alterar o manifesto")
    parser.add_argument("--allow-success-resend", action="store_true", help="permite reenviar CPF cujo ultimo status local ja e sucesso")
    parser.add_argument("--only-xlsx-receipts", action="store_true", help="seleciona somente os 35 recibos da planilha RECIBOS_CORRETOS_35_SOLUCOES_AGOSTO_459.xlsx")
    parser.add_argument("--cert", default=str(DEFAULT_CERT))
    parser.add_argument("--cnpj", default="09445502000109")
    parser.add_argument("--senha", default=os.getenv("ESOCIAL_CERT_SENHA") or "")
    args = parser.parse_args(argv)

    if not args.execute:
        print(json.dumps(dry_run(cpf=args.cpf, limit=args.limit, allow_zip_receipts=args.allow_zip_receipts, override_recibo=args.override_recibo, only_xlsx_receipts=args.only_xlsx_receipts), ensure_ascii=False, indent=2))
        return 0
    if args.confirmar != CONFIRM_TOKEN:
        raise SystemExit(f"Para enviar em producao, rode com --confirmar {CONFIRM_TOKEN}")

    senha = args.senha
    if not senha:
        senha = getpass.getpass("Senha do certificado A1 SOLUCOES: ")
    if not senha:
        raise SystemExit("Senha nao informada")
    rodar(cert_path=Path(args.cert), senha=senha, cnpj=args.cnpj, cpf=args.cpf, limit=args.limit, allow_zip_receipts=args.allow_zip_receipts, override_recibo=args.override_recibo, allow_success_resend=args.allow_success_resend, only_xlsx_receipts=args.only_xlsx_receipts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())