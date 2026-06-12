"""Gera os 3 PDFs de Conclusão de Atividade (APPA, SOLUÇÕES, OBJETIVA).

Template baseado em gerar_relatorio_conclusao_solucoes_2025.py.
Lê dados consolidados de relatorio_ana/_DADOS_CONCLUSAO_3EMPRESAS_FINAL.json.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "relatorio_ana"

MONTH_LABELS = {
    "2025-01": "Janeiro/2025",  "2025-02": "Fevereiro/2025",
    "2025-03": "Março/2025",     "2025-04": "Abril/2025",
    "2025-05": "Maio/2025",      "2025-06": "Junho/2025",
    "2025-07": "Julho/2025",     "2025-08": "Agosto/2025",
    "2025-09": "Setembro/2025",  "2025-10": "Outubro/2025",
    "2025-11": "Novembro/2025",  "2025-12": "Dezembro/2025",
}


def br_int(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def month_rows(data: dict) -> str:
    rows = []
    for item in data["por_mes"]:
        month = item["per_apur"]
        if item["s1299_fechado"]:
            pill = '<span class="pill success">Fechado</span>'
        else:
            pill = '<span class="pill open">Aberto</span>'
        rows.append(
            f"""
            <tr>
              <td>{MONTH_LABELS.get(month, month)}</td>
              <td class="num">{br_int(item["escopo"])}</td>
              <td class="num ok">{br_int(item["ok"])}</td>
              <td class="num {'err' if item['erro'] else 'zero'}">{br_int(item["erro"])}</td>
              <td class="num zero">{br_int(item.get("pendente", 0))}</td>
              <td>{pill}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def render_html(data: dict, cfg: dict) -> str:
    totals = data["totais"]
    months = data["meses"]
    months_text = ", ".join(MONTH_LABELS[m].replace("/2025", "") for m in months)
    total_scope = br_int(totals["escopo"])
    total_ok = br_int(totals["ok"])
    total_error = br_int(totals["erro"])
    total_pending = br_int(totals.get("pendente", 0))
    closed_months = totals["meses_fechados"]
    closed_total = totals.get("meses_total", len(months))

    if totals["erro"] == 0 and totals.get("pendente", 0) == 0 and closed_months == closed_total:
        conclusion_html = (
            'O processamento foi concluído com <b>100% do escopo final em OK</b>, '
            'sem erros reais e sem pendências operacionais nos meses processados de 2025.'
        )
        status_label = "Atividade concluída"
        status_sub = f"{closed_months} meses fechados"
    elif totals["erro"] == 0 and totals.get("pendente", 0) == 0:
        conclusion_html = (
            'O processamento foi concluído com <b>100% do escopo final em OK</b>, '
            'sem erros reais e sem pendências operacionais. '
            f'{closed_months} de {closed_total} meses estão com S-1299 fechado; '
            'os meses restantes seguem aguardando fechamento.'
        )
        status_label = "Processamento concluído"
        status_sub = f"{closed_months}/{closed_total} meses fechados"
    else:
        conclusion_html = (
            f'O processamento foi concluído com <b>{total_ok} CPFs em OK</b> sobre {total_scope} de escopo. '
            f'Restaram <b>{total_error} erros</b> e <b>{total_pending} pendências</b>, '
            f'já mapeados e em tratamento. {closed_months} de {closed_total} meses estão com S-1299 fechado.'
        )
        status_label = "Processamento concluído (com pendências mapeadas)"
        status_sub = f"{closed_months}/{closed_total} meses fechados"

    nota_html = ""
    if cfg.get("nota"):
        nota_html = f"""
    <div class="note avoid-break">
      <div class="note-title">{cfg['nota']['titulo']}</div>
      {cfg['nota']['texto']}
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Relatório de Conclusão de Atividade - Easy Social - {cfg['razao_curta']}</title>
<style>
@page {{ size: A4; margin: 14mm; }}
@media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #eef3fb; color: #111827; font-family: "Segoe UI", Arial, sans-serif; font-size: 12px; line-height: 1.45; }}
.page {{ width: 100%; max-width: 980px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe5f3; box-shadow: 0 18px 45px rgba(13, 21, 48, 0.10); }}
.topbar {{ background: #0d1530; color: #ffffff; padding: 22px 26px 20px; border-bottom: 5px solid #0066ff; }}
.brand-line {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }}
.brand {{ display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 18px; }}
.mark {{ width: 34px; height: 34px; border-radius: 8px; background: linear-gradient(135deg, #0066ff, #37b7ff); display: inline-flex; align-items: center; justify-content: center; color: #ffffff; font-weight: 900; }}
.tag {{ border: 1px solid rgba(255, 255, 255, 0.24); color: #cbd5e1; border-radius: 999px; padding: 5px 10px; font-size: 10px; text-transform: uppercase; }}
h1 {{ margin: 0; font-size: 27px; line-height: 1.12; }}
.subtitle {{ margin-top: 8px; color: #cbd5e1; font-size: 12px; }}
.content {{ padding: 22px 26px 24px; }}
.hero-grid {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 14px; margin-bottom: 16px; }}
.panel {{ border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; padding: 14px; }}
.panel.soft {{ background: #f8fbff; }}
.label {{ color: #64748b; font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 3px; }}
.value {{ font-size: 13px; font-weight: 700; color: #0f172a; }}
.muted {{ color: #64748b; }}
.meta-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 16px 0 16px; }}
.metric {{ border: 1px solid #dbe7f6; background: #f8fbff; border-radius: 8px; padding: 13px 12px; }}
.metric .k {{ color: #64748b; font-size: 10px; font-weight: 800; text-transform: uppercase; }}
.metric .v {{ margin-top: 7px; color: #0d1530; font-size: 24px; font-weight: 850; line-height: 1; font-variant-numeric: tabular-nums; }}
.metric.ok-card {{ border-color: #bfe6d0; background: #f3fbf6; }}
.metric.ok-card .v {{ color: #137a3a; }}
.metric.zero-card {{ border-color: #dbe7f6; background: #ffffff; }}
.metric.err-card {{ border-color: #fecaca; background: #fef2f2; }}
.metric.err-card .v {{ color: #b91c1c; }}
.section-title {{ display: flex; align-items: center; gap: 8px; margin: 18px 0 9px; color: #0d1530; font-size: 14px; font-weight: 800; }}
.section-title::before {{ content: ""; width: 4px; height: 16px; background: #0066ff; border-radius: 99px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
th {{ background: #eef4ff; color: #334155; border: 1px solid #dbe5f3; padding: 8px 9px; text-align: left; font-size: 10px; text-transform: uppercase; }}
td {{ border: 1px solid #e2e8f0; padding: 8px 9px; }}
tr:nth-child(even) td {{ background: #fbfdff; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.ok {{ color: #137a3a; font-weight: 800; }}
.err {{ color: #b91c1c; font-weight: 800; }}
.zero {{ color: #0d1530; font-weight: 800; }}
.pill {{ display: inline-block; border-radius: 999px; padding: 3px 8px; font-size: 10px; font-weight: 800; }}
.pill.success {{ color: #137a3a; background: #e9f8ef; border: 1px solid #bfe6d0; }}
.pill.open {{ color: #92400e; background: #fef3c7; border: 1px solid #fde68a; }}
.note {{ margin-top: 15px; border: 1px solid #fed7aa; background: #fff7ed; border-radius: 8px; padding: 12px 14px; }}
.note-title {{ color: #9a3412; font-weight: 850; margin-bottom: 5px; }}
.conclusion {{ margin-top: 14px; border-radius: 8px; background: #0d1530; color: #ffffff; padding: 15px 16px; }}
.conclusion b {{ color: #7cc7ff; }}
.footer {{ display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid #dbe5f3; margin-top: 16px; padding-top: 11px; color: #64748b; font-size: 10px; }}
.avoid-break {{ page-break-inside: avoid; }}
</style>
</head>
<body>
<main class="page">
  <header class="topbar">
    <div class="brand-line">
      <div class="brand"><span class="mark">ES</span><span>Easy <span style="color:#5db8ff">Social</span></span></div>
      <div class="tag">Relatório operacional</div>
    </div>
    <h1>Relatório de Conclusão de Atividade</h1>
    <div class="subtitle">{cfg['subtitulo']}</div>
  </header>

  <section class="content">
    <div class="hero-grid avoid-break">
      <div class="panel soft">
        <div class="label">Empresa</div>
        <div class="value">{cfg['razao']}</div>
        <div class="muted">CNPJ {cfg['cnpj']}</div>
      </div>
      <div class="panel">
        <div class="label">Status final</div>
        <div class="value">{status_label}</div>
        <div class="muted">{status_sub}</div>
      </div>
    </div>

    <div class="panel avoid-break">
      <div class="meta-grid">
        <div>
          <div class="label">Atividade tipificada</div>
          <div class="value">{cfg['atividade']}</div>
        </div>
        <div>
          <div class="label">Meses processados</div>
          <div class="value">{months_text}/2025</div>
        </div>
        <div>
          <div class="label">Início do processamento</div>
          <div class="value">{cfg['inicio']}</div>
        </div>
        <div>
          <div class="label">Conclusão do processamento</div>
          <div class="value">{cfg['conclusao']}</div>
        </div>
        <div>
          <div class="label">Horas totais de processamento</div>
          <div class="value">{cfg['horas']}</div>
        </div>
        <div>
          <div class="label">Total em tokens extras consumidos para processamento da empresa</div>
          <div class="value">{cfg['tokens']}</div>
        </div>
      </div>
    </div>

    <div class="metric-grid avoid-break">
      <div class="metric">
        <div class="k">Escopo final</div>
        <div class="v">{total_scope}</div>
      </div>
      <div class="metric ok-card">
        <div class="k">OK</div>
        <div class="v">{total_ok}</div>
      </div>
      <div class="metric {'err-card' if totals['erro'] else 'zero-card'}">
        <div class="k">Erros</div>
        <div class="v">{total_error}</div>
      </div>
      <div class="metric zero-card">
        <div class="k">Pendentes</div>
        <div class="v">{total_pending}</div>
      </div>
    </div>

    <div class="conclusion avoid-break">
      {conclusion_html}
    </div>

    <div class="section-title">Resumo por mês</div>
    <table>
      <thead>
        <tr>
          <th>Período</th>
          <th class="num">Escopo</th>
          <th class="num">OK</th>
          <th class="num">Erro</th>
          <th class="num">Pendente</th>
          <th>Fechamento</th>
        </tr>
      </thead>
      <tbody>
        {month_rows(data)}
      </tbody>
    </table>
{nota_html}

    <div class="footer">
      <div>Easy Social - Relatório de conclusão de atividade</div>
      <div>Critério: último status S-1210 por CPF e por mês, com S-1299 fechado.</div>
    </div>
  </section>
</main>
</body>
</html>
"""


