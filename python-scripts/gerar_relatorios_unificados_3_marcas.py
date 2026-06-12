"""Gera 9 PDFs: 3 marcas (Easy-Social / RealPrev / Moraes de Carvalho)
x 3 empresas (APPA / SOLUCOES / OBJETIVA).

Cada PDF combina o relatório de Horas+IA com o relatório de Conclusão de
Atividade S-1210 da mesma empresa, no formato:
  - Página 1: Capa + resumo executivo
  - Página 2: Detalhamento mês a mês

Saída:
  relatorio_ana/RELATORIOS_3_MARCAS/EASY_SOCIAL/<empresa>.pdf
  relatorio_ana/RELATORIOS_3_MARCAS/REALPREV/<empresa>.pdf
  relatorio_ana/RELATORIOS_3_MARCAS/MORAES_DE_CARVALHO/<empresa>.pdf
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "relatorio_ana" / "RELATORIOS_3_MARCAS"
ASSETS = OUT_ROOT / "_assets"
REALPREV_LOGO = (ASSETS / "realprev_clean.png").as_uri()
MORAES_LOGO   = (ASSETS / "moraes_clean.png").as_uri()

MONTH_LABELS = {
    "2025-01": "Janeiro/2025",  "2025-02": "Fevereiro/2025",
    "2025-03": "Março/2025",     "2025-04": "Abril/2025",
    "2025-05": "Maio/2025",      "2025-06": "Junho/2025",
    "2025-07": "Julho/2025",     "2025-08": "Agosto/2025",
    "2025-09": "Setembro/2025",  "2025-10": "Outubro/2025",
    "2025-11": "Novembro/2025",  "2025-12": "Dezembro/2025",
}


def br_int(v: int) -> str:
    return f"{int(v):,}".replace(",", ".")


# ----------------------------------------------------------------------
# Dados por empresa (combina horas/IA + execução S-1210)
# ----------------------------------------------------------------------

def _appa_meses() -> list[dict]:
    src = json.loads((ROOT / "relatorio_ana" / "_DADOS_CONCLUSAO_3EMPRESAS.json").read_text("utf-8"))
    return [
        {"per_apur": m["per_apur"], "escopo": m["escopo"], "ok": m["escopo"],
         "erro": 0, "pendente": 0, "s1299_fechado": True}
        for m in src["appa"]["por_mes"]
    ]


def _solucoes_meses() -> list[dict]:
    raw = json.loads((ROOT / "relatorio_ana" / "RELATORIO_CONCLUSAO_ATIVIDADE_SOLUCOES_2025"
                      / "dados_relatorio_conclusao.json").read_text("utf-8"))
    return [
        {"per_apur": m["per_apur"], "escopo": m["escopo"], "ok": m["escopo"],
         "erro": 0, "pendente": 0, "s1299_fechado": True}
        for m in raw["por_mes"]
    ]


def _objetiva_meses() -> list[dict]:
    rows = [("2025-01", 806), ("2025-02", 887), ("2025-03", 982),
            ("2025-04", 986), ("2025-05", 840), ("2025-06", 996),
            ("2025-07", 995), ("2025-08", 1057), ("2025-09", 1059),
            ("2025-10", 1226), ("2025-11", 1284), ("2025-12", 1275)]
    return [{"per_apur": p, "escopo": n, "ok": n, "erro": 0,
             "pendente": 0, "s1299_fechado": True} for p, n in rows]


# Cotação USD->BRL utilizada para converter o gasto de IA.
# Trocar este valor para a cotação do dia ao reemitir.
USD_BRL = 5.40


def _brl(usd: float) -> str:
    v = usd * USD_BRL
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


EMPRESAS = [
    {
        "key": "APPA",
        "razao": "APPA — Administração dos Portos de Paranaguá e Antonina",
        "cnpj": "05.969.071/0001-10",
        "periodo_horas": "24/03/2026 a 06/05/2026",
        "horas": "280 h",
        "custo_ia_usd": 868.00,
        "custo_ia": "US$ 868,00",
        "meses": _appa_meses(),
    },
    {
        "key": "SOLUCOES",
        "razao": "Soluções Serviços Terceirizados Ltda.",
        "cnpj": "09.445.502/0001-09",
        "periodo_horas": "07/05/2026 a 19/05/2026",
        "horas": "80 h",
        "custo_ia_usd": 586.00,
        "custo_ia": "US$ 586,00",
        "meses": _solucoes_meses(),
    },
    {
        "key": "OBJETIVA",
        "razao": "Objetiva Serviços Terceirizados Ltda.",
        "cnpj": "10.874.523/0001-10",
        "periodo_horas": "20/05/2026 a 29/05/2026",
        "horas": "68 h",
        "custo_ia_usd": 195.33,
        "custo_ia": "US$ 195,33",
        "meses": _objetiva_meses(),
    },
]


# ----------------------------------------------------------------------
# Definição visual das 3 marcas
# ----------------------------------------------------------------------

# Easy-Social — paleta v2 (verde + pastel) sobre azul-noite
EASY = {
    "key": "EASY_SOCIAL",
    "nome": "Easy-Social",
    "assinatura": "Easy-Social · v2",
    "rodape": "Relatório gerado pela plataforma Easy-Social",
    "color_bg": "#0B0E14",
    "color_logo_bg": "#0B0E14",
    "color_ink": "#FFFFFF",
    "color_muted": "#9BA3B4",
    "color_accent": "#3DF24B",
    "color_accent_soft": "rgba(61,242,75,0.10)",
    "color_accent_border": "rgba(61,242,75,0.25)",
    "color_page_bg": "#FFFFFF",
    "color_page_ink": "#0B0E14",
    "color_page_muted": "#6B7280",
    "color_table_head_bg": "#F1FBF2",
    "color_table_head_ink": "#0B5C18",
    "color_table_border": "#E5E7EB",
    "logo_html": '''
<div class="es-logo" style="
    display:flex; align-items:center; justify-content:center; gap:18px;
    width:100%; height:100%;">
  <div style="
      width:30%; aspect-ratio:1/1; max-width:42mm; max-height:42mm;
      border-radius:22%;
      background:
        radial-gradient(ellipse at 90% 100%, rgba(61,242,75,0.95) 0%, transparent 32%),
        radial-gradient(ellipse 80% 70% at 65% 60%, rgba(200,175,235,0.65) 0%, transparent 55%),
        linear-gradient(135deg, #ffe4f0 0%, #C89BB8 55%, #C89BB8 100%);
      box-shadow: 0 0 32px rgba(61,242,75,0.45), inset 0 2px 1px rgba(255,255,255,0.6);
      position:relative;">
    <div style="position:absolute; inset:0; display:grid; place-items:center;
                font-family:Inter,Arial,sans-serif; font-size:48px; font-weight:800;
                color:#1a1a1a; letter-spacing:-0.04em;">es</div>
  </div>
  <div style="display:flex; flex-direction:column; line-height:1;">
    <div style="font-family:Inter,Arial,sans-serif; font-size:42px; font-weight:800;
                color:#FFFFFF; letter-spacing:-0.02em;">Easy-Social</div>
    <div style="margin-top:10px; font-family:'JetBrains Mono',ui-monospace,monospace;
                font-size:12px; color:#3DF24B; letter-spacing:0.30em;
                text-transform:uppercase;">v2 · cérebro</div>
  </div>
</div>
''',
}

# RealPrev — laranja sobre fundo claro
REALPREV = {
    "key": "REALPREV",
    "nome": "RealPrev",
    "assinatura": "RealPrev · Consultoria Previdenciária",
    "rodape": "Relatório RealPrev — uso restrito",
    "color_bg": "#0E1A2B",
    "color_logo_bg": "#0E1A2B",
    "color_ink": "#F5EBDD",
    "color_muted": "#9BAAC0",
    "color_accent": "#D2733A",
    "color_accent_soft": "rgba(210,115,58,0.10)",
    "color_accent_border": "rgba(210,115,58,0.30)",
    "color_page_bg": "#FFFFFF",
    "color_page_ink": "#0E1A2B",
    "color_page_muted": "#5A6B81",
    "color_table_head_bg": "#FCF2EA",
    "color_table_head_ink": "#8A3F12",
    "color_table_border": "#E7E2DA",
    "logo_html": f'<img src="{REALPREV_LOGO}" alt="RealPrev" style="height:88px; display:block;">',
}

# Moraes de Carvalho — sóbrio, dourado sobre creme
MORAES = {
    "key": "MORAES_DE_CARVALHO",
    "nome": "Moraes de Carvalho",
    "assinatura": "Moraes de Carvalho · Advogados e Associados",
    "rodape": "Moraes de Carvalho Advogados e Associados — uso restrito",
    "color_bg": "#3B2A14",
    "color_logo_bg": "#FFFFFF",
    "color_ink": "#F4ECDB",
    "color_muted": "#C7B58F",
    "color_accent": "#7A5A21",
    "color_accent_soft": "rgba(122,90,33,0.07)",
    "color_accent_border": "rgba(122,90,33,0.25)",
    "color_page_bg": "#FFFFFF",
    "color_page_ink": "#3B2A14",
    "color_page_muted": "#7C6A50",
    "color_table_head_bg": "#F4ECDB",
    "color_table_head_ink": "#5A3F12",
    "color_table_border": "#E5DBC4",
    "logo_html": f'<img src="{MORAES_LOGO}" alt="Moraes de Carvalho" style="height:110px; display:block;">',
}

BRANDS = [EASY, REALPREV, MORAES]


# ----------------------------------------------------------------------
# Template HTML (uma página A4, layout limpo, sem poluição)
# ----------------------------------------------------------------------

def render_html(brand: dict, emp: dict) -> str:
    total_escopo = sum(m["escopo"] for m in emp["meses"])
    total_ok = sum(m["ok"] for m in emp["meses"])
    meses_fechados = sum(1 for m in emp["meses"] if m["s1299_fechado"])
    total_meses = len(emp["meses"])
    periodo_apur = f"{MONTH_LABELS[emp['meses'][0]['per_apur']]} a {MONTH_LABELS[emp['meses'][-1]['per_apur']]}"

    rows_html = "\n".join(
        f"""<tr>
          <td>{MONTH_LABELS[m["per_apur"]]}</td>
          <td class="num">{br_int(m["escopo"])}</td>
          <td class="num ok">{br_int(m["ok"])}</td>
          <td class="num">0</td>
          <td class="num">0</td>
          <td class="status">Fechado</td>
        </tr>"""
        for m in emp["meses"]
    )

    alerta_dedep_html = ""
    if emp["key"] == "SOLUCOES":
        alerta_dedep_html = (
            '<div class="note">'
            '<div class="note-title">Observação técnica</div>'
            'Foi detectada anomalia nos arquivos originais da empresa envolvendo valores '
            'de dedução unitária de dependente acima do padrão legal esperado. O Easy-Social '
            'não realizou readequação desses valores durante o reenvio, para não alterar bases '
            'de IR e demais efeitos tributários já transmitidos pela empresa. Para uma adequação '
            'futura às normas corretas, recomenda-se análise específica com a equipe Easy-Social.'
            '</div>'
        )

    descricao_html = (
        '<div class="atividade-section">'
        '<div class="atividade-label">Descrição da atividade</div>'
        '<div class="atividade-text">'
        f'Foram coletados todos os eventos do eSocial referentes a <b>{total_meses} meses</b> '
        f'de 2025, CPF por CPF, totalizando <b>{br_int(total_ok)} CPFs/competência</b> '
        'processados no ano. Os XMLs originalmente transmitidos foram baixados do ambiente '
        'do eSocial e reaproveitados para reenvio com as readequações das rubricas que '
        'sofreram alteração nas incidências dos três tributos: '
        '<b>IRRF, INSS e FGTS</b>.'
        '</div>'
        '</div>'
    )

    if emp["key"] == "APPA":
        topicos = [
            ('Análise e recomendação de incidências',
             'Análise profunda da base legal que justificava as incidências '
             '(<b>IRRF</b> e <b>INSS</b>) declaradas nas rubricas, tanto no sistema de folha '
             'interno da empresa quanto no eSocial. Em seguida, o Easy-Social produziu um '
             'sistema de recomendação das incidências reais, respaldado pela base legal e '
             'pelos artigos aplicáveis a cada natureza/rubrica. Em conjunto com a empresa, '
             'foram definidas as incidências corretas dos três tributos '
             '(<b>IRRF, INSS e FGTS</b>) rubrica a rubrica.'),
            ('Readequação via envio de eventos no eSocial',
             'Além de sugerir as incidências corretas, o Easy-Social executou o envio dos '
             'eventos ao eSocial e a verificação dos respectivos arquivos de retorno, '
             'garantindo conformidade com a base legal. A readequação completa, somada '
             'aos envios, regularizou a empresa perante o eSocial.'),
            ('Repositório de rubricas readequadas',
             'Geração de repositório consolidado com as rubricas reconfiguradas, '
             'destinado à adequação do sistema de folha nativo da empresa, para que '
             'internamente as incidências reflitam o estado correto.'),
            ('Análise integral de S-1210 e S-5002',
             'Análise e criação de repositório com todos os eventos <b>S-1210</b> e '
             'respectivos totalizadores <b>S-5002</b> do ano-calendário 2025, obtidos '
             'diretamente do eSocial via XML, com conferência dos valores totalizadores.'),
            ('Sistema de envio por lotes',
             'Foi identificada a existência de naturezas com incidências distintas conforme '
             'grupos de CPFs — situação herdada da operação anterior. Para tratar essa '
             'particularidade sem perder rastreabilidade, o Easy-Social criou um mecanismo '
             'de lotes que permite configurar rubricas diferentes por grupo de CPFs e '
             'seguir ajustando-as ao longo dos envios de S-1210.'),
            ('Envio massivo de S-1210 por lotes',
             'Transmissão mês a mês de todos os CPFs com S-1210 da empresa, segregados '
             'em grupos de lotes conforme a configuração de rubricas aplicável a cada '
             'grupo.'),
            ('Revisão do fechamento de folha por CPF',
             'Revisão completa do estado da empresa dentro do eSocial, validando o '
             'fechamento de folha CPF a CPF. Nos casos com pendência, foi feito o '
             'retrabalho sobre o que havia sido transmitido de forma incorreta, com '
             'readequação conforme a revisão.'),
            ('Repositório consolidado final',
             'Criação do repositório final com todos os dados transmitidos, contemplando '
             'versões anteriores e atuais dos eventos, para servir de base à atualização '
             'dos dados internos do sistema de folha vigente da empresa.'),
        ]
        topicos_html = ''.join(
            f'<li><b>{titulo}.</b> {texto}</li>' for titulo, texto in topicos
        )
        descricao_html = (
            '<div class="atividade-section">'
            '<div class="atividade-label">Descrição da atividade</div>'
            '<div class="atividade-text">'
            'Foi iniciado um trabalho para o reenvio dos eventos <b>S-1210</b>; durante a '
            'execução, foi identificada inconsistência relevante na tabela de rubricas e '
            'naturezas do eSocial, tanto no "sistema de folha interno da empresa" quanto '
            'no próprio eSocial. Diante disso, entendeu-se necessária a readequação de '
            'grande parte das rubricas. Para atender a essa demanda, foram realizadas as '
            'seguintes frentes de trabalho:'
            '</div>'
            f'<ol class="atividade-list">{topicos_html}</ol>'
            '</div>'
        )

    pontos_criticos_html = ""
    if emp["key"] == "APPA":
        pontos_criticos_html = (
            '<div class="pontos-criticos">'
            '<div class="pc-title">'
            '<span class="pc-icon">!</span>'
            'Pontos cr\u00edticos identificados no sistema da empresa'
            '</div>'
            '<div class="pc-body">'
            '<div class="pc-item">'
            '<div class="pc-h">1. Rubricas com m\u00faltiplas incid\u00eancias por CPF</div>'
            '<p>Culturalmente, a APPA utiliza rubricas com diferentes configura\u00e7\u00f5es de '
            'incid\u00eancias de <b>IRRF, INSS e FGTS</b> ao longo do ano \u2014 ou seja, uma mesma '
            'rubrica possui incid\u00eancias distintas dependendo de qual CPF est\u00e1 sendo tratado. '
            'Para viabilizar o reenvio, classificamos esses CPFs em grupos e executamos os '
            'envios de forma modular por meio de <b>lotes</b>.</p>'
            '<p><b>Risco:</b> antes do in\u00edcio desta atividade, a empresa relatou um '
            '<b>travamento na configura\u00e7\u00e3o da rubrica</b>. Alterar a configura\u00e7\u00e3o de '
            'incid\u00eancia de uma mesma rubrica diversas vezes pode travar essa rubrica '
            'dentro do eSocial. O efeito \u00e9 catastr\u00f3fico: a rubrica perde a capacidade de '
            'ser redefinida e passa a incidir <b>retroativamente</b> sobre os CPFs envolvidos.</p>'
            '<p><b>Recomenda\u00e7\u00e3o:</b> criar rubricas com naturezas bem estabelecidas, '
            'evitando reescrever a mesma rubrica m\u00faltiplas vezes. O Easy-Social j\u00e1 possui '
            'solu\u00e7\u00e3o capaz de suportar esse modelo \u2014 trata-se de uma avalia\u00e7\u00e3o nossa para '
            'um poss\u00edvel trabalho futuro.</p>'
            '</div>'
            '<div class="pc-item">'
            '<div class="pc-h">2. Reanálise estrutural do sistema de rubricas</div>'
            '<p>Sugerimos uma reanálise do sistema de rubricas em conjunto com a equipe de '
            'RH, eliminando rubricas <b>duplicadas, in\u00fateis ou redundantes</b>, e habilitando '
            'a capacidade de <b>adicionar e remover</b> rubricas. Nesta etapa, apenas '
            '<b>readequamos</b> as rubricas existentes \u2014 a reestrutura\u00e7\u00e3o completa fica '
            'como pr\u00f3ximo passo recomendado.</p>'
            '</div>'
            '</div>'
            '</div>'
        )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório — {emp['razao']} — {brand['nome']}</title>
<style>
@page {{ size: A4; margin: 0; }}
@media print {{ body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; font-family: "Inter", "Segoe UI", Arial, sans-serif;
  color: {brand['color_page_ink']}; background: #FFFFFF; font-size: 11.5px; line-height: 1.5; }}

/* Banner header full-bleed */
.banner {{
  width: 100%;
  background: {brand.get('color_logo_bg', brand['color_bg'])};
  padding: 4mm 12mm;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid {brand['color_accent_border']};
  height: 32mm;
}}
.banner .logo-wrap {{
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}}
.banner .logo-wrap img {{
  max-width: 100%; max-height: 100%;
  object-fit: contain; display: block;
}}
.banner .logo-wrap .es-logo {{ width: 100%; height: 100%; }}

/* Faixa de título */
.title-bar {{
  width: 100%;
  background: {brand['color_bg']};
  color: {brand['color_ink']};
  padding: 3mm 16mm;
  border-bottom: 4px solid {brand['color_accent']};
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10mm;
}}
.title-bar .title-left {{ flex: 1 1 auto; }}
.title-bar .title-left h1 {{
  margin: 0; font-size: 22px; font-weight: 800;
  letter-spacing: -0.3px; line-height: 1.2; color: {brand['color_ink']};
}}
.title-bar .title-left .sub {{
  margin-top: 5px; font-size: 11.5px; color: {brand['color_muted']};
}}
.title-bar .kicker {{
  flex: 0 0 auto;
  font-size: 10.5px; letter-spacing: 2.5px; text-transform: uppercase;
  color: {brand['color_ink']}; background: transparent;
  border: 1px solid {brand['color_accent']};
  padding: 6px 14px; border-radius: 999px;
}}
.banner .kicker {{
  display: inline-block;
  font-size: 9.5px;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: {brand['color_accent']};
  background: {brand['color_accent_soft']};
  border: 1px solid {brand['color_accent_border']};
  padding: 4px 12px;
  border-radius: 999px;
  margin-bottom: 10px;
}}
.banner h1 {{
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.3px;
  line-height: 1.2;
  color: {brand['color_ink']};
}}
.banner .sub {{
  margin-top: 6px;
  font-size: 11px;
  color: {brand['color_muted']};
  max-width: 110mm;
  margin-left: auto;
}}

/* Conteúdo */
.content {{ padding: 5mm 16mm 5mm 16mm; }}

.empresa-row {{
  display: flex; justify-content: space-between; align-items: flex-end;
  padding-bottom: 5px; margin-bottom: 7px;
  border-bottom: 1px solid {brand['color_table_border']};
}}
.empresa-row .razao {{ font-size: 15px; font-weight: 700; color: {brand['color_page_ink']}; }}
.empresa-row .cnpj {{ font-size: 12px; color: {brand['color_page_muted']}; margin-top: 3px; }}
.empresa-row .periodo {{ font-size: 11px; color: {brand['color_page_muted']}; text-align: right; }}
.empresa-row .periodo b {{ color: {brand['color_page_ink']}; font-weight: 700; }}

.kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }}
.kpi {{ border: 1px solid {brand['color_table_border']}; border-radius: 8px;
  padding: 8px 12px; background: #FFFFFF; }}
.kpi .k {{ font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase;
  color: {brand['color_page_muted']}; }}
.kpi .v {{ font-size: 21px; font-weight: 800; margin-top: 5px; color: {brand['color_page_ink']};
  font-variant-numeric: tabular-nums; line-height: 1.05; }}
.kpi .v.cifrao {{ font-size: 17px; }}
.kpi .vsub {{ font-size: 11.5px; font-weight: 600; margin-top: 2px;
  color: {brand['color_page_muted']}; font-variant-numeric: tabular-nums; line-height: 1.1; }}
.kpi.accent {{ border-color: {brand['color_accent_border']}; background: {brand['color_accent_soft']}; }}
.kpi.accent .v {{ color: {brand['color_accent']}; }}

.section {{ margin-top: 14px; }}
.section-title {{ display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }}
.section-title .bar {{ width: 3px; height: 14px; background: {brand['color_accent']}; border-radius: 99px; }}
.section-title h3 {{ margin: 0; font-size: 13px; font-weight: 700; letter-spacing: 0.2px;
  text-transform: uppercase; color: {brand['color_page_ink']}; }}

table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
th {{ background: {brand['color_table_head_bg']}; color: {brand['color_table_head_ink']};
  text-align: left; padding: 6px 10px; font-size: 10.5px; text-transform: uppercase;
  letter-spacing: 0.6px; border-bottom: 1px solid {brand['color_table_border']}; }}
td {{ padding: 6px 10px; border-bottom: 1px solid {brand['color_table_border']}; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.ok {{ color: {brand['color_accent']}; font-weight: 700; }}
.status {{ font-weight: 600; color: {brand['color_accent']}; }}

.conclusion {{ margin-top: 8px; border-radius: 8px; padding: 9px 13px;
  background: {brand['color_accent_soft']}; border: 1px solid {brand['color_accent_border']};
  font-size: 11px; color: {brand['color_page_ink']}; }}
.conclusion b {{ color: {brand['color_accent']}; }}
.conclusion .crit {{ margin-top: 5px; font-size: 9px; color: {brand['color_page_muted']};
  font-weight: 400; }}

/* Blocos de Atividade Realizada / Descrição */
.atividade-block {{ margin-top: 8px; margin-bottom: 10px; }}
.atividade-section {{ margin-bottom: 6px; }}
.atividade-section:last-child {{ margin-bottom: 0; }}
.atividade-label {{ font-size: 9.5px; letter-spacing: 1.6px; text-transform: uppercase;
  color: {brand['color_accent']}; font-weight: 800; margin-bottom: 3px; }}
.atividade-text {{ font-size: 11px; color: {brand['color_page_ink']}; line-height: 1.5; text-align: justify; }}
.atividade-text b {{ color: {brand['color_page_ink']}; font-weight: 700; }}
.atividade-list {{ margin: 6px 0 0 0; padding-left: 18px; font-size: 11px;
  color: {brand['color_page_ink']}; line-height: 1.5; }}
.atividade-list li {{ margin-bottom: 5px; text-align: justify; }}
.atividade-list li:last-child {{ margin-bottom: 0; }}
.atividade-list li b {{ color: {brand['color_page_ink']}; }}

.note {{ margin-top: 6px; border-radius: 8px; padding: 8px 12px;
  background: #FFF8E1; border: 1px solid #E6C76A; border-left: 4px solid #B8860B;
  font-size: 10.5px; color: #5A4310; line-height: 1.4; }}
.note .note-title {{ font-weight: 800; text-transform: uppercase; letter-spacing: 1.2px;
  font-size: 9.5px; color: #8A6212; margin-bottom: 3px; }}

/* Pontos críticos — destaque vermelho/laranja */
.pontos-criticos {{ margin-top: 10px; border-radius: 10px; overflow: hidden;
  border: 1px solid #E0A0A0; background: #FFF5F2;
  break-inside: avoid; page-break-inside: avoid; }}
.pontos-criticos .pc-title {{ display: flex; align-items: center; gap: 10px;
  background: #B12B1B; color: #FFFFFF; padding: 7px 14px;
  font-size: 11.5px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px;
  break-after: avoid; page-break-after: avoid; }}
.pontos-criticos .pc-icon {{ display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 50%; background: #FFFFFF; color: #B12B1B;
  font-weight: 900; font-size: 13px; line-height: 1; }}
.pontos-criticos .pc-body {{ padding: 10px 14px; }}
.pontos-criticos .pc-item {{ margin-bottom: 8px;
  break-inside: avoid; page-break-inside: avoid; }}
.pontos-criticos .pc-item:last-child {{ margin-bottom: 0; }}
.pontos-criticos .pc-h {{ font-size: 11px; font-weight: 800; color: #7A1B0F;
  margin-bottom: 3px; break-after: avoid; page-break-after: avoid; }}
.pontos-criticos p {{ margin: 0 0 4px 0; font-size: 10.5px; line-height: 1.5;
  color: {brand['color_page_ink']}; text-align: justify;
  break-inside: avoid; page-break-inside: avoid; orphans: 3; widows: 3; }}
.pontos-criticos p:last-child {{ margin-bottom: 0; }}
.pontos-criticos p b {{ color: #7A1B0F; }}

.page-footer {{ display: flex; justify-content: space-between; align-items: center;
  margin-top: 7px; padding-top: 4px; border-top: 1px solid {brand['color_table_border']};
  font-size: 9.5px; color: {brand['color_page_muted']}; }}
</style>
</head>
<body>

<header class="banner">
  <div class="logo-wrap">{brand['logo_html']}</div>
</header>
<div class="title-bar">
  <div class="title-left">
    <h1>Horas Trabalhadas, Custo de IA e Conclusão do Processamento S-1210</h1>
    <div class="sub">Documento consolidado: horas, custo de IA e status final dos períodos S-1210/S-1299 de 2025.</div>
  </div>
  <span class="kicker">Relatório de Atividade · 2026</span>
</div>

<main class="content">
  <div class="empresa-row">
    <div>
      <div class="razao">{emp['razao']}</div>
      <div class="cnpj">CNPJ {emp['cnpj']}</div>
    </div>
    <div class="periodo">
      <div>Período do trabalho: <b>{emp['periodo_horas']}</b></div>
      <div>Períodos cobertos: <b>{periodo_apur}</b></div>
    </div>
  </div>

  <div class="atividade-block">
    <div class="atividade-section">
      <div class="atividade-label">Atividade realizada</div>
      <div class="atividade-text">
        Reenvio massivo dos eventos <b>S-1210</b> (Pagamentos de Rendimentos do Trabalho)
        e dos eventos de abertura e fechamento de folha (<b>S-1298</b> e <b>S-1299</b>),
        cobrindo o período de <b>{periodo_apur}</b>.
      </div>
    </div>
    {descricao_html}
  </div>

  <div class="kpis">
    <div class="kpi"><div class="k">Horas trabalhadas</div><div class="v">{emp['horas']}</div></div>
    <div class="kpi">
      <div class="k">Gasto com IA</div>
      <div class="v cifrao">{emp['custo_ia']}</div>
      <div class="vsub">{_brl(emp['custo_ia_usd'])}</div>
    </div>
    <div class="kpi accent"><div class="k">CPFs processados (OK)</div><div class="v">{br_int(total_ok)}</div></div>
  </div>
  {pontos_criticos_html}

  <div class="section">
    <div class="section-title"><span class="bar"></span><h3>Execução por mês — S-1210 / S-1299</h3></div>
    <table>
      <thead>
        <tr>
          <th>Período de apuração</th>
          <th class="num">Escopo</th>
          <th class="num">OK</th>
          <th class="num">Erro</th>
          <th class="num">Pendente</th>
          <th>S-1299</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>

  <div class="conclusion">
    Processamento concluído com <b>{br_int(total_ok)} CPFs em OK</b> sobre um escopo final de
    <b>{br_int(total_escopo)}</b>, sem erros e sem pendências.
    <b>{meses_fechados} de {total_meses}</b> meses estão com S-1299 aceito e período fechado.
    <div class="crit">{brand['rodape']} · Critério: último status S-1210 por CPF e por mês, com S-1299 fechado.</div>
  </div>
  {alerta_dedep_html}
</main>

</body>
</html>
"""


