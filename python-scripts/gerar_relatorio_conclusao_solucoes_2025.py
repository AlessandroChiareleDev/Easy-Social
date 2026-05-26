from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "relatorio_ana" / "RELATORIO_CONCLUSAO_ATIVIDADE_SOLUCOES_2025"
DATA_PATH = OUT_DIR / "dados_relatorio_conclusao.json"
HTML_PATH = OUT_DIR / "RELATORIO_CONCLUSAO_ATIVIDADE_EASY_SOCIAL_SOLUCOES_2025.html"

MONTH_LABELS = {
    "2025-02": "Fevereiro/2025",
    "2025-03": "Março/2025",
    "2025-04": "Abril/2025",
    "2025-05": "Maio/2025",
    "2025-06": "Junho/2025",
    "2025-07": "Julho/2025",
    "2025-08": "Agosto/2025",
    "2025-09": "Setembro/2025",
    "2025-10": "Outubro/2025",
    "2025-11": "Novembro/2025",
    "2025-12": "Dezembro/2025",
}


def br_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def month_rows(data: dict) -> str:
    rows = []
    for item in data["por_mes"]:
        month = item["per_apur"]
        fechamento = "Fechado" if item["s1299_fechado"] else "Aberto"
        rows.append(
            f"""
            <tr>
              <td>{MONTH_LABELS.get(month, month)}</td>
              <td class="num">{br_int(item["escopo"])}</td>
              <td class="num ok">{br_int(item["ok"])}</td>
              <td class="num zero">{br_int(item["erro"])}</td>
              <td class="num zero">{br_int(item["pendente"])}</td>
              <td><span class="pill success">{fechamento}</span></td>
            </tr>
            """
        )
    return "\n".join(rows)


