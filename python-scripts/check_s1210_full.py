#!/usr/bin/env python3
"""Extract ALL fields from Adriana's S-1210 XML."""
import xml.etree.ElementTree as ET

tree = ET.parse('/opt/easy-social/xmls_set2025/ID1059690710000002025102413525500013.S-1210.xml')
root = tree.getroot()

print('=== TODOS OS CAMPOS DO S-1210 ===')
for elem in root.iter():
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    if elem.text and elem.text.strip():
        print(f'  {tag}: {elem.text.strip()}')

# Also check S-1200 for planSaude
print('\n=== S-1200 MAIS RECENTE - TODOS OS CAMPOS ===')
tree2 = ET.parse('/opt/easy-social/xmls_set2025/ID1059690710000002025102413182600003.S-1200.xml')
root2 = tree2.getroot()
for elem in root2.iter():
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    if elem.text and elem.text.strip():
        print(f'  {tag}: {elem.text.strip()}')
