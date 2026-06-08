from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "OBJETIVA_JAN_MAI_2025"
sys.path.insert(0, str(BASE_DIR))

import gerar_xmls_fevereiro_67_corrigidos as base

base.PER_APUR = "2025-12"
base.S1200_PERIODOS = ["2025-11", "2025-12"]
base.TOTAL_ESPERADO = 72
base.ERRORS_CSV = base.ROOT / "relatorio_ana" / "OBJETIVA_DEZEMBRO_2025_ERROS_V2_ATUAL_2026-05-28.csv"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "OBJETIVA_DEZEMBRO_2025" / "xmls_dezembro_72_corrigidos"
base.PLAN_DIR = base.OUT_DIR / "01_plano_saude_retificacao"


if __name__ == "__main__":
    base.main()