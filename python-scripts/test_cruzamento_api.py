import requests
r = requests.get('http://localhost:8000/api/cruzamento-eb/rubricas',
                 params={'page': 1, 'per_page': 10, 'filtro': 'inconsistentes'}, timeout=10)
d = r.json()
print(f"Status: {r.status_code}")
print(f"Keys: {list(d.keys()) if isinstance(d, dict) else type(d)}")
print(f"Response: {str(d)[:300]}")
for x in d['rubricas']:
    print(f"  ID={x['cod_rubrica']}: {x['descricao'][:30]} | INSS={x['incid_inss']} IRRF={x['incid_irrf']} FGTS={x['incid_fgts']}")
    print(f"    Correto INSS: {x['incid_base_legal_inss'][:50]}")
    print(f"    Correto IRRF: {x['incid_base_legal_irrf'][:50]}")
    print(f"    Correto FGTS: {x['incid_base_legal_fgts'][:50]}")
