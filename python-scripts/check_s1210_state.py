import xml.etree.ElementTree as ET
import glob

cpf = "31381951805"
ns_evt = {"e": "http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00"}
ns_rec = {"rc": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0"}

for f in sorted(glob.glob("/opt/easy-social/xmls_set2025/*S-1210*")):
    with open(f) as fh:
        content = fh.read()
    if cpf not in content:
        continue
    root = ET.fromstring(content)
    evt = root.find(".//e:evtPgtos", ns_evt)
    if evt is None:
        continue
    ide = evt.find("e:ideEvento", ns_evt)
    ind_retif = ide.find("e:indRetif", ns_evt).text
    nr_ref_el = ide.find("e:nrRecibo", ns_evt)
    nr_ref = nr_ref_el.text if nr_ref_el is not None else "N/A"
    recibo_el = root.find(".//rc:recibo/rc:nrRecibo", ns_rec)
    recibo_txt = recibo_el.text if recibo_el is not None else "N/A"
    dmdevs = [p.text for p in evt.findall(".//e:ideDmDev", ns_evt)]
    fname = f.rsplit("/", 1)[-1]
    print(fname)
    print(f"  indRetif={ind_retif}, retif_against={nr_ref}")
    print(f"  RESULT recibo: {recibo_txt}")
    print(f"  dmDevs: {dmdevs}")
    print()
