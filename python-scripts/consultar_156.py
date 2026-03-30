"""Consultar resultado do envio da rubrica 156"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from esocial.certificate_manager import CertificateManager
from esocial.esocial_client import ESocialClient
import psycopg2

conn = psycopg2.connect(host='localhost', port=5432, database='easy_social_db',
                        user='easy_social_user', password='sua_senha_segura')
cur = conn.cursor()
cur.execute('SELECT arquivo_path, senha_encrypted FROM certificados_a1 WHERE ativo = TRUE LIMIT 1')
row = cur.fetchone()
conn.close()

senha = CertificateManager.decrypt_password(row[1])
with open(row[0], 'rb') as f:
    pfx_data = f.read()

protocolo = '1.2.202603.0000000000205431186'
print(f'Consultando protocolo: {protocolo}')
resultado = ESocialClient.consultar_lote(protocolo, pfx_data, senha)

print(f'Sucesso: {resultado.get("sucesso")}')
print(f'Codigo Resposta: {resultado.get("codigo_resposta")}')
print(f'Descricao: {resultado.get("descricao")}')

if resultado.get('eventos'):
    for evt in resultado['eventos']:
        print(f'\n  Evento {evt.get("id", "?")}:')
        print(f'    Codigo: {evt.get("codigo_resposta")}')
        print(f'    Descricao: {evt.get("descricao")}')
        print(f'    Nr Recibo: {evt.get("nr_recibo")}')
        if evt.get('ocorrencias'):
            for oc in evt['ocorrencias']:
                print(f'    Ocorrencia: [{oc.get("tipo")}] {oc.get("codigo")}: {oc.get("descricao")}')
else:
    print('Nenhum evento retornado (pode estar em processamento)')
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
