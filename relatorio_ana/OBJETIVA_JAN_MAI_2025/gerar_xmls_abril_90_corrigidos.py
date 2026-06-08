from __future__ import annotations

import gerar_xmls_fevereiro_67_corrigidos as base

base.PER_APUR = "2025-04"
base.S1200_PERIODOS = ["2025-03", "2025-04"]
base.TOTAL_ESPERADO = 90
base.ERRORS_CSV = base.ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "erros_s1210_objetiva_2025-04.csv"
base.OUT_DIR = base.ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "xmls_abril_90_corrigidos"
base.PLAN_DIR = base.OUT_DIR / "01_plano_saude_retificacao"


if __name__ == "__main__":
    base.main()