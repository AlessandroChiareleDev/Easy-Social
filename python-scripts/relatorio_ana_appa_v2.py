"""
Relatório COMPLETO para Ana (RH APPA) — v2
───────────────────────────────────────────
Gera relatório com TODOS os eventos por CPF:
- S-1200 (remuneração), S-1210 (pagamento),
- S-3000 (exclusão), S-5001/S-5002/S-5003 (totalizadores),
- S-1010 (rubricas), etc.

Saída: CSV completo + CSV resumo por CPF
"""
import psycopg2
import psycopg2.extras
import csv
import sys
import os
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "relatorio_ana")
os.makedirs(OUTPUT_DIR, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")

DESCRICAO_EVENTOS = {
    "S-1010": "Tabela de Rubricas",
    "S-1200": "Remuneração do Trabalhador",
    "S-1210": "Pagamentos de Rendimentos",
    "S-1298": "Reabertura de Período",
    "S-1299": "Fechamento de Período",
    "S-2200": "Cadastro/Admissão",
    "S-2205": "Alteração de Dados Cadastrais",
    "S-2206": "Alteração Contratual",
    "S-2210": "CAT",
    "S-2230": "Afastamento Temporário",
    "S-2240": "Condições Ambientais do Trabalho",
    "S-2299": "Desligamento",
    "S-2500": "Processo Trabalhista",
    "S-3000": "Exclusão de Evento",
    "S-3500": "Exclusão de Processo Trabalhista",
    "S-5001": "Totalizador INSS/Contrib. Previdenciária",
    "S-5002": "Totalizador IRRF",
    "S-5003": "Totalizador Contrib. Patronal (FGTS/Outras)",
    "S-5503": "Totalizador Processo Trabalhista",
}


def connect():
    return psycopg2.connect(
        **DB_CONFIG,
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3
    )


def formatar_cpf(cpf: str) -> str:
    if cpf and len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf or ""


def gerar_relatorio_eventos_detalhado():
    """CSV 1: Todos os eventos do explorador, linha por linha."""
    conn = connect()
    cur = conn.cursor()

    print("  Consultando explorador_eventos (pode demorar)...")
    cur.execute("""
        SELECT cpf, tipo_evento, per_apur, nr_recibo, id_evento,
               dt_processamento, cd_resposta
        FROM explorador_eventos
        WHERE cpf IS NOT NULL
        ORDER BY cpf, per_apur, tipo_evento, dt_processamento
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    csv_file = os.path.join(OUTPUT_DIR, f"eventos_detalhado_{TIMESTAMP}.csv")
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "CPF",
            "CPF_Formatado",
            "Tipo_Evento",
            "Descricao_Evento",
            "Periodo",
            "Nr_Recibo",
            "ID_Evento",
            "Data_Processamento",
            "Codigo_Resposta"
        ])
        for row in rows:
            r = dict(zip(cols, row))
            writer.writerow([
                r['cpf'],
                formatar_cpf(r['cpf']),
                r['tipo_evento'],
                DESCRICAO_EVENTOS.get(r['tipo_evento'], r['tipo_evento']),
                r['per_apur'] or "",
                r['nr_recibo'] or "",
                r['id_evento'] or "",
                r['dt_processamento'].strftime('%d/%m/%Y %H:%M') if r['dt_processamento'] else "",
                r['cd_resposta'] or ""
            ])

    print(f"  -> {csv_file}")
    print(f"     {len(rows)} linhas")
    conn.close()
    return csv_file, rows, cols


def gerar_relatorio_resumo_cpf(rows, cols):
    """CSV 2: Resumo por CPF — quantos eventos de cada tipo."""
    cpf_data = defaultdict(lambda: {"tipos": defaultdict(int), "recibos": []})

    for row in rows:
        r = dict(zip(cols, row))
        cpf = r['cpf']
        tipo = r['tipo_evento']
        cpf_data[cpf]["tipos"][tipo] += 1
        if r['nr_recibo']:
            cpf_data[cpf]["recibos"].append(r['nr_recibo'])

    # Descobrir todos os tipos de evento que aparecem
    all_tipos = sorted(set(
        tipo for d in cpf_data.values() for tipo in d["tipos"]
    ))

    csv_file = os.path.join(OUTPUT_DIR, f"resumo_por_cpf_{TIMESTAMP}.csv")
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        header = ["CPF", "CPF_Formatado", "Total_Eventos"]
        header += [f"Qtd_{t}" for t in all_tipos]
        header += ["Tipos_Evento", "Total_Recibos"]
        writer.writerow(header)

        for cpf in sorted(cpf_data.keys()):
            d = cpf_data[cpf]
            total = sum(d["tipos"].values())
            row_out = [
                cpf,
                formatar_cpf(cpf),
                total,
            ]
            row_out += [d["tipos"].get(t, 0) for t in all_tipos]
            row_out += [
                ", ".join(sorted(d["tipos"].keys())),
                len(d["recibos"]),
            ]
            writer.writerow(row_out)

    print(f"  -> {csv_file}")
    print(f"     {len(cpf_data)} CPFs")
    return csv_file


def gerar_relatorio_retificacoes():
    """CSV 3: Retificações S-1210 do pipeline batch com recibo original → novo."""
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT r.per_apur, c.cpf, c.status, c.nr_recibo_original, c.nr_recibo_novo,
               c.lote_num, c.processed_at, c.erro_descricao
        FROM pipeline_cpf_results c
        JOIN pipeline_runs r ON r.id = c.run_id
        ORDER BY c.cpf
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    csv_file = os.path.join(OUTPUT_DIR, f"retificacoes_s1210_{TIMESTAMP}.csv")
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "CPF",
            "CPF_Formatado",
            "Periodo",
            "Status",
            "Recibo_Original",
            "Recibo_Novo",
            "Lote",
            "Processado_Em",
            "Erro"
        ])
        for row in rows:
            r = dict(zip(cols, row))
            writer.writerow([
                r['cpf'],
                formatar_cpf(r['cpf']),
                r['per_apur'],
                r['status'],
                r['nr_recibo_original'] or "",
                r['nr_recibo_novo'] or "",
                r['lote_num'] or "",
                r['processed_at'].strftime('%d/%m/%Y %H:%M') if r['processed_at'] else "",
                r['erro_descricao'] or ""
            ])

    print(f"  -> {csv_file}")
    print(f"     {len(rows)} retificações")
    conn.close()
    return csv_file


def gerar_relatorio_s1010():
    """CSV 4: Rubricas S-1010 alteradas em produção."""
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, modo, status, protocolo_envio, codigo_resposta,
               descricao_resposta, nr_recibo, rubrica_detalhes, ocorrencias,
               created_at
        FROM esocial_envios
        WHERE ambiente = '1' AND modo IN ('alteracao', 'inclusao')
        ORDER BY created_at
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    csv_file = os.path.join(OUTPUT_DIR, f"rubricas_s1010_{TIMESTAMP}.csv")
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Envio_ID",
            "Modo",
            "Status",
            "Protocolo",
            "Codigo_Resposta",
            "Descricao_Resposta",
            "Nr_Recibo",
            "Rubricas",
            "Ocorrencias",
            "Data_Envio"
        ])
        ok = 0
        for row in rows:
            r = dict(zip(cols, row))
            rubricas = ""
            if r['rubrica_detalhes']:
                det = r['rubrica_detalhes']
                if isinstance(det, list):
                    rubricas = ", ".join(
                        f"{d.get('codRubr','?')}" for d in det
                    )
                elif isinstance(det, str):
                    import json
                    try:
                        det = json.loads(det)
                        rubricas = ", ".join(f"{d.get('codRubr','?')}" for d in det)
                    except:
                        rubricas = det

            ocorr = ""
            if r['ocorrencias']:
                oc = r['ocorrencias']
                if isinstance(oc, list):
                    ocorr = " | ".join(
                        f"{o.get('codigo','')}: {o.get('descricao','')}" for o in oc
                    )

            if r['status'] in ('processado', 'aceito'):
                ok += 1

            writer.writerow([
                r['id'],
                r['modo'],
                r['status'],
                r['protocolo_envio'] or "",
                r['codigo_resposta'] or "",
                r['descricao_resposta'] or "",
                r['nr_recibo'] or "",
                rubricas,
                ocorr[:200] if ocorr else "",
                r['created_at'].strftime('%d/%m/%Y %H:%M') if r['created_at'] else ""
            ])

    print(f"  -> {csv_file}")
    print(f"     {len(rows)} envios ({ok} processados OK)")
    conn.close()
    return csv_file


def main():
    print()
    print("█" * 70)
    print("█  RELATÓRIO COMPLETO PARA ANA (RH APPA) — v2")
    print("█  " + datetime.now().strftime('%d/%m/%Y %H:%M'))
    print("█" * 70)

    print("\n[1/4] Eventos detalhados (todos os tipos por CPF)...")
    csv1, rows, cols = gerar_relatorio_eventos_detalhado()

    print("\n[2/4] Resumo por CPF (quantos eventos de cada tipo)...")
    csv2 = gerar_relatorio_resumo_cpf(rows, cols)

    print("\n[3/4] Retificações S-1210 (recibo original → novo)...")
    csv3 = gerar_relatorio_retificacoes()

    print("\n[4/4] Rubricas S-1010 alteradas...")
    csv4 = gerar_relatorio_s1010()

    print(f"\n{'=' * 70}")
    print(f"  PRONTO! Arquivos na pasta:")
    print(f"  {OUTPUT_DIR}")
    print(f"{'=' * 70}")
    print(f"  1. {os.path.basename(csv1)} — todos os eventos, linha por linha")
    print(f"  2. {os.path.basename(csv2)} — resumo por CPF (1 linha por CPF)")
    print(f"  3. {os.path.basename(csv3)} — retificações S-1210 com recibos")
    print(f"  4. {os.path.basename(csv4)} — rubricas S-1010 alteradas")
    print(f"\n  Separador: ; | Encoding: UTF-8-BOM (Excel PT-BR)")


if __name__ == "__main__":
    main()
