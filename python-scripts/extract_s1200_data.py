"""Extract recibo and structure from latest S-1200 for CPF 31381951805"""
import re

data = open("/opt/easy-social/xmls_set2025/ID1059690710000002025102413182600003.S-1200.xml").read()

# Recibo
m = re.search(r"nrRecibo>([^<]+)<", data)
print("RECIBO S-1200:", m.group(1) if m else "NOT FOUND")

# All dmDevs
print("\ndmDevs:")
for m in re.finditer(r"ideDmDev>([^<]+)<", data):
    print(" ", m.group(1))

# All rubricas with values
print("\nRubricas:")
for m in re.finditer(r"codRubr>([^<]+)</.*?ideTabRubr>([^<]+)</.*?vrRubr>([^<]+)<", data, re.DOTALL):
    print(f"  cod={m.group(1)} tab={m.group(2)} vr={m.group(3)}")

# Check indRetif
m = re.search(r"indRetif>([^<]+)<", data)
print(f"\nindRetif: {m.group(1) if m else 'N/A'}")

# Check nrRecibo in ideEvento (retif against)
m = re.search(r"ideEvento.*?nrRecibo>([^<]+)<", data, re.DOTALL)
print(f"Retif against: {m.group(1) if m else 'N/A'}")

# Full S-1200 event XML (between first <evtRemun and </Signature>)
print("\n--- Full event structure (first 3000 chars) ---")
evt_start = data.find("<evtRemun")
evt_end = data.find("</evtRemun>") + len("</evtRemun>")
if evt_start > 0 and evt_end > evt_start:
    print(data[evt_start:min(evt_start+3000, evt_end)])