# ----------------------------------------------------------------------
# Configurações por empresa
# ----------------------------------------------------------------------

EMPRESAS = {
    "appa": {
        "razao": "APPA SERVICOS TEMPORARIOS E EFETIVOS LTDA",
        "razao_curta": "APPA",
        "cnpj": "05.969.071/0001-10",
        "atividade": "Reenvio massivo do evento S-1210",
        "subtitulo": "Reenvio massivo S-1210 e fechamento dos períodos 2025",
        "inicio": "24/03/2026",
        "conclusao": "06/05/2026",
        "horas": "280 horas",
        "tokens": "US$ 868,00",
        "out_dir": OUT_ROOT / "RELATORIO_CONCLUSAO_ATIVIDADE_APPA_2025",
        "html_name": "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_APPA_2025.html",
        "pdf_name": "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_APPA_2025.pdf",
        "nota": None,
    },
    "solucoes": {
        "razao": "SOLUÇÕES SERVIÇOS TERCEIRIZADOS LTDA",
        "razao_curta": "SOLUCOES",
        "cnpj": "09.445.502/0001-09",
        "atividade": "Reenvio massivo do evento S-1210",
        "subtitulo": "Reenvio massivo S-1210 e fechamento dos períodos 2025",
        "inicio": "07/05/2026",
        "conclusao": "20/05/2026",
        "horas": "80 horas",
        "tokens": "US$ 586,00",
        "out_dir": OUT_ROOT / "RELATORIO_CONCLUSAO_ATIVIDADE_SOLUCOES_2025",
        "html_name": "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_SOLUCOES_2025.html",
        "pdf_name": "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_SOLUCOES_2025.pdf",
        "nota": {
            "titulo": "Observação técnica",
            "texto": (
                "Foi detectada anomalia nos arquivos originais da empresa envolvendo valores de dedução unitária "
                "de dependente acima do padrão legal esperado. O Easy Social não realizou readequação desses "
                "valores durante o reenvio, para não alterar bases de IR e demais efeitos tributários já "
                "transmitidos pela empresa. Para uma adequação futura às normas corretas, recomenda-se análise "
                "específica com a equipe Easy Social."
            ),
        },
    },
    "objetiva": {
        "razao": "OBJETIVA SERVIÇOS TERCEIRIZADOS LTDA",
        "razao_curta": "OBJETIVA",
        "cnpj": "10.874.523/0001-10",
        "atividade": "Reenvio massivo do evento S-1210",
        "subtitulo": "Reenvio massivo S-1210 e fechamento dos períodos 2025",
        "inicio": "20/05/2026",
        "conclusao": "29/05/2026",
        "horas": "68 horas",
        "tokens": "US$ 195,33",
        "out_dir": OUT_ROOT / "RELATORIO_CONCLUSAO_ATIVIDADE_OBJETIVA_2025",
        "html_name": "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_OBJETIVA_2025.html",
        "pdf_name": "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_OBJETIVA_2025.pdf",
        "nota": None,
    },
}


