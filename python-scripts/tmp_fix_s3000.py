import pathlib

p = pathlib.Path("/opt/easy-social/python-scripts/esocial/xml_s3000.py")
txt = p.read_text()

old_line = '            _sub(ide_folha, "perApur", per_apur)'
new_lines = '            _sub(ide_folha, "indApuracao", ind_apuracao)\n            _sub(ide_folha, "perApur", per_apur)'

assert old_line in txt, "Old text not found!"
assert txt.count(old_line) == 1, "Multiple matches!"

txt = txt.replace(old_line, new_lines, 1)
p.write_text(txt)
print("Fixed successfully!")
