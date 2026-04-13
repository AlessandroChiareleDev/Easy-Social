"""
Relatório para Ana (RH APPA)
─────────────────────────────
Gera um relatório completo de todos os eventos eSocial alterados,
com CPF, tipo de evento, recibo original, recibo novo, status, etc.

Saída: CSV + resumo no terminal
"""
import psycopg2
import csv
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")

def connect():
    return psycopg2.connect(
        **DB_CONFIG,
        keepalives=1, keepalives_idle=30,
        keepalives_interval=10, keepalives_count=3
    )

def formatar_cpf(cpf: str) -> str:
    """Formata CPF: 12345678901 → 123.456.789-01"""
    if cpf and len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf or ""

def gerar_relatorio_pipeline():
    """Relatório principal: retificações S-1210 por CPF (pipeline batch)"""
    conn = connect()
    cur = conn.cursor()

    # Info do pipeline run
    cur.execute("""
        SELECT id, per_apur, status, total_cpfs, cpfs_ok, cpfs_erro,
               s1298_done, s1299_done, started_at, finished_at
        FROM pipeline_runs
        ORDER BY id
    """)
    runs = cur.fetchall()
    run_cols = [d[0] for d in cur.description]

    print("=" * 70)
    print("  RELATÓRIO DE EVENTOS ESOCIAL - APPA")
    print(f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 70)

    for run in runs:
        run_dict = dict(zip(run_cols, run))
        run_id = run_dict['id']
        per_apur = run_dict['per_apur']

        print(f"\n── Pipeline Run #{run_id} | Período: {per_apur} ──")
        print(f"   Status: {run_dict['status']}")
        print(f"   Total CPFs: {run_dict['total_cpfs']}")
        print(f"   Sucesso: {run_dict['cpfs_ok']}")
        print(f"   Erros: {run_dict['cpfs_erro']}")
        print(f"   S-1298 (reabertura): {'✓' if run_dict['s1298_done'] else '✗'}")
        print(f"   S-1299 (fechamento): {'✓' if run_dict['s1299_done'] else '✗'}")
        print(f"   Início: {run_dict['started_at']}")
        print(f"   Fim: {run_dict['finished_at']}")

        # Buscar CPFs deste run
        cur.execute("""
            SELECT cpf, status, nr_recibo_original, nr_recibo_novo,
                   erro_descricao, lote_num, processed_at
            FROM pipeline_cpf_results
            WHERE run_id = %s
            ORDER BY cpf
        """, (run_id,))
        cpf_rows = cur.fetchall()
        cpf_cols = [d[0] for d in cur.description]

        # Gerar CSV
        csv_file = os.path.join(OUTPUT_DIR, f"relatorio_appa_{per_apur}_{TIMESTAMP}.csv")
        with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "CPF",
                "CPF_Formatado",
                "Período",
                "Tipo_Evento",
                "Status",
                "Recibo_Original",
                "Recibo_Novo",
                "Lote",
                "Processado_Em",
                "Erro"
            ])
            for row in cpf_rows:
                r = dict(zip(cpf_cols, row))
                writer.writerow([
                    r['cpf'],
                    formatar_cpf(r['cpf']),
                    per_apur,
                    "S-1210 (Retificação)",
                    r['status'],
                    r['nr_recibo_original'] or "",
                    r['nr_recibo_novo'] or "",
                    r['lote_num'] or "",
                    r['processed_at'].strftime('%d/%m/%Y %H:%M') if r['processed_at'] else "",
                    r['erro_descricao'] or ""
                ])

        print(f"\n   📄 CSV gerado: {csv_file}")
        print(f"   Total linhas: {len(cpf_rows)}")

        # Resumo por status
        status_count = {}
        for row in cpf_rows:
            s = dict(zip(cpf_cols, row))['status']
            status_count[s] = status_count.get(s, 0) + 1
        print(f"   Resumo: {status_count}")

    conn.close()
    return csv_file if runs else None

def gerar_relatorio_s1010():
    """Relatório das rubricas S-1010 alteradas"""
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, tipo_evento, modo, ambiente, ini_valid, status,
               protocolo_envio, codigo_resposta, descricao_resposta,
               total_eventos, rubrica_detalhes, nr_recibo,
               created_at
        FROM esocial_envios
        WHERE ambiente = '1'
        ORDER BY created_at
    """)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    print(f"\n{'=' * 70}")
    print("  S-1010 — RUBRICAS ALTERADAS EM PRODUÇÃO")
    print(f"{'=' * 70}")

    csv_file = os.path.join(OUTPUT_DIR, f"relatorio_appa_s1010_{TIMESTAMP}.csv")
    total_rubricas = 0

    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Envio_ID",
            "Tipo_Evento",
            "Modo",
            "Início_Validade",
            "Status",
            "Protocolo",
            "Código_Resposta",
            "Descrição_Resposta",
            "Nr_Recibo",
            "Rubricas",
            "Data_Envio"
        ])

        for row in rows:
            r = dict(zip(cols, row))
            rubricas_info = ""
            if r['rubrica_detalhes']:
                detalhes = r['rubrica_detalhes']
                if isinstance(detalhes, list):
                    rubricas_info = ", ".join(
                        f"{d.get('codRubr', '?')} ({d.get('ideTabRubr', '?')})"
                        for d in detalhes
                    )
                    total_rubricas += len(detalhes)
                elif isinstance(detalhes, dict):
                    rubricas_info = str(detalhes)
                    total_rubricas += 1

            writer.writerow([
                r['id'],
                r['tipo_evento'],
                r['modo'],
                r['ini_valid'] or "",
                r['status'],
                r['protocolo_envio'] or "",
                r['codigo_resposta'] or "",
                r['descricao_resposta'] or "",
                r['nr_recibo'] or "",
                rubricas_info,
                r['created_at'].strftime('%d/%m/%Y %H:%M') if r['created_at'] else ""
            ])

            status_icon = "✓" if r['status'] in ('aceito', 'processado') else "✗"
            print(f"  {status_icon} Envio #{r['id']}: {r['modo']} | {r['status']} | "
                  f"Resp: {r['codigo_resposta']} | Recibo: {r['nr_recibo'] or 'N/A'}")
            if rubricas_info:
                print(f"    Rubricas: {rubricas_info[:100]}")

    print(f"\n   📄 CSV S-1010: {csv_file}")
    print(f"   Total envios produção: {len(rows)}")
    print(f"   Total rubricas alteradas: {total_rubricas}")

    conn.close()
    return csv_file

def main():
    print("\n" + "█" * 70)
    print("█  GERAÇÃO DE RELATÓRIO PARA ANA (RH APPA)")
    print("█  Data: " + datetime.now().strftime('%d/%m/%Y %H:%M'))
    print("█" * 70)

    try:
        csv1 = gerar_relatorio_pipeline()
        csv2 = gerar_relatorio_s1010()

        print(f"\n{'=' * 70}")
        print("  ARQUIVOS GERADOS:")
        print(f"{'=' * 70}")
        if csv1:
            print(f"  1. {csv1}")
        if csv2:
            print(f"  2. {csv2}")
        print(f"\n  ✅ Pronto! Envie os CSVs para a Ana.")
        print(f"  Obs: CSVs com separador ; e encoding UTF-8-BOM (compatível Excel PT-BR)")

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
