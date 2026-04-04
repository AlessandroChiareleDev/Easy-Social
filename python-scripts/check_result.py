import json

with open("pipeline_result.json", "r") as f:
    d = json.load(f)

print(f"Status: {d.get('status')}")
print(f"Steps: {d.get('steps_ok')}/{d.get('total_steps')}")
print()
for s in d.get("steps", []):
    print(f"Step {s['step']}: {s['evento']} {s['per_apur']}")
    print(f"  recibo: {s.get('nr_recibo', 'N/A')}")
    print(f"  protocolo: {s.get('protocolo', 'N/A')}")
    print(f"  status: {s['status']}")
    print(f"  codigo: {s.get('codigo_resposta', 'N/A')}")
    if s.get('descricao'):
        print(f"  desc: {s['descricao'][:200]}")
    print()