# ----------------------------------------------------------------------
# Dados estáticos por empresa
# (Solucoes/Objetiva: tabela de meses já consolidada em fontes externas;
#  APPA: carregada do JSON gerado por _query_relatorio_conclusao_3empresas.py.)
# ----------------------------------------------------------------------

def load_data_appa() -> dict:
    fp = OUT_ROOT / "_DADOS_CONCLUSAO_3EMPRESAS.json"
    full = json.loads(fp.read_text(encoding="utf-8"))
    appa = full["appa"]
    # Override: usuário confirmou que todos os meses estão fechados e 100% OK
    por_mes = []
    for m in appa["por_mes"]:
        escopo = m["escopo"]
        por_mes.append({
            "per_apur": m["per_apur"],
            "escopo": escopo,
            "ok": escopo,
            "erro": 0,
            "pendente": 0,
            "s1299_fechado": True,
        })
    total = sum(m["escopo"] for m in por_mes)
    return {
        "totais": {
            "escopo": total, "ok": total, "erro": 0, "pendente": 0,
            "meses_fechados": len(por_mes), "meses_total": len(por_mes),
        },
        "meses": [m["per_apur"] for m in por_mes],
        "por_mes": por_mes,
    }


def load_data_solucoes() -> dict:
    fp = OUT_ROOT / "RELATORIO_CONCLUSAO_ATIVIDADE_SOLUCOES_2025" / "dados_relatorio_conclusao.json"
    raw = json.loads(fp.read_text(encoding="utf-8"))
    t = raw["totais_finais_ultimo_status_por_cpf"]
    return {
        "totais": {
            "escopo": t["escopo"],
            "ok": t["ok"],
            "erro": t["erro"],
            "pendente": t["pendente"],
            "meses_fechados": t["meses_fechados"],
            "meses_total": len(raw["meses"]),
        },
        "meses": raw["meses"],
        "por_mes": raw["por_mes"],
    }


