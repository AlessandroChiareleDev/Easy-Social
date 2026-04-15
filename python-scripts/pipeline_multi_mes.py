"""
Orquestrador Multi-Mês — Pipeline S-1210 + Relatórios
══════════════════════════════════════════════════════
Executa o pipeline completo para múltiplos meses em sequência:
  1. Importar XMLs do mês
  2. Snapshot S-5002 ANTES
  3. S-1298 → S-1210 retif → S-1299
  4. Snapshot S-5002 DEPOIS
  5. Gerar relatório ANTES vs DEPOIS

Uso:
  python pipeline_multi_mes.py --periodos 2025-01,2025-02,2025-03
  python pipeline_multi_mes.py --periodos 2025-01,2025-02,2025-03 --dry-run
  python pipeline_multi_mes.py --config meses.json

Formato meses.json:
  {
    "meses": [
      {"periodo": "2025-01", "xml_folder": "/opt/easy-social/xmls/jan2025"},
      {"periodo": "2025-02", "xml_folder": "/opt/easy-social/xmls/fev2025"},
      {"periodo": "2025-03", "xml_folder": "/opt/easy-social/xmls/mar2025"}
    ]
  }
"""

import sys, os, json, argparse, re, time, logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import DB_CONFIG
import psycopg2
import psycopg2.extras

# Imports locais
from pipeline_batch import run_pipeline, _load_s1210_data
from relatorio_antes_depois import gerar_relatorio

# ── Logging ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/pipeline_multi_mes.log"),
    ],
)
log = logging.getLogger("multi_mes")


# ── Importação de XMLs ────────────────────────────────────────

def importar_xmls(xml_folder: str, per_apur: str):
    """
    Importa XMLs de uma pasta via API do explorador.
    Usa requests para chamar o endpoint local.
    """
    import requests

    log.info(f"  Importando XMLs de {xml_folder} ...")

    try:
        resp = requests.post(
            "http://localhost:8000/api/explorador/importar",
            json={"folder_path": xml_folder},
            timeout=600,
        )
        if resp.status_code == 200:
            data = resp.json()
            log.info(f"  ✓ Importação: {data.get('total_importados', '?')} eventos importados")
            return data
        else:
            log.error(f"  ✗ Importação falhou: HTTP {resp.status_code} — {resp.text[:500]}")
            return None
    except Exception as e:
        log.error(f"  ✗ Erro ao importar: {e}")
        return None


def contar_cpfs_periodo(per_apur: str) -> int:
    """Conta CPFs com S-1210 disponíveis no período."""
    cpfs = _load_s1210_data(per_apur)
    return len(cpfs)


# ── Orquestrador ──────────────────────────────────────────────

