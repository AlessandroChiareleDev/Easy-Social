#!/usr/bin/env python3
"""Check S-1200 XMLs for Adriana to find ideDmDev values."""
import xml.etree.ElementTree as ET
import glob

cpf = '31381951805'
ns_remun = 'http://www.esocial.gov.br/schema/evt/evtRemun/v_S_01_03_00'
ns_download = 'http://www.esocial.gov.br/schema/download/retornoProcessamento/v1_0_0'

files = glob.glob('/opt/easy-social/xmls_set2025/*.S-1200.xml')
for f in sorted(files):
    with open(f) as fh:
        content = fh.read()
    if cpf not in content:
        continue
    
    print(f"\n{'='*60}")
    print(f"FILE: {f.split('/')[-1]}")
    print(f"{'='*60}")
    
    tree = ET.parse(f)
    root = tree.getroot()
    
    # Find all elements with relevant info
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag in ('indRetif', 'perApur', 'nrRecibo', 'cpfTrab', 'ideDmDev', 'codRubr', 'tpRubr', 'natRubr', 'vrRubr', 'vrLiq'):
            print(f"  {tag}: {elem.text}")
        if tag == 'ideDmDev':
            print(f"  --- Demonstrativo: {elem.text} ---")
