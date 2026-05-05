"""
Ingestor de XMLs eSocial locais para o DB de uma empresa.

Le uma pasta com arquivos *.S-XXXX.xml (formato resposta WsConsultarIdentificadores
com <retornoProcessamentoDownload><evento/><recibo/></retornoProcessamentoDownload>)
e popula:

  - explorador_importacoes (1 row por execucao)
  - explorador_eventos     (1 row por XML, idempotente por id_evento)
  - explorador_rubricas    (N rows por evento S-1210/S-1200)

Uso:
  python importer_xml_local.py --pasta "C:\\Users\\xandao\\Downloads\\solucoes\\_extracted\\01-2026" \\
                               --empresa-id 2 \\
                               --periodo 2026-01

Sem --periodo, infere do nome da pasta (ou deixa nulo).
Idempotencia: garantida via INDEX UNIQUE em explorador_eventos.id_evento
(criado automaticamente se nao existir).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterator, Optional

from lxml import etree
from psycopg2.extras import execute_values

# Permite rodar standalone (python importer_xml_local.py)
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from esocial.tenant import connect_for_empresa  # noqa: E402


RE_TIPO_EVT = re.compile(r"\.(S-\d+)\.xml$", re.IGNORECASE)
TIPOS_COM_RUBRICAS = {"S-1210", "S-1200"}


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def find_first(elem, local_name: str):
    """Acha primeiro descendente cujo local-name == local_name (qualquer ns)."""
    for el in elem.iter():
        if strip_ns(el.tag) == local_name:
            return el
    return None


def find_all(elem, local_name: str):
    return [el for el in elem.iter() if strip_ns(el.tag) == local_name]


def text_of(elem, local_name: str) -> Optional[str]:
    el = find_first(elem, local_name)
    if el is None:
        return None
    return (el.text or "").strip() or None


def elem_to_dict(elem) -> dict:
    """Serializa elemento XML para dict simples (recursivo)."""
    result: dict = {}
    for k, v in elem.attrib.items():
        result[f"@{strip_ns(k)}"] = v
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        if text and not result:
            return text  # type: ignore
        if text:
            result["#text"] = text
        return result
    for child in children:
        key = strip_ns(child.tag)
        sub = elem_to_dict(child)
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(sub)
        else:
            result[key] = sub
    return result


def parse_xml_file(path: Path) -> Optional[dict]:
    """Parseia 1 XML e devolve dict com campos extraidos.

    Returns None se o arquivo nao for um evento eSocial reconhecivel.
    """
    m = RE_TIPO_EVT.search(path.name)
    if not m:
        return None
    tipo_evento = m.group(1).upper()

    try:
        tree = etree.parse(str(path))
    except etree.XMLSyntaxError:
        return None
    root = tree.getroot()

    # Nó <evento> dentro de retornoProcessamentoDownload (ou root direto se for envelope diferente)
    evento_wrap = find_first(root, "evento")
    recibo_wrap = find_first(root, "recibo")

    # Dentro de <evento> ha um <eSocial> com o evento real (evtPgtos, evtRemun, etc)
    evt_root = evento_wrap if evento_wrap is not None else root

    # Id do evento: atributo Id="..." em algum descendente (evtPgtos/evtRemun/...)
    id_evento = None
    for el in evt_root.iter():
        if "Id" in el.attrib and strip_ns(el.tag).startswith("evt"):
            id_evento = el.attrib["Id"]
            break
    if id_evento is None:
        # fallback: qualquer Id="" no doc
        for el in evt_root.iter():
            if "Id" in el.attrib:
                id_evento = el.attrib["Id"]
                break

    cpf = (
        text_of(evt_root, "cpfBenef")
        or text_of(evt_root, "cpfTrab")
        or text_of(evt_root, "cpf")
    )
    per_apur = text_of(evt_root, "perApur") or text_of(evt_root, "perRef")

    # Recibo: dentro de <recibo><retornoEvento><recibo><nrRecibo>
    nr_recibo = None
    cd_resposta = None
    dt_proc = None
    rubricas: list[dict] = []
    if recibo_wrap is not None:
        # Pode ter aninhado <recibo><...><recibo><nrRecibo>...
        # Pegamos o ULTIMO nrRecibo encontrado (o mais interno)
        nrs = find_all(recibo_wrap, "nrRecibo")
        if nrs:
            nr_recibo = (nrs[-1].text or "").strip() or None
        cd_resposta = text_of(recibo_wrap, "cdResposta")
        dt_proc = text_of(recibo_wrap, "dhProcessamento")
        for r in find_all(recibo_wrap, "rubrica"):
            a = r.attrib
            try:
                vr = a.get("vrR") or a.get("vrRubr")
                vr_f = float(vr) if vr is not None else None
            except (TypeError, ValueError):
                vr_f = None
            rubricas.append(
                {
                    "cod_rubr": a.get("cdR"),
                    "ide_tab_rubr": a.get("idT"),
                    "nat_rubr": a.get("ntR"),
                    "tp_rubr": a.get("tpR"),
                    "cod_inc_irrf": a.get("inIR"),
                    "cod_inc_cp": a.get("inCP"),
                    "cod_inc_fgts": a.get("inFG"),
                    "vr_rubr": vr_f,
                    "ind_ap_ir": a.get("indApurIR") or a.get("indApIR"),
                    "_nrR": a.get("nrR"),
                    "_idE": a.get("idE"),
                    "_prA": a.get("prA"),
                }
            )

    dados = {
        "evento": elem_to_dict(evt_root) if evt_root is not None else None,
        "recibo": elem_to_dict(recibo_wrap) if recibo_wrap is not None else None,
    }

    return {
        "tipo_evento": tipo_evento,
        "id_evento": id_evento,
        "cpf": cpf,
        "per_apur": per_apur,
        "nr_recibo": nr_recibo,
        "cd_resposta": cd_resposta,
        "dt_processamento": dt_proc,
        "arquivo_origem": path.name,
        "dados_json": dados,
        "rubricas": rubricas,
    }


def ensure_unique_index(conn) -> None:
    """Cria UNIQUE INDEX em explorador_eventos.id_evento se nao existir."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_indexes WHERE schemaname='public' "
            "AND indexname='ux_explorador_eventos_id_evento'"
        )
        if cur.fetchone():
            return
        cur.execute(
            "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS "
            "ux_explorador_eventos_id_evento ON public.explorador_eventos (id_evento) "
            "WHERE id_evento IS NOT NULL"
        )
    conn.commit()


