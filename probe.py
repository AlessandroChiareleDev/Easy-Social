import json

def probe_file(path):
    print(f"\nProbing {path}:")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Type: {type(data)}")
    if isinstance(data, list):
        print(f"Length: {len(data)}")
        if len(data) > 0:
            print(f"First element type: {type(data[0])}")
            print(f"First element keys/value: {data[0] if not isinstance(data[0], dict) else list(data[0].keys())}")
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")

probe_file(r"relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/resolvedor_quinzenais_dtpgto_agosto_202_deddepen.json")
probe_file(r"relatorio_ana/CORRECAO_AGOSTO_202_DEDDEPEN/preflight_agosto_202_deddepen.json")
