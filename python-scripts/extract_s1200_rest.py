data = open("/opt/easy-social/xmls_set2025/ID1059690710000002025102413182600003.S-1200.xml").read()
evt_start = data.find("<evtRemun")
evt_end = data.find("</evtRemun>") + len("</evtRemun>")
evt = data[evt_start:evt_end]
print(evt[2800:])