def iter_xmls(pasta: Path) -> Iterator[Path]:
    for p in pasta.rglob("*.xml"):
        if RE_TIPO_EVT.search(p.name):
            yield p


def importar(
    pasta: Path,
    empresa_id: int,
    periodo: Optional[str] = None,
    batch_size: int = 500,
    only: Optional[set[str]] = None,
) -> dict:
    conn = connect_for_empresa(empresa_id)
    conn.autocommit = False

    # CREATE INDEX CONCURRENTLY nao roda em transacao
    conn.autocommit = True
    try:
        ensure_unique_index(conn)
    except Exception as e:
        print(f"[warn] nao foi possivel garantir indice unico: {e}")
    conn.autocommit = False

    cur = conn.cursor()

    # 1. Cria importacao
    total_arquivos_estim = sum(1 for _ in iter_xmls(pasta))
    cur.execute(
        "INSERT INTO explorador_importacoes (pasta, periodo, total_arquivos, importado_em) "
        "VALUES (%s, %s, %s, NOW()) RETURNING id",
        (str(pasta), periodo, total_arquivos_estim),
    )
    importacao_id = cur.fetchone()[0]
    conn.commit()
    print(
        f"[importacao] id={importacao_id} pasta={pasta} periodo={periodo} "
        f"total={total_arquivos_estim}"
    )

    stats = {
        "lidos": 0,
        "inseridos": 0,
        "duplicados": 0,
        "erros": 0,
        "rubricas": 0,
        "por_tipo": {},
    }

    buf_eventos: list[tuple] = []
    buf_rubricas_pending: list[list[dict]] = []  # paralelo a buf_eventos

    def flush():
        if not buf_eventos:
            return
        # Insere eventos. ON CONFLICT (id_evento) WHERE id_evento NOT NULL DO NOTHING
        # Como WHERE em conflict precisa partial index, e ja temos -> usar id_evento
        sql = (
            "INSERT INTO explorador_eventos "
            "(importacao_id, tipo_evento, cpf, per_apur, nr_recibo, id_evento, "
            "dt_processamento, cd_resposta, arquivo_origem, dados_json, created_at) "
            "VALUES %s "
            "ON CONFLICT (id_evento) WHERE id_evento IS NOT NULL DO NOTHING "
            "RETURNING id, id_evento"
        )
        # execute_values nao suporta RETURNING bem com ON CONFLICT em algumas versoes,
        # entao iteramos.
        ids_inseridos: dict[str, int] = {}
        for tup, rubricas in zip(buf_eventos, buf_rubricas_pending):
            try:
                cur.execute(
                    "INSERT INTO explorador_eventos "
                    "(importacao_id, tipo_evento, cpf, per_apur, nr_recibo, id_evento, "
                    "dt_processamento, cd_resposta, arquivo_origem, dados_json, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW()) "
                    "ON CONFLICT (id_evento) WHERE id_evento IS NOT NULL "
                    "DO NOTHING RETURNING id",
                    tup,
                )
                row = cur.fetchone()
                if row:
                    stats["inseridos"] += 1
                    if rubricas:
                        ids_inseridos[str(row[0])] = row[0]
                        # bind rubricas a este evento_id
                        for rb in rubricas:
                            rb["_evento_id"] = row[0]
                else:
                    stats["duplicados"] += 1
            except Exception as e:
                stats["erros"] += 1
                conn.rollback()
                print(f"[err evento] {tup[8]}: {e}")
                continue

        # Agora insere rubricas em batch
        rub_rows = []
        for rubricas in buf_rubricas_pending:
            for rb in rubricas:
                eid = rb.get("_evento_id")
                if not eid:
                    continue
                rub_rows.append(
                    (
                        eid,
                        rb.get("cod_rubr"),
                        rb.get("ide_tab_rubr"),
                        rb.get("nat_rubr"),
                        rb.get("tp_rubr"),
                        rb.get("cod_inc_cp"),
                        rb.get("cod_inc_irrf"),
                        rb.get("cod_inc_fgts"),
                        rb.get("vr_rubr"),
                        rb.get("ind_ap_ir"),
                    )
                )
        if rub_rows:
            execute_values(
                cur,
                "INSERT INTO explorador_rubricas "
                "(evento_id, cod_rubr, ide_tab_rubr, nat_rubr, tp_rubr, "
                "cod_inc_cp, cod_inc_irrf, cod_inc_fgts, vr_rubr, ind_ap_ir) "
                "VALUES %s",
                rub_rows,
                page_size=1000,
            )
            stats["rubricas"] += len(rub_rows)

        conn.commit()
        buf_eventos.clear()
        buf_rubricas_pending.clear()

    t0 = time.time()
    last_print = t0

    for path in iter_xmls(pasta):
        stats["lidos"] += 1
        try:
            data = parse_xml_file(path)
        except Exception as e:
            stats["erros"] += 1
            print(f"[err parse] {path.name}: {e}")
            continue
        if data is None:
            continue
        tipo = data["tipo_evento"]
        if only and tipo not in only:
            continue
        stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1

        rubricas = data["rubricas"] if tipo in TIPOS_COM_RUBRICAS else []

        buf_eventos.append(
            (
                importacao_id,
                tipo,
                data["cpf"],
                data["per_apur"],
                data["nr_recibo"],
                data["id_evento"],
                data["dt_processamento"],
                data["cd_resposta"],
                data["arquivo_origem"],
                json.dumps(data["dados_json"], ensure_ascii=False),
            )
        )
        buf_rubricas_pending.append(rubricas)

        if len(buf_eventos) >= batch_size:
            flush()

        now = time.time()
        if now - last_print >= 5:
            print(
                f"  ... lidos={stats['lidos']} inseridos={stats['inseridos']} "
                f"dup={stats['duplicados']} rub={stats['rubricas']} "
                f"({stats['lidos']/(now-t0):.0f}/s)"
            )
            last_print = now

    flush()
    cur.close()
    conn.close()

    elapsed = time.time() - t0
    print()
    print(f"==== IMPORTACAO {importacao_id} CONCLUIDA em {elapsed:.1f}s ====")
    print(f"  lidos       = {stats['lidos']}")
    print(f"  inseridos   = {stats['inseridos']}")
    print(f"  duplicados  = {stats['duplicados']}")
    print(f"  erros       = {stats['erros']}")
    print(f"  rubricas    = {stats['rubricas']}")
    print(f"  por_tipo    = {stats['por_tipo']}")
    return stats


def _infer_periodo(pasta: Path) -> Optional[str]:
    name = pasta.name
    m = re.search(r"(\d{4})[-_](\d{2})", name)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(\d{2})[-_](\d{4})", name)
    if m:
        return f"{m.group(2)}-{m.group(1)}"
    return None


def main():
    ap = argparse.ArgumentParser(description="Importa XMLs eSocial locais para o DB.")
    ap.add_argument("--pasta", required=True, help="Pasta com XMLs (recursivo).")
    ap.add_argument("--empresa-id", type=int, required=True)
    ap.add_argument("--periodo", default=None, help="ex: 2026-01 (auto se omitido)")
    ap.add_argument("--batch-size", type=int, default=500)
    ap.add_argument(
        "--only",
        default=None,
        help="Filtra tipos (vírgula). Ex: S-1210,S-1200",
    )
    args = ap.parse_args()

    pasta = Path(args.pasta)
    if not pasta.exists():
        print(f"Pasta nao existe: {pasta}", file=sys.stderr)
        sys.exit(2)

    periodo = args.periodo or _infer_periodo(pasta)
    only = (
        {x.strip().upper() for x in args.only.split(",") if x.strip()}
        if args.only
        else None
    )

    importar(
        pasta=pasta,
        empresa_id=args.empresa_id,
        periodo=periodo,
        batch_size=args.batch_size,
        only=only,
    )


if __name__ == "__main__":
    main()
