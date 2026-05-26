from __future__ import annotations

from pathlib import Path

import preparar_resposta_jaque_novembro as base


base.PER_APUR = "2025-12"
base.XLSX = Path(r"C:\Users\xandao\Downloads\resposta final\2025-12_relatorio_final_jaque.xlsx")
base.ERRORS_CSV = base.ROOT / "relatorio_ana" / "GISELE_SX_ERROS_S1210_DEZEMBRO_2025.csv"


if __name__ == "__main__":
    raise SystemExit(base.main())