# ----------------------------------------------------------------------
# Conversão HTML -> PDF (Edge headless)
# ----------------------------------------------------------------------

def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge = next((c for c in candidates if Path(c).exists()), None) \
        or shutil.which("msedge") or shutil.which("chrome")
    if not edge:
        print(f"  [PDF] navegador não encontrado")
        return False
    cmd = [edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={pdf_path}", html_path.as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return pdf_path.exists()


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for brand in BRANDS:
        brand_dir = OUT_ROOT / brand["key"]
        brand_dir.mkdir(parents=True, exist_ok=True)
        for emp in EMPRESAS:
            html_path = brand_dir / f"_tmp_{emp['key']}.html"
            pdf_path = brand_dir / f"{emp['key']}_RELATORIO_2026.pdf"
            html_path.write_text(render_html(brand, emp), encoding="utf-8")
            ok = html_to_pdf(html_path, pdf_path)
            try:
                html_path.unlink()
            except OSError:
                pass
            print(f"  {brand['key']:>22} / {emp['key']:<10} -> {'OK' if ok else 'FALHOU'}")
    # Limpa HTMLs antigos remanescentes
    for old in OUT_ROOT.rglob("*.html"):
        try:
            old.unlink()
        except OSError:
            pass
    print(f"\nPasta: {OUT_ROOT}")


if __name__ == "__main__":
    main()
