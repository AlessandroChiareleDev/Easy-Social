from __future__ import annotations

import enviar_67_fevereiro_persistir_v2 as base

base.PER_APUR = "2025-04"
base.OUT_ROOT = base.ROOT / "relatorio_ana" / "OBJETIVA_JAN_MAI_2025" / "xmls_abril_90_corrigidos"
base.MANIFEST = base.OUT_ROOT / "manifest_90_xmls_corrigidos.json"
base.RUN_DIR = base.OUT_ROOT / "retorno_envio_90_abril"
base.RESULT_PATH = base.RUN_DIR / "resultado_envio_90_abril.json"


if __name__ == "__main__":
    base.main()