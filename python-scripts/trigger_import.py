import requests
r = requests.post("http://localhost:8000/api/explorador/importar", json={"pasta": "/opt/easy-social/xmls_set2025", "periodo": "2025-09"}, timeout=30)
print(r.status_code, r.json())
