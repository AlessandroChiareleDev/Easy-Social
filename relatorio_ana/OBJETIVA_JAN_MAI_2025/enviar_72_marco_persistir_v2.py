from __future__ import annotations

import enviar_67_fevereiro_persistir_v2 as base

base.PER_APUR = "2025-03"
base.OUT_ROOT = base.ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "xmls_marco_72_corrigidos"
base.MANIFEST = base.OUT_ROOT / "manifest_72_xmls_corrigidos.json"
base.RUN_DIR = base.OUT_ROOT / "retorno_envio_72_marco"
base.RESULT_PATH = base.RUN_DIR / "resultado_envio_72_marco.json"


if __name__ == "__main__":
    base.main()