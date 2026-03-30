import requests

# Tentar diferentes URLs com headers de browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}

urls = [
    'https://frontend.esocial.gov.br/adm/Tabela/BaixarConteudo?idTabela=3',
    'https://frontend.esocial.gov.br/Tabela/BaixarConteudo?idTabela=3',
    'https://frontend.esocial.gov.br/adm/api/tabela/3',
    'https://frontend.esocial.gov.br/api/tabela/3',
]

for url in urls:
    try:
        r = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
        ct = r.headers.get('content-type', 'none')
        print(f'{r.status_code} len={len(r.content)} ct={ct[:60]} - {url}')
        if r.status_code == 200 and len(r.content) > 500:
            preview = r.content[:200].decode('latin-1', errors='replace')
            print(f'  Preview: {preview[:150]}')
    except Exception as e:
        print(f'ERR - {url} - {e}')
