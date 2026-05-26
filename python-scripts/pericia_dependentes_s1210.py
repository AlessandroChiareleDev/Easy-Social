from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET


SOURCE_DIR = Path(r"C:\Users\xandao\Downloads\todos os meses 2025 SOLUCOES")
OUT_DIR = Path(r"C:\Users\xandao\Downloads\Relatorio_Pericia_Tecnica_Inconsistencia_Valor_Base_Unitario_Deducao_por_Dependente")
REPORT_NAME = "relatorio_pericia_tecnica_inconsistencia_valor_base_unitario_deducao_por_dependente.html"
UNIT_VALUE = Decimal("189.59")
MAX_PROOFS = 12
CANDIDATE_TARGET = 72
PRIORITY_MARKERS = ("2026-01", "2025-08", "2025-07", "2025-09", "2025-12")


@dataclass
class Evidence:
    index: int
    zip_name: str
    entry_name: str
    proof_file: str
    event_id: str
    per_apur: str
    cpf_benef: str
    cpf_dep_values: list[str]
    zero_dep_count: int
    ded_depen_values: list[str]
    repeated_dep_groups: list[str]
    max_ded_depen: str
    multiple_of_unit: str
    sha256: str
    warnings: list[str]
    snippet: str


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_of(root: ET.Element, wanted: str) -> str:
    for elem in root.iter():
        if local_name(elem.tag) == wanted and elem.text:
            return elem.text.strip()
    return ""


def texts_of(root: ET.Element, names: set[str]) -> list[str]:
    out: list[str] = []
    for elem in root.iter():
        if local_name(elem.tag) in names and elem.text:
            out.append(elem.text.strip())
    return out


def extract_tag(xml_text: str, tag: str) -> str:
    match = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml_text, re.DOTALL)
    return match.group(1).strip() if match else ""


def decimal_or_none(value: str) -> Decimal | None:
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def money(value: Decimal | str | None) -> str:
    if value is None:
        return "-"
    dec = value if isinstance(value, Decimal) else decimal_or_none(str(value))
    if dec is None:
        return str(value)
    return f"R$ {dec:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def is_zero_cpf(value: str) -> bool:
    cpf = normalize_cpf(value)
    return len(cpf) == 11 and set(cpf) == {"0"}


def is_bad_cpf(value: str) -> bool:
    cpf = normalize_cpf(value)
    return len(cpf) == 11 and len(set(cpf)) == 1


def find_warning_texts(xml_text: str) -> list[str]:
    snippets: list[str] = []
    for key in ["valor informado", "valor unit", "dependente", "deducao", "dedução"]:
        pos = xml_text.lower().find(key)
        if pos >= 0:
            snippets.append(xml_text[max(0, pos - 120):pos + 360].replace("\n", " ").strip())
    return snippets[:3]


def build_snippet(xml_text: str) -> str:
    keys = ["dedDepen", "cpfDep", "cpfDepen", "nrInscDep", "valor informado", "valor unit"]
    positions = [xml_text.find(k) for k in keys if xml_text.find(k) >= 0]
    if not positions:
        return xml_text[:900]
    start = max(0, min(positions) - 260)
    end = min(len(xml_text), max(positions) + 850)
    return xml_text[start:end]


def safe_proof_filename(index: int, per_apur: str, cpf: str, entry_name: str) -> str:
    stem = Path(entry_name).stem.replace(".", "_")
    return f"prova_{index:02d}_{per_apur}_{cpf}_{stem}.xml"


def ordered_zips() -> list[Path]:
    zips = sorted(SOURCE_DIR.glob("*.zip"))
    return sorted(
        zips,
        key=lambda p: (
            next((idx for idx, marker in enumerate(PRIORITY_MARKERS) if marker in p.name), 99),
            p.name,
        ),
    )


