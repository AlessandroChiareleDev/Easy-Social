from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "OBJETIVA_JAN_MAI_2025"
sys.path.insert(0, str(BASE_DIR))

import gerar_xmls_fevereiro_67_corrigidos as base

base.PER_APUR = "2025-06"
base.S1200_PERIODOS = ["2025-05", "2025-06"]
base.TOTAL_ESPERADO = 87
base.ERRORS_CSV = base.ROOT / "relatorio_ana" / "OBJETIVA_JUN_NOV_2025" / "erros_s1210_objetiva_2025-06.csv"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "OBJETIVA_JUN_NOV_2025" / "2025-06" / "xmls_junho_87_corrigidos"
base.PLAN_DIR = base.OUT_DIR / "01_plano_saude_retificacao"


if __name__ == "__main__":
    base.main()