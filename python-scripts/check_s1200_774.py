import sys
data = open("/opt/easy-social/xmls_set2025/ID1059690710000002025102413182600003.S-1200.xml").read()
if "planoSaude" in data:
    print("TEM planoSaude no S-1200")
    idx = data.find("planoSaude")
    print(data[max(0,idx-200):idx+500])
else:
    print("NAO tem planoSaude no S-1200")
if "774" in data:
    idx = data.find("774")
    print("\nContexto rubrica 774:")
    print(data[max(0,idx-300):idx+300])
