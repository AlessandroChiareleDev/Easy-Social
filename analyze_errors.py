#!/usr/bin/env python3
"""Analyze pipeline errors"""
import json, sys, urllib.request

url = "http://localhost:8000/api/pipeline-batch/runs/1/cpfs?status=erro&limit=100"
data = json.loads(urllib.request.urlopen(url).read())

print(f"Total erros: {data['total']}\n")

# Group by error type
error_types = {}
for item in data['items']:
    cpf = item['cpf']
    lote = item['lote_num']
    erro = item['erro_descricao'] or 'Sem descrição'
    
    # Extract error code [XXXX]
    import re
    codes = re.findall(r'\[(\d+)\]', erro)
    key = ', '.join(codes) if codes else 'unknown'
    
    if key not in error_types:
        error_types[key] = {'count': 0, 'cpfs': [], 'desc': ''}
    error_types[key]['count'] += 1
    error_types[key]['cpfs'].append(cpf)
    error_types[key]['desc'] = erro

print("=" * 70)
print("ERROS AGRUPADOS POR TIPO")
print("=" * 70)

for code, info in sorted(error_types.items(), key=lambda x: -x[1]['count']):
    print(f"\n[{code}] — {info['count']} CPFs")
    print(f"  CPFs: {', '.join(info['cpfs'])}")
    print(f"  Erro: {info['desc'][:500]}")
    print()