def iter_s1210_xmls() -> Iterable[tuple[str, str, bytes]]:
    for zip_path in ordered_zips():
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name_lower = info.filename.lower()
                if not name_lower.endswith(".xml"):
                    continue
                if ".s-1210" not in name_lower and "s-1210" not in name_lower:
                    continue
                yield zip_path.name, info.filename, zf.read(info)


def classify(xml_bytes: bytes, zip_name: str, entry_name: str) -> tuple[dict, str] | None:
    xml_text = xml_bytes.decode("utf-8", errors="ignore")
    if "evtPgtos" not in xml_text and "S-1210" not in entry_name:
        return None
    if "dedDepen" not in xml_text and "cpfDep" not in xml_text and "vlrDedDep" not in xml_text:
        return None

    cpf_benef = extract_tag(xml_text, "cpfBenef") or extract_tag(xml_text, "cpfTrab") or extract_tag(xml_text, "cpf")
    per_apur = extract_tag(xml_text, "perApur") or infer_per_apur(zip_name)
    event_match = re.search(r"<evtPgtos[^>]*\bId=['\"]([^'\"]+)", xml_text)
    event_id = event_match.group(1) if event_match else ""
    event_id = event_id or Path(entry_name).stem.split(".")[0]

    dep_blocks = re.findall(r"<dedDepen[^>]*>(.*?)</dedDepen>", xml_text, flags=re.DOTALL)
    cpf_dep_values: list[str] = []
    ded_depen_values: list[str] = []
    grouped: dict[str, Decimal] = {}
    grouped_counts: dict[str, int] = {}
    for block in dep_blocks:
        cpf_dep = (
            extract_tag(block, "cpfDep")
            or extract_tag(block, "cpfDepen")
            or extract_tag(block, "nrInscDep")
        )
        vlr = extract_tag(block, "vlrDedDep") or extract_tag(block, "vlrDedDepen") or extract_tag(block, "dedDepen")
        if cpf_dep:
            cpf_dep_values.append(cpf_dep)
        if vlr:
            ded_depen_values.append(vlr)
        dec = decimal_or_none(vlr)
        if cpf_dep and dec is not None:
            key = normalize_cpf(cpf_dep)
            grouped[key] = grouped.get(key, Decimal("0")) + dec
            grouped_counts[key] = grouped_counts.get(key, 0) + 1

    if not cpf_dep_values:
        cpf_dep_values = re.findall(r"<[^>]*(?:cpfDep|cpfDepen|nrInscDep)[^>]*>([^<]+)</", xml_text)
    if not ded_depen_values:
        ded_depen_values = re.findall(r"<[^>]*(?:vlrDedDep|vlrDedDepen)[^>]*>([^<]+)</", xml_text)

    ded_decimals = [d for d in (decimal_or_none(v) for v in ded_depen_values) if d is not None]
    grouped_high = {cpf: total for cpf, total in grouped.items() if total > UNIT_VALUE}
    repeated_groups = {
        cpf: total for cpf, total in grouped.items()
        if grouped_counts.get(cpf, 0) > 1 and total > UNIT_VALUE
    }
    zero_cpfs = [v for v in cpf_dep_values if is_zero_cpf(v)]
    repeated_cpfs = [v for v in cpf_dep_values if is_bad_cpf(v)]
    warnings = find_warning_texts(xml_text)

    if not grouped_high and not zero_cpfs and not repeated_cpfs:
        return None

    max_ded = max(grouped.values()) if grouped else (max(ded_decimals) if ded_decimals else Decimal("0"))
    multiple = (max_ded / UNIT_VALUE) if UNIT_VALUE and max_ded else Decimal("0")
    score = len(zero_cpfs) * 10 + len(repeated_cpfs) * 6 + len(grouped_high) * 4 + len(repeated_groups) * 8
    if max_ded >= UNIT_VALUE * 3:
        score += 8
    elif max_ded >= UNIT_VALUE * 2:
        score += 4
    return {
        "score": score,
        "zip_name": zip_name,
        "entry_name": entry_name,
        "event_id": event_id,
        "per_apur": per_apur,
        "cpf_benef": normalize_cpf(cpf_benef),
        "cpf_dep_values": cpf_dep_values,
        "zero_dep_count": len(zero_cpfs),
        "ded_depen_values": ded_depen_values,
        "repeated_dep_groups": [f"{cpf}: {total}" for cpf, total in sorted(repeated_groups.items())],
        "max_ded_depen": str(max_ded),
        "multiple_of_unit": f"{multiple:.2f}x",
        "warnings": warnings,
    }, xml_text


