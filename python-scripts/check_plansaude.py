#!/usr/bin/env python3
"""Extract ALL fields from FIRST S-1210 XML and look for planSaude data."""
import xml.etree.ElementTree as ET

# First S-1210
print('=== PRIMEIRO S-1210 ===')
tree = ET.parse('/opt/easy-social/xmls_set2025/ID1059690710000002025100610373900001.S-1210.xml')
root = tree.getroot()
for elem in root.iter():
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    if elem.text and elem.text.strip() and tag not in ('X509Certificate', 'SignatureValue', 'DigestValue'):
        print(f'  {tag}: {elem.text.strip()}')

# Also check DB for planSaude data
print('\n=== BUSCANDO planSaude em TODOS XMLs S-1210 ===')
import glob
for f in sorted(glob.glob('/opt/easy-social/xmls_set2025/*.S-1210.xml')):
    with open(f) as fh:
        c = fh.read()
    if 'planSaude' in c or 'cnpjOper' in c or 'regANS' in c:
        print(f'  ACHEI planSaude em: {f.split("/")[-1]}')
        tree2 = ET.parse(f)
        for elem in tree2.getroot().iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag in ('cnpjOper', 'regANS', 'vlrSaudeTit', 'vlrSaudeDep', 'tpDep', 'vlrReembTit', 'vlrReembDep', 'planSaude', 'detOper', 'detPlano', 'infoSaudeColet'):
                print(f'    {tag}: {elem.text}')

# Check other common XML directories
import os
for d in ['/opt/easy-social/xmls', '/opt/easy-social/recibos_s1010']:
    if os.path.exists(d):
        print(f'\n  Dir exists: {d}')
