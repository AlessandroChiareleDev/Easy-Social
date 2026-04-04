"""Script one-shot para executar o pipeline de recuperação via API local."""
import requests
import json
import sys

BODY = {
    "cpf": "08132588983",
    "ambiente": "1",
    "ind_apuracao": "1",
    "per_apur_alvo": "2024-12",
    "per_apur_bloqueador": "2025-01",
    "s1200_nr_recibo": "1.1.0000000030324738244",
    "s1210_alvo_nr_recibo": "1.1.0000000039598280881",
    "s1210_bloq_nr_recibo": "1.1.0000000039598924749",
    "s1200_dm_devs": [
        {"ideDmDev":"20241129.1.01512563","codCateg":"101","infoPerApur":{"ideEstabLot":[{"tpInsc":"1","nrInsc":"05969071000110","codLotacao":"E00278-001-05A","remunPerApur":[{"matricula":"001-001-056502","itensRemun":[{"codRubr":"9276","ideTabRubr":"1","vrRubr":"231.00","indApurIR":"0"}],"infoAgNocivo":{"grauExp":"1"}}]}]}},
        {"ideDmDev":"20241129.1.01512566","codCateg":"101","infoPerApur":{"ideEstabLot":[{"tpInsc":"1","nrInsc":"05969071000110","codLotacao":"E00278-001-05A","remunPerApur":[{"matricula":"001-001-056502","itensRemun":[{"codRubr":"9284","ideTabRubr":"1","vrRubr":"667.80","indApurIR":"0"}],"infoAgNocivo":{"grauExp":"1"}}]}]}},
        {"ideDmDev":"10711955","codCateg":"101","infoPerApur":{"ideEstabLot":[{"tpInsc":"1","nrInsc":"05969071000110","codLotacao":"E00278-001-05A","remunPerApur":[{"matricula":"001-001-056502","itensRemun":[{"codRubr":"2","ideTabRubr":"1","qtdRubr":"30.00","vrRubr":"2501.20","indApurIR":"0"},{"codRubr":"10","ideTabRubr":"EA001","vrRubr":"125.06","indApurIR":"0"},{"codRubr":"105","ideTabRubr":"EA001","qtdRubr":"34.34","vrRubr":"585.62","indApurIR":"0"},{"codRubr":"160","ideTabRubr":"EA001","vrRubr":"140.55","indApurIR":"0"},{"codRubr":"273","ideTabRubr":"1","vrRubr":"0.70","indApurIR":"0"},{"codRubr":"541","ideTabRubr":"1","vrRubr":"1.20","indApurIR":"0"},{"codRubr":"566","ideTabRubr":"1","qtdRubr":"12.00","vrRubr":"301.11","indApurIR":"0"},{"codRubr":"570","ideTabRubr":"1","qtdRubr":"7.50","vrRubr":"39.63","indApurIR":"0"},{"codRubr":"672","ideTabRubr":"1","vrRubr":"150.07","indApurIR":"0"},{"codRubr":"776","ideTabRubr":"1","vrRubr":"108.12","indApurIR":"0"}],"infoAgNocivo":{"grauExp":"1"}}]}]}},
        {"ideDmDev":"10711965","codCateg":"101","infoPerApur":{"ideEstabLot":[{"tpInsc":"1","nrInsc":"05969071000110","codLotacao":"E00278-001-05A","remunPerApur":[{"matricula":"001-001-056502","itensRemun":[{"codRubr":"273","ideTabRubr":"1","vrRubr":"0.44","indApurIR":"0"},{"codRubr":"480","ideTabRubr":"EA001","vrRubr":"70.94","indApurIR":"0"},{"codRubr":"596","ideTabRubr":"1","qtdRubr":"9.00","vrRubr":"6.38","indApurIR":"0"}],"infoAgNocivo":{"grauExp":"1"}}]}]}}
    ],
    "s1210_alvo_info_pgtos": [
        {"dtPgto":"2024-12-06","tpPgto":"1","perRef":"2024-11","ideDmDev":"10711884","vrLiq":"2883"},
        {"dtPgto":"2024-12-20","tpPgto":"1","perRef":"2024","ideDmDev":"10711933","vrLiq":"1273"}
    ],
    "s1210_alvo_info_ir_complem": {
        "infoIRCR": [
            {"tpCR":"056107","dedDepen":[{"tpRend":"12","cpfDep":"14020816930","vlrDedDep":"189.59"},{"tpRend":"11","cpfDep":"14020816930","vlrDedDep":"189.59"}]}
        ]
    },
    "s1210_bloq_info_pgtos": [
        {"dtPgto":"2025-01-07","tpPgto":"1","perRef":"2024-12","ideDmDev":"10711965","vrLiq":"65"},
        {"dtPgto":"2025-01-07","tpPgto":"1","perRef":"2024-12","ideDmDev":"10711955","vrLiq":"2753"}
    ]
}

print("=" * 60)
print("  PIPELINE RECOVERY — Executando...")
print("=" * 60)
print(f"CPF: {BODY['cpf']}")
print(f"Período alvo: {BODY['per_apur_alvo']}")
print(f"Período bloqueador: {BODY['per_apur_bloqueador']}")
print(f"Ambiente: PRODUÇÃO")
print()

try:
    resp = requests.post(
        "http://localhost:8000/api/pipeline/recuperar",
        json=BODY,
        timeout=600,
    )
    print(f"HTTP Status: {resp.status_code}")
    print()
    
    data = resp.json()
    print(f"Status: {data.get('status')}")
    print(f"Steps OK: {data.get('steps_ok')}/{data.get('total_steps')}")
    print()
    
    for step in data.get("steps", []):
        icon = "✓" if step["status"] == "ok" else "✗"
        print(f"  {icon} Step {step['step']}: {step['evento']} ({step['per_apur']}) — {step['status']}")
        if step.get("nr_recibo"):
            print(f"    Recibo: {step['nr_recibo']}")
        if step.get("descricao"):
            desc = step["descricao"][:200]
            print(f"    Desc: {desc}")
        print()
    
    print("=" * 60)
    print(f"  RESULTADO: {data.get('status', '?').upper()}")
    print("=" * 60)
    
    # Save full response
    with open("pipeline_result.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    print("\nResposta completa salva em pipeline_result.json")

except Exception as e:
    print(f"ERRO: {e}")
    sys.exit(1)