def infer_per_apur(zip_name: str) -> str:
    m = re.search(r"(20\d{2})-(\d{2})", zip_name)
    return f"{m.group(1)}-{m.group(2)}" if m else ""


def scan() -> tuple[list[Evidence], dict]:
    proofs_dir = OUT_DIR / "xmls_prova"
    proofs_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[tuple[int, dict, bytes, str]] = []
    total_s1210 = 0
    total_flagged = 0
    zips_seen: set[str] = set()

    for zip_name, entry_name, xml_bytes in iter_s1210_xmls():
        zips_seen.add(zip_name)
        total_s1210 += 1
        classified = classify(xml_bytes, zip_name, entry_name)
        if not classified:
            continue
        data, xml_text = classified
        total_flagged += 1
        candidates.append((int(data["score"]), data, xml_bytes, xml_text))
        has_zero = any(int(item[1]["zero_dep_count"]) > 0 for item in candidates)
        has_repeated = any(item[1]["repeated_dep_groups"] for item in candidates)
        if len(candidates) >= CANDIDATE_TARGET and has_zero and has_repeated:
            break

    candidates.sort(key=lambda item: (item[0], item[1]["per_apur"], item[1]["cpf_benef"]), reverse=True)
    zero_selected = [item for item in candidates if int(item[1]["zero_dep_count"]) > 0][:4]
    selected_keys = {(item[1]["zip_name"], item[1]["entry_name"]) for item in zero_selected}
    selected = zero_selected[:]
    for item in candidates:
        key = (item[1]["zip_name"], item[1]["entry_name"])
        if key in selected_keys:
            continue
        selected.append(item)
        selected_keys.add(key)
        if len(selected) >= MAX_PROOFS:
            break

    evidences: list[Evidence] = []
    for idx, (_score, data, xml_bytes, xml_text) in enumerate(selected, 1):
        proof_name = safe_proof_filename(idx, data["per_apur"], data["cpf_benef"], data["entry_name"])
        proof_path = proofs_dir / proof_name
        proof_path.write_bytes(xml_bytes)
        evidences.append(Evidence(
            index=idx,
            zip_name=data["zip_name"],
            entry_name=data["entry_name"],
            proof_file=f"xmls_prova/{proof_name}",
            event_id=data["event_id"],
            per_apur=data["per_apur"],
            cpf_benef=data["cpf_benef"],
            cpf_dep_values=data["cpf_dep_values"][:10],
            zero_dep_count=int(data["zero_dep_count"]),
            ded_depen_values=data["ded_depen_values"][:10],
            repeated_dep_groups=data["repeated_dep_groups"][:10],
            max_ded_depen=data["max_ded_depen"],
            multiple_of_unit=data["multiple_of_unit"],
            sha256=hashlib.sha256(xml_bytes).hexdigest(),
            warnings=data["warnings"],
            snippet=build_snippet(xml_text),
        ))

    summary = {
        "source_dir": str(SOURCE_DIR),
        "out_dir": str(OUT_DIR),
        "zip_count": len(list(SOURCE_DIR.glob("*.zip"))),
        "zips_with_s1210": len(zips_seen),
        "total_s1210_scanned": total_s1210,
        "total_flagged": total_flagged,
        "selected": len(evidences),
        "scan_mode": "prioritario_com_parada_por_evidencia",
        "priority_markers": list(PRIORITY_MARKERS),
        "unit_value": str(UNIT_VALUE),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return evidences, summary


def rel(path: Path) -> str:
    return path.as_posix()


def badge(text: str, cls: str = "") -> str:
    return f'<span class="badge {cls}">{html.escape(text)}</span>'


def render_html(evidences: list[Evidence], summary: dict) -> str:
    rows = []
    cards = []
    for ev in evidences:
        cpfs = ", ".join(ev.cpf_dep_values[:4]) or "sem cpfDep explicito"
        ded = ", ".join(money(v) for v in ev.ded_depen_values[:4]) or "sem dedDepen explicito"
        repeated = "; ".join(ev.repeated_dep_groups[:3]) or "sem repeticao agregada"
        warning_text = "<br>".join(html.escape(w) for w in ev.warnings) or "Advertencia/critica nao textual no XML original; inconsistencia apurada pelos campos do proprio evento."
        rows.append(f"""
        <tr>
          <td>#{ev.index:02d}</td>
          <td><strong>{html.escape(ev.per_apur)}</strong><br><span>{html.escape(ev.cpf_benef)}</span></td>
          <td>{html.escape(cpfs)}<br>{badge(str(ev.zero_dep_count) + ' CPF zerado(s)', 'danger') if ev.zero_dep_count else badge('dependente repetido', 'warn')}</td>
          <td><strong>{money(ev.max_ded_depen)}</strong><br><span>{html.escape(ev.multiple_of_unit)} do valor unitario ({money(UNIT_VALUE)})</span><br><small>{html.escape(repeated)}</small></td>
          <td><a href="{html.escape(ev.proof_file)}" download>Abrir XML</a><br><small>{html.escape(ev.zip_name)}</small></td>
        </tr>
        """)
        cards.append(f"""
        <article class="proof-card">
          <div class="proof-top">
            <span class="proof-index">Prova {ev.index:02d}</span>
            <a class="proof-download" href="{html.escape(ev.proof_file)}" download>Baixar XML original</a>
          </div>
          <h3>{html.escape(ev.per_apur)} · CPF trabalhador {html.escape(ev.cpf_benef)}</h3>
          <p class="muted">Origem: {html.escape(ev.zip_name)} · {html.escape(ev.entry_name)}</p>
          <div class="mini-grid">
            <div><span>Valor unitario legal usado na critica</span><strong>{money(UNIT_VALUE)}</strong></div>
            <div><span>Maior deducao encontrada</span><strong>{money(ev.max_ded_depen)}</strong></div>
            <div><span>Multiplo do unitario</span><strong>{html.escape(ev.multiple_of_unit)}</strong></div>
            <div><span>CPF dependente zerado</span><strong>{ev.zero_dep_count}</strong></div>
          </div>
                    <p class="muted">Dependentes repetidos/soma por CPF: {html.escape(repeated)}</p>
          <p class="warning-text">{warning_text}</p>
          <details>
            <summary>Trecho tecnico do XML</summary>
            <pre>{html.escape(ev.snippet[:1800])}</pre>
          </details>
          <p class="hash">SHA-256: {html.escape(ev.sha256)}</p>
        </article>
        """)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatorio Pericia Tecnica - Inconsistencia Valor Base Unitario de Deducao por Dependente</title>
<style>
:root {{
  --bg: #090d14;
  --panel: rgba(17, 24, 39, 0.82);
  --panel-2: rgba(13, 28, 24, 0.72);
  --line: rgba(255,255,255,0.12);
  --text: #f6f7fb;
  --muted: #9aa4b2;
  --green: #39ff70;
  --pink: #f0d1e5;
  --amber: #ffb020;
  --red: #ff5c7a;
  --blue: #8ab8ff;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Arial, sans-serif;
  background:
    radial-gradient(circle at 18% 12%, rgba(240,209,229,0.18), transparent 28%),
    radial-gradient(circle at 85% 8%, rgba(57,255,112,0.10), transparent 24%),
    linear-gradient(180deg, #080b11 0%, #0c1018 48%, #070a10 100%);
  color: var(--text);
  line-height: 1.5;
}}
a {{ color: var(--green); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.page {{ max-width: 1180px; margin: 0 auto; padding: 42px 24px 72px; }}
.hero {{
  border: 1px solid var(--line);
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(57,255,112,0.04));
  border-radius: 18px;
  padding: 34px;
  box-shadow: 0 30px 90px rgba(0,0,0,0.40), inset 0 1px 0 rgba(255,255,255,0.16);
}}
.eyebrow {{ color: var(--green); letter-spacing: .16em; font-size: 12px; font-weight: 800; text-transform: uppercase; }}
h1 {{ font-size: clamp(30px, 5vw, 58px); line-height: 1.02; margin: 12px 0 16px; letter-spacing: 0; }}
.lead {{ max-width: 820px; color: #dbe2ee; font-size: 18px; }}
.stamp {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 24px; }}
.badge {{ display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: 999px; padding: 7px 11px; color: #dbe2ee; background: rgba(255,255,255,0.06); font-weight: 700; font-size: 12px; }}
.badge.danger {{ color: #ffd1da; border-color: rgba(255,92,122,.42); background: rgba(255,92,122,.12); }}
.badge.warn {{ color: #ffe4ad; border-color: rgba(255,176,32,.42); background: rgba(255,176,32,.10); }}
.badge.ok {{ color: #c8ffd6; border-color: rgba(57,255,112,.42); background: rgba(57,255,112,.10); }}
.section {{ margin-top: 26px; }}
.grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }}
.metric {{ border: 1px solid var(--line); background: var(--panel); border-radius: 14px; padding: 18px; }}
.metric span {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .12em; }}
.metric strong {{ display: block; font-size: 30px; margin-top: 8px; }}
.verdict {{ border: 1px solid rgba(57,255,112,.35); background: linear-gradient(135deg, rgba(57,255,112,.10), rgba(240,209,229,.06)); border-radius: 16px; padding: 22px; }}
.verdict h2, .section h2 {{ margin: 0 0 12px; font-size: 24px; }}
.verdict p {{ margin: 0; color: #dbe2ee; max-width: 920px; }}
.table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 14px; background: rgba(255,255,255,0.04); }}
table {{ width: 100%; border-collapse: collapse; min-width: 880px; }}
th {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .12em; text-align: left; padding: 14px; border-bottom: 1px solid var(--line); }}
td {{ padding: 14px; border-bottom: 1px solid rgba(255,255,255,.08); vertical-align: top; }}
td span, small, .muted {{ color: var(--muted); }}
.proof-card {{ border: 1px solid var(--line); background: var(--panel); border-radius: 16px; padding: 22px; margin-top: 14px; }}
.proof-top {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
.proof-index {{ color: var(--green); font-size: 12px; font-weight: 900; letter-spacing: .14em; text-transform: uppercase; }}
.proof-download {{ border: 1px solid rgba(57,255,112,.35); border-radius: 10px; padding: 8px 12px; background: rgba(57,255,112,.08); font-weight: 800; }}
.proof-card h3 {{ margin: 12px 0 4px; font-size: 21px; }}
.mini-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 16px 0; }}
.mini-grid div {{ border: 1px solid var(--line); border-radius: 12px; padding: 12px; background: rgba(0,0,0,.22); }}
.mini-grid span {{ color: var(--muted); display: block; font-size: 12px; }}
.mini-grid strong {{ display: block; margin-top: 6px; color: var(--pink); font-size: 18px; }}
.warning-text {{ color: #ffd9a6; border-left: 3px solid var(--amber); padding-left: 12px; }}
details {{ margin-top: 14px; }}
summary {{ cursor: pointer; color: var(--blue); font-weight: 800; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #05070b; border: 1px solid rgba(255,255,255,.10); border-radius: 12px; padding: 14px; color: #d8e5ff; max-height: 340px; overflow: auto; }}
.hash {{ font-family: Consolas, ui-monospace, monospace; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
.footer {{ margin-top: 34px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--line); padding-top: 18px; }}
@media (max-width: 900px) {{ .grid, .mini-grid {{ grid-template-columns: 1fr 1fr; }} .hero {{ padding: 24px; }} }}
@media (max-width: 620px) {{ .grid, .mini-grid {{ grid-template-columns: 1fr; }} .page {{ padding: 24px 14px; }} }}
</style>
</head>
<body>
<main class="page">
  <section class="hero">
    <div class="eyebrow">Relatorio de pericia tecnica</div>
    <h1>Inconsistencia no valor base unitario de deducao por dependente</h1>
    <p class="lead">Evidencias extraidas exclusivamente dos XMLs originais baixados do eSocial nos arquivos quinzenais de SOLUCOES. O objetivo e demonstrar que as inconsistencias ja constavam na origem: CPF de dependente zerado/invalido e deducao por dependente acima do valor unitario.</p>
    <div class="stamp">
      {badge('Fonte: ZIPs quinzenais locais', 'ok')}
      {badge('Sem consulta ao eSocial')}
      {badge('Gerado em ' + summary['generated_at'])}
    </div>
  </section>

  <section class="section grid">
    <div class="metric"><span>ZIPs disponiveis</span><strong>{summary['zip_count']}</strong></div>
    <div class="metric"><span>S-1210 lidos</span><strong>{summary['total_s1210_scanned']:,}</strong></div>
    <div class="metric"><span>Eventos com indicio</span><strong>{summary['total_flagged']:,}</strong></div>
    <div class="metric"><span>Provas anexadas</span><strong>{summary['selected']}</strong></div>
  </section>

  <section class="section verdict">
    <h2>Conclusao objetiva</h2>
    <p>As amostras anexadas mostram S-1210 originais contendo deducao de dependente superior ao valor unitario de {money(UNIT_VALUE)} e/ou CPF de dependente zerado. Portanto, o erro nao foi criado pelo processo de retificacao: a retificacao apenas retransmitiu valores e estruturas que ja estavam presentes nos XMLs originais.</p>
  </section>

  <section class="section">
    <h2>Mapa das provas</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Prova</th><th>Periodo / CPF</th><th>Dependente</th><th>Deducao</th><th>Arquivo</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </section>

  <section class="section">
    <h2>XMLs originais anexados</h2>
    {''.join(cards)}
  </section>

  <section class="section verdict">
    <h2>Encaminhamento tecnico</h2>
    <p>Para preservar a rastreabilidade fiscal, a recomendacao tecnica e nao recalcular nem substituir valores de deducao existentes nos XMLs originais. Havendo divergencia material nos descontos/dependentes, a correcao deve partir da folha/origem da empresa, pois alterar o S-1210 isoladamente pode alterar bases de IR e gerar diferencas indevidas.</p>
  </section>

  <div class="footer">
    Pasta de origem: {html.escape(summary['source_dir'])}<br>
    Pasta de evidencias: {html.escape(summary['out_dir'])}<br>
    Relatorio gerado localmente a partir dos arquivos ZIP indicados pelo usuario.
  </div>
</main>
</body>
</html>
"""


def main() -> None:
    if not SOURCE_DIR.exists():
        raise SystemExit(f"Fonte nao encontrada: {SOURCE_DIR}")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    evidences, summary = scan()
    html_text = render_html(evidences, summary)
    report_path = OUT_DIR / REPORT_NAME
    report_path.write_text(html_text, encoding="utf-8")
    (OUT_DIR / "manifesto_evidencias.json").write_text(
        json.dumps({"summary": summary, "evidences": [asdict(e) for e in evidences]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"report": str(report_path), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()