"""
SCRIPT DE RECUPERAÇÃO — Lote 28 (Erro [459])
=============================================

Este script consulta o eSocial para cada CPF afetado pelo crash do lote 28,
busca o recibo NOVO (da retificação que o eSocial JÁ processou), e atualiza
o nosso banco de dados.

COMO FUNCIONA:
- Para cada CPF com erro [459], consulta o webservice 'ConsultarIdentificadoresTrabalhador'
- O eSocial retorna todos os eventos daquele CPF no período
- Filtramos pelo S-1210 mais recente (que será a retificação que queremos)
- Pegamos o nrRecibo e atualizamos o pipeline_cpf_results

PARA RODAR:
  cd /opt/easy-social/python-scripts
  python3 recuperar_lote28.py

ATENÇÃO: Roda em PRODUÇÃO! Os dados são apenas de CONSULTA + UPDATE local.
         Não envia nenhum evento ao eSocial.
"""

import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import DB_CONFIG, LOCAL_DB_CONFIG
import psycopg2
import psycopg2.extras
from esocial.esocial_client import ESocialClient
from esocial.certificate_manager import CertificateManager

# ── Config ──
PER_APUR = "2025-09"
AMBIENTE_PRODUCAO = True
RUN_ID = 1
DT_INI = "2025-09-01"
DT_FIM = "2025-09-30"
DELAY_ENTRE_CONSULTAS = 2  # segundos entre cada consulta ao eSocial

# ── Carregar certificado ──
def load_cert():
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cnpj, arquivo_path, senha_encrypted "
                "FROM certificados_a1 WHERE ativo = TRUE LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "cnpj": row[0],
                "arquivo_path": row[1],
                "senha": CertificateManager.decrypt_password(row[2]),
            }
    finally:
        conn.close()


def main():
    print("=" * 70)
    print("RECUPERAÇÃO DE RECIBOS — LOTE 28 (Erro [459])")
    print("=" * 70)
    
    # 1. Carregar certificado
    cert_info = load_cert()
    if not cert_info:
        print("ERRO: Certificado não encontrado!")
        sys.exit(1)
    
    print(f"Certificado: CNPJ {cert_info['cnpj']}")
    
    with open(cert_info['arquivo_path'], 'rb') as f:
        pfx_data = f.read()
    senha = cert_info['senha']
    cnpj = cert_info['cnpj']
    empregador = {"tpInsc": 1, "nrInsc": cnpj}
    
    # 2. Buscar CPFs com erro [459]
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT cpf, nr_recibo_original
        FROM pipeline_cpf_results
        WHERE run_id = %s AND erro_descricao LIKE '%%[459]%%'
        ORDER BY cpf
    """, (RUN_ID,))
    cpfs_459 = cur.fetchall()
    
    print(f"CPFs com erro [459]: {len(cpfs_459)}")
    print()
    
    # 3. Para cada CPF, consultar o eSocial
    recuperados = 0
    falhas = 0
    
    for i, row in enumerate(cpfs_459):
        cpf = row['cpf']
        recibo_original = row['nr_recibo_original']
        
        print(f"[{i+1}/{len(cpfs_459)}] CPF {cpf}...", end=" ", flush=True)
        
        try:
            result = ESocialClient.consultar_identificadores_trabalhador(
                cpf=cpf,
                dt_ini=DT_INI,
                dt_fim=DT_FIM,
                pfx_data=pfx_data,
                password=senha,
                empregador=empregador,
                producao=AMBIENTE_PRODUCAO,
            )
            
            if not result.get('sucesso'):
                print(f"FALHA na consulta: {result.get('descricao', result.get('erro', '?'))}")
                falhas += 1
                time.sleep(DELAY_ENTRE_CONSULTAS)
                continue
            
            # Procurar S-1210 nos eventos retornados
            eventos = result.get('eventos', [])
            s1210_eventos = [e for e in eventos if 'S-1210' in e.get('tipo', '')]
            
            if not s1210_eventos:
                print(f"Nenhum S-1210 encontrado para período {PER_APUR}")
                falhas += 1
                time.sleep(DELAY_ENTRE_CONSULTAS)
                continue
            
            # Pegar o mais recente (último da lista, ou o que tem recibo diferente do original)
            recibo_novo = None
            for evt in s1210_eventos:
                nr = evt.get('nrRecibo') or evt.get('nr_recibo')
                if nr and nr != recibo_original:
                    recibo_novo = nr
            
            if not recibo_novo:
                # Se só tem 1, pode ser que o recibo retornado é o novo
                for evt in s1210_eventos:
                    nr = evt.get('nrRecibo') or evt.get('nr_recibo')
                    if nr:
                        recibo_novo = nr
            
            if recibo_novo:
                # Atualizar no banco
                cur.execute("""
                    UPDATE pipeline_cpf_results
                    SET status = 'ok', nr_recibo_novo = %s, erro_descricao = NULL,
                        processed_at = NOW()
                    WHERE run_id = %s AND cpf = %s
                """, (recibo_novo, RUN_ID, cpf))
                conn.commit()
                print(f"✓ RECUPERADO! Recibo: {recibo_novo}")
                recuperados += 1
            else:
                print(f"Eventos encontrados mas sem recibo novo. Eventos: {json.dumps(s1210_eventos, indent=2)[:200]}")
                falhas += 1
        
        except Exception as e:
            print(f"ERRO: {e}")
            falhas += 1
        
        time.sleep(DELAY_ENTRE_CONSULTAS)
    
    print()
    print("=" * 70)
    print(f"RESULTADO: {recuperados} recuperados, {falhas} falhas de {len(cpfs_459)} total")
    print("=" * 70)
    
    conn.close()


if __name__ == "__main__":
    main()
