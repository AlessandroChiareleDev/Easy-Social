"""
INVESTIGAÇÃO LOTE 28 — Erro [459] após crash de DNS

Objetivo: Levantar tudo sobre os 31 CPFs que deram [459] para o especialista analisar.
O que aconteceu: eSocial JÁ processou a retificação, mas perdemos os recibos novos.
"""
import psycopg2, psycopg2.extras, json

conn = psycopg2.connect(
    host='aws-1-us-east-2.pooler.supabase.com',
    port=5432,
    dbname='postgres',
    user='postgres.zpizibafccwsjgvplcum',
    password='6.18.13.1.8Supa',
    sslmode='require'
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# 1. Pegar todos os CPFs com erro [459]
cur.execute("""
    SELECT cpf, nr_recibo_original, nr_recibo_novo, erro_descricao, lote_num, processed_at,
           pagamentos, info_ir_cr
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND erro_descricao LIKE '%[459]%'
    ORDER BY cpf
""")
cpfs_459 = cur.fetchall()

print("=" * 80)
print("RELATÓRIO LOTE 28 — ERRO [459] — CRASH DNS")
print("=" * 80)
print()

print(f"Total de CPFs afetados: {len(cpfs_459)}")
print()

# 2. Contexto do crash
print("─" * 80)
print("O QUE ACONTECEU:")
print("─" * 80)
print("""
1. O pipeline enviou o Lote 28 (50 CPFs) ao eSocial como uma única requisição SOAP.
2. O eSocial processou TODOS os 50 eventos com sucesso e retornou os recibos.
3. O pipeline começou a gravar os resultados no banco (Supabase), um CPF por vez.
4. Conseguiu gravar 6 CPFs (03628162556 até 03635161586) como OK com recibo.
5. No 7º CPF (03635806544), o DNS do servidor caiu momentaneamente:
   "could not translate host name aws-1-us-east-2.pooler.supabase.com"
6. O pipeline crashou (sem retry na época) → processo morreu.
7. CPF 03635806544 foi corrigido manualmente (recibo salvo no banco).
8. Os 43 CPFs restantes do lote ficaram com status 'pendente' sem recibo.

9. Ao reiniciar o pipeline, ele tentou RETIFICAR esses 43 novamente.
10. Mas o eSocial rejeitou com [459]: "recibo de entrega não localizado ou já retificado"
    Motivo: O recibo ORIGINAL que o pipeline usou na 2ª tentativa já foi CONSUMIDO
    pela 1ª retificação (passo 2 acima). O eSocial marcou o evento original como 
    "retificado", então o recibo original ficou inválido.

RESULTADO: Esses 31 CPFs ESTÃO retificados no eSocial (a retificação foi aceita),
mas NÃO temos os recibos novos gravados no nosso banco.
""")

# 3. Verificar se existe consulta possível
print("─" * 80)
print("COMO RESOLVER:")
print("─" * 80)
print("""
OPÇÃO A — Consultar recibos via webservice eSocial (recomendado):
  Usar o webservice de Consulta Lote para buscar os recibos novos pelo protocolo
  de envio do lote original. Se o protocolo foi perdido, consultar pelo CPF+período.

OPÇÃO B — Reenviar S-1210 usando o recibo NOVO como base:
  Para cada CPF, consultar no eSocial qual é o recibo ATIVO atual do S-1210 
  daquele CPF em 2025-09, e fazer nova retificação usando esse recibo como base.

OPÇÃO C — Consultar no Portal Web do eSocial:
  Entrar em https://www.esocial.gov.br/ com o certificado digital do empregador
  e verificar os eventos S-1210 de cada CPF manualmente.
""")

# 4. Tabela detalhada de cada CPF
print("─" * 80)
print("TABELA DETALHADA DOS 31 CPFs COM ERRO [459]:")
print("─" * 80)
print()
print(f"{'CPF':<15} {'Recibo Original (INVÁLIDO)':<40} {'Pgtos':<6} {'Processado em'}")
print("─" * 80)
for row in cpfs_459:
    n_pgtos = len(row['pagamentos']) if row['pagamentos'] else 0
    proc = str(row['processed_at'])[:19] if row['processed_at'] else '—'
    print(f"{row['cpf']:<15} {row['nr_recibo_original']:<40} {n_pgtos:<6} {proc}")

# 5. Totais de pagamento desses CPFs
print()
print("─" * 80)
print("VALORES ENVOLVIDOS:")
print("─" * 80)
total_vlr = 0
for row in cpfs_459:
    if row['pagamentos']:
        for p in row['pagamentos']:
            total_vlr += float(p.get('vrLiq', '0'))
print(f"Soma total de vrLiq dos 31 CPFs: R$ {total_vlr:,.2f}")
print()

# 6. Lote 28 completo — quem salvou OK vs quem deu 459
print("─" * 80)
print("COMPOSIÇÃO DO LOTE 28 ORIGINAL (50 CPFs):")
print("─" * 80)
cur.execute("""
    SELECT cpf, status, nr_recibo_novo, lote_num
    FROM pipeline_cpf_results
    WHERE run_id = 1 AND (
        (lote_num = 28 AND status = 'ok')
        OR erro_descricao LIKE '%[459]%'
        OR cpf = '03635806544'
    )
    ORDER BY cpf
""")
lote28_all = cur.fetchall()

ok_count = 0
fix_count = 0
err_count = 0
for row in lote28_all:
    if row['status'] == 'ok' and row['lote_num'] == 28:
        tag = "✓ OK (recibo salvo)"
        ok_count += 1
    elif row['cpf'] == '03635806544' and row['status'] == 'ok':
        tag = "✓ OK (corrigido manualmente)"
        fix_count += 1
    else:
        tag = "✗ ERRO [459] — retificado no eSocial mas sem recibo no banco"
        err_count += 1
    recibo = row['nr_recibo_novo'] or '—'
    print(f"  {row['cpf']}  {tag}")
    if row['nr_recibo_novo']:
        print(f"                   Recibo novo: {row['nr_recibo_novo']}")

print(f"\nResumo: {ok_count} OK salvos + {fix_count} corrigido manual + {err_count} com erro [459]")
print(f"Total do lote: {ok_count + fix_count + err_count} CPFs")

# 7. Lista para copiar (para consulta no eSocial)
print()
print("─" * 80)
print("LISTA DE CPFs PARA CONSULTA NO eSocial (copiar/colar):")
print("─" * 80)
for row in cpfs_459:
    print(row['cpf'])

# 8. Situação geral do pipeline
print()
print("─" * 80)
print("SITUAÇÃO GERAL DO PIPELINE:")
print("─" * 80)
cur.execute("""
    SELECT status, COUNT(*) as qtd FROM pipeline_cpf_results WHERE run_id = 1 GROUP BY status ORDER BY status
""")
for row in cur.fetchall():
    print(f"  {row['status']:<12}: {row['qtd']}")

cur.execute("SELECT COUNT(*) FROM pipeline_cpf_results WHERE run_id=1")
total = cur.fetchone()['count']
print(f"  {'TOTAL':<12}: {total}")

conn.close()