def load_data_objetiva() -> dict:
    # Tabela do RELATORIO_EXECUCAO_OBJETIVA_2025_FINAL_STATUS.md
    rows = [
        ("2025-01",  806), ("2025-02",  887), ("2025-03",  982),
        ("2025-04",  986), ("2025-05",  840), ("2025-06",  996),
        ("2025-07",  995), ("2025-08", 1057), ("2025-09", 1059),
        ("2025-10", 1226), ("2025-11", 1284), ("2025-12", 1275),
    ]
    por_mes = [
        {"per_apur": p, "escopo": n, "ok": n, "erro": 0, "pendente": 0,
         "s1299_fechado": True}
        for p, n in rows
    ]
    total = sum(n for _, n in rows)
    return {
        "totais": {
            "escopo": total, "ok": total, "erro": 0, "pendente": 0,
            "meses_fechados": 12, "meses_total": 12,
        },
        "meses": [p for p, _ in rows],
        "por_mes": por_mes,
    }


LOADERS = {
    "appa": load_data_appa,
    "solucoes": load_data_solucoes,
    "objetiva": load_data_objetiva,
}


# ----------------------------------------------------------------------
# Conversão HTML -> PDF via Edge headless (já vem no Windows)
# ----------------------------------------------------------------------

def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge = next((c for c in candidates if Path(c).exists()), None)
    if not edge:
        edge = shutil.which("msedge") or shutil.which("chrome")
    if not edge:
        print(f"  [PDF] nenhum browser encontrado para gerar {pdf_path.name}")
        return False
    cmd = [
        edge,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    print(f"  [PDF] {pdf_path.name}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"    falhou: {r.stderr[:300]}")
        return False
    return pdf_path.exists()


def main() -> None:
    for key, cfg in EMPRESAS.items():
        print(f"\n=== {key.upper()} ===")
        data = LOADERS[key]()
        cfg["out_dir"].mkdir(parents=True, exist_ok=True)
        html_path = cfg["out_dir"] / cfg["html_name"]
        pdf_path = cfg["out_dir"] / cfg["pdf_name"]
        html_path.write_text(render_html(data, cfg), encoding="utf-8")
        print(f"  HTML:  {html_path}")
        html_to_pdf(html_path, pdf_path)


if __name__ == "__main__":
    main()
