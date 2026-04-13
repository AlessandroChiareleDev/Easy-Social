import pathlib

p = pathlib.Path("/opt/easy-social/python-scripts/esocial/xml_s3000.py")
txt = p.read_text()

# Remove the indApuracao line that was added incorrectly
old = '            _sub(ide_folha, "indApuracao", ind_apuracao)\n            _sub(ide_folha, "perApur", per_apur)'
new = '            _sub(ide_folha, "perApur", per_apur)'

assert old in txt, "Old text not found!"
assert txt.count(old) == 1, "Multiple matches!"
txt = txt.replace(old, new, 1)
p.write_text(txt)
print("Removed indApuracao from ideFolhaPagto - S-3000 only needs perApur!")