def executar_mes(periodo: str, xml_folder: str = None, dry_run: bool = False) -> dict:
    """
    Executa pipeline completo para um mês:
    1. Importar XMLs (se xml_folder fornecido)
    2. Executar pipeline (snapshot antes → S-1298 → S-1210 → S-1299 → snapshot depois)
    3. Gerar relatório ANTES vs DEPOIS
    """
    log.info(f"\n{'═'*70}")
    log.info(f"  MÊS: {periodo}")
    log.info(f"{'═'*70}")

    resultado = {
        "periodo": periodo,
        "importacao": None,
        "pipeline": None,
        "relatorio": None,
        "status": "pendente",
    }

    # Step 1: Importar XMLs
    if xml_folder:
        if not os.path.isdir(xml_folder):
            log.error(f"  ✗ Pasta não encontrada: {xml_folder}")
            resultado["status"] = "erro"
            resultado["erro"] = f"Pasta não encontrada: {xml_folder}"
            return resultado

        import_result = importar_xmls(xml_folder, periodo)
        resultado["importacao"] = import_result
        if not import_result:
            log.warning("  ⚠ Importação falhou, tentando continuar com dados existentes...")

    # Verificar se tem dados
    total_cpfs = contar_cpfs_periodo(periodo)
    log.info(f"  CPFs disponíveis para {periodo}: {total_cpfs}")

    if total_cpfs == 0:
        log.error(f"  ✗ Nenhum CPF com S-1210 em {periodo}. Importe os XMLs primeiro.")
        resultado["status"] = "erro"
        resultado["erro"] = "Sem dados S-1210 para o período"
        return resultado

    # Step 2: Executar pipeline
    try:
        pipeline_result = run_pipeline(periodo, dry_run=dry_run)
        resultado["pipeline"] = pipeline_result
    except SystemExit:
        log.error(f"  ✗ Pipeline falhou para {periodo}")
        resultado["status"] = "erro"
        resultado["erro"] = "Pipeline falhou (ver log)"
        return resultado
    except Exception as e:
        log.error(f"  ✗ Pipeline erro: {e}")
        resultado["status"] = "erro"
        resultado["erro"] = str(e)
        return resultado

    # Step 3: Relatório (somente se não dry-run)
    if not dry_run:
        try:
            run_id = pipeline_result.get("run_id")
            if run_id:
                relatorio_path = gerar_relatorio(run_id=run_id, per_apur=periodo)
                resultado["relatorio"] = relatorio_path
                log.info(f"  ✓ Relatório: {relatorio_path}")
        except Exception as e:
            log.warning(f"  ⚠ Erro ao gerar relatório: {e}")
            resultado["relatorio"] = f"ERRO: {e}"

    resultado["status"] = "completo" if not dry_run else "dry_run"
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Pipeline Multi-Mês")
    parser.add_argument("--periodos", help="Períodos separados por vírgula: 2025-01,2025-02,2025-03")
    parser.add_argument("--config", help="Arquivo JSON com config dos meses")
    parser.add_argument("--dry-run", action="store_true", help="Não envia eventos, só conta CPFs")
    args = parser.parse_args()

    meses = []

    if args.config:
        with open(args.config) as f:
            cfg = json.load(f)
        meses = cfg.get("meses", [])
    elif args.periodos:
        for p in args.periodos.split(","):
            p = p.strip()
            if re.match(r"^\d{4}-\d{2}$", p):
                meses.append({"periodo": p, "xml_folder": None})
            else:
                print(f"ERRO: Período inválido: {p}")
                sys.exit(1)
    else:
        print("ERRO: Forneça --periodos ou --config")
        sys.exit(1)

    log.info(f"\n{'═'*70}")
    log.info(f"  PIPELINE MULTI-MÊS — {len(meses)} meses")
    log.info(f"  Meses: {', '.join(m['periodo'] for m in meses)}")
    log.info(f"  Modo: {'DRY RUN' if args.dry_run else 'PRODUÇÃO'}")
    log.info(f"{'═'*70}")

    resultados = []
    for m in meses:
        resultado = executar_mes(
            periodo=m["periodo"],
            xml_folder=m.get("xml_folder"),
            dry_run=args.dry_run,
        )
        resultados.append(resultado)

        # Pausa entre meses
        if not args.dry_run and m != meses[-1]:
            log.info("\n  Aguardando 30s antes do próximo mês...")
            time.sleep(30)

    # ═══════════════ RESUMO GERAL ═══════════════
    log.info(f"\n\n{'═'*70}")
    log.info("  RESUMO GERAL MULTI-MÊS")
    log.info(f"{'═'*70}")

    for r in resultados:
        p_info = r.get("pipeline", {})
        status_icon = "✓" if r["status"] == "completo" else ("⊘" if r["status"] == "dry_run" else "✗")
        log.info(f"  {status_icon} {r['periodo']}: "
                 f"CPFs={p_info.get('total_cpfs', '?')}, "
                 f"OK={p_info.get('cpfs_ok', '?')}, "
                 f"Erro={p_info.get('cpfs_erro', '?')}, "
                 f"Status={r['status']}")
        if r.get("relatorio"):
            log.info(f"    Relatório: {r['relatorio']}")

    # Salvar resumo JSON
    resumo_path = f"/tmp/pipeline_multi_mes_result_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(resumo_path, "w") as f:
        json.dump(resultados, f, indent=2, default=str)
    log.info(f"\n  Resumo salvo em: {resumo_path}")

    return resultados


if __name__ == "__main__":
    main()