def render_html(data: dict) -> str:
    totals = data["totais_finais_ultimo_status_por_cpf"]
    months_text = ", ".join(MONTH_LABELS[month].replace("/2025", "") for month in data["meses"])
    total_scope = br_int(totals["escopo"])
    total_ok = br_int(totals["ok"])
    total_error = br_int(totals["erro"])
    total_pending = br_int(totals["pendente"])
    closed_months = totals["meses_fechados"]

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Relatório de Conclusão de Atividade - Easy Social</title>
<style>
@page {{ size: A4; margin: 14mm; }}
@media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: #eef3fb;
  color: #111827;
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 12px;
  line-height: 1.45;
}}
.page {{
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #dbe5f3;
  box-shadow: 0 18px 45px rgba(13, 21, 48, 0.10);
}}
.topbar {{
  background: #0d1530;
  color: #ffffff;
  padding: 22px 26px 20px;
  border-bottom: 5px solid #0066ff;
}}
.brand-line {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}}
.brand {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 0;
}}
.mark {{
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0066ff, #37b7ff);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 900;
}}
.tag {{
  border: 1px solid rgba(255, 255, 255, 0.24);
  color: #cbd5e1;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 10px;
  text-transform: uppercase;
}}
h1 {{
  margin: 0;
  font-size: 27px;
  line-height: 1.12;
  letter-spacing: 0;
}}
.subtitle {{
  margin-top: 8px;
  color: #cbd5e1;
  font-size: 12px;
}}
.content {{ padding: 22px 26px 24px; }}
.hero-grid {{
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 14px;
  margin-bottom: 16px;
}}
.panel {{
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  padding: 14px;
}}
.panel.soft {{ background: #f8fbff; }}
.label {{
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 3px;
}}
.value {{ font-size: 13px; font-weight: 700; color: #0f172a; }}
.muted {{ color: #64748b; }}
.meta-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}}
.metric-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 16px 0 16px;
}}
.metric {{
  border: 1px solid #dbe7f6;
  background: #f8fbff;
  border-radius: 8px;
  padding: 13px 12px;
}}
.metric .k {{
  color: #64748b;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
}}
.metric .v {{
  margin-top: 7px;
  color: #0d1530;
  font-size: 24px;
  font-weight: 850;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}}
.metric.ok-card {{ border-color: #bfe6d0; background: #f3fbf6; }}
.metric.ok-card .v {{ color: #137a3a; }}
.metric.zero-card {{ border-color: #dbe7f6; background: #ffffff; }}
.section-title {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 18px 0 9px;
  color: #0d1530;
  font-size: 14px;
  font-weight: 800;
}}
.section-title::before {{
  content: "";
  width: 4px;
  height: 16px;
  background: #0066ff;
  border-radius: 99px;
}}
table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
th {{
  background: #eef4ff;
  color: #334155;
  border: 1px solid #dbe5f3;
  padding: 8px 9px;
  text-align: left;
  font-size: 10px;
  text-transform: uppercase;
}}
td {{ border: 1px solid #e2e8f0; padding: 8px 9px; }}
tr:nth-child(even) td {{ background: #fbfdff; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.ok {{ color: #137a3a; font-weight: 800; }}
.zero {{ color: #0d1530; font-weight: 800; }}
.pill {{
  display: inline-block;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 800;
}}
.pill.success {{ color: #137a3a; background: #e9f8ef; border: 1px solid #bfe6d0; }}
.note {{
  margin-top: 15px;
  border: 1px solid #fed7aa;
  background: #fff7ed;
  border-radius: 8px;
  padding: 12px 14px;
}}
.note-title {{ color: #9a3412; font-weight: 850; margin-bottom: 5px; }}
.conclusion {{
  margin-top: 14px;
  border-radius: 8px;
  background: #0d1530;
  color: #ffffff;
  padding: 15px 16px;
}}
.conclusion b {{ color: #7cc7ff; }}
.footer {{
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid #dbe5f3;
  margin-top: 16px;
  padding-top: 11px;
  color: #64748b;
  font-size: 10px;
}}
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
    <div class="subtitle">Reenvio massivo S-1210 e fechamento dos períodos 2025</div>
  </header>

  <section class="content">
    <div class="hero-grid avoid-break">
      <div class="panel soft">
        <div class="label">Empresa</div>
        <div class="value">SOLUÇÕES SERVIÇOS TERCEIRIZADOS LTDA</div>
        <div class="muted">CNPJ 09.445.502/0001-09</div>
      </div>
      <div class="panel">
        <div class="label">Status final</div>
        <div class="value">Atividade concluída</div>
        <div class="muted">{closed_months} meses fechados, janeiro fora do escopo</div>
      </div>
    </div>

    <div class="panel avoid-break">
      <div class="meta-grid">
        <div>
          <div class="label">Atividade tipificada</div>
          <div class="value">Reenvio massivo do evento S-1210</div>
        </div>
        <div>
          <div class="label">Meses processados</div>
          <div class="value">{months_text}/2025</div>
        </div>
        <div>
          <div class="label">Início do processamento</div>
          <div class="value">07/05/2026</div>
        </div>
        <div>
          <div class="label">Conclusão do processamento</div>
          <div class="value">20/05/2026</div>
        </div>
        <div>
          <div class="label">Horas totais de processamento</div>
          <div class="value">126 horas</div>
        </div>
        <div>
          <div class="label">Total em tokens extras consumidos para processamento da empresa</div>
          <div class="value">US$ 586,00</div>
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
      <div class="metric zero-card">
        <div class="k">Erros</div>
        <div class="v">{total_error}</div>
      </div>
      <div class="metric zero-card">
        <div class="k">Pendentes</div>
        <div class="v">{total_pending}</div>
      </div>
    </div>

    <div class="conclusion avoid-break">
      O processamento foi concluído com <b>100% do escopo final em OK</b>, sem erros reais e sem pendências operacionais nos meses de fevereiro a dezembro de 2025.
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

    <div class="note avoid-break">
      <div class="note-title">1.11 Observação técnica</div>
      Foi detectada anomalia nos arquivos originais da empresa envolvendo valores de dedução unitária de dependente acima do padrão legal esperado. O Easy Social não realizou readequação desses valores durante o reenvio, para não alterar bases de IR e demais efeitos tributários já transmitidos pela empresa. Para uma adequação futura às normas corretas, recomenda-se análise específica com a equipe Easy Social.
    </div>

    <div class="footer">
      <div>Easy Social - Relatório de conclusão de atividade</div>
      <div>Critério: último status S-1210 por CPF e por mês, com S-1299 fechado.</div>
    </div>
  </section>
</main>
</body>
</html>
"""


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    HTML_PATH.write_text(render_html(data), encoding="utf-8")
    print(HTML_PATH)


if __name__ == "__main__":
    main()