#!/bin/bash
set -e
F=/opt/easy-social/python-scripts/esocial/s1210_repo_routes.py
cp "$F" "$F.bak_jan_fix_$(date +%s)"
python3 -c "
import re
with open('$F','r',encoding='utf-8') as fh: t=fh.read()
new = t.replace('for m in range(2, 13)', 'for m in range(1, 13)')
if new == t:
    print('NO CHANGE - pattern not found')
    raise SystemExit(2)
with open('$F','w',encoding='utf-8') as fh: fh.write(new)
print('OK - replaced')
"
grep -n "for m in range" "$F"
pm2 restart easy-python
sleep 3
pm2 list | grep easy-python
echo '--- HTTP test ---'
curl -s "http://127.0.0.1:8000/api/s1210-repo/anual/overview?ano=2025" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('meses retornados:', [m['per_apur'] for m in d['meses']])
jan=[m for m in d['meses'] if m['per_apur']=='2025-01']
if jan:
    print('JAN L1:', jan[0]['lotes'][0])
"
