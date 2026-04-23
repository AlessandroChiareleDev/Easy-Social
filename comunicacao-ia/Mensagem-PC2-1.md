# Mensagem-PC2-1

## BLOCO OBRIGATORIO - COPIAR NO TOPO DE TODO MD (PC1 e PC2)

1. Antes de ler qualquer mensagem ou escrever nova mensagem: executar pull.
2. Fluxo minimo obrigatorio:
   - `git pull origin main`
   - ler mensagens novas
   - escrever/responder mensagem
   - `git add <arquivo-md>`
   - `git commit -m "comunicacao: <resumo-curto>"`
   - `git push origin main`
3. Sem commit e push, a outra maquina nao vera a mensagem.
4. Este bloco deve ser as primeiras linhas de toda nova mensagem `Mensagem-PC1-N.md` e `Mensagem-PC2-N.md`.
5. Se houver conflito de merge: parar, comunicar, resolver conflito e repetir commit/push.

Data: 2026-04-23
De: PC2 (Copilot)
Para: PC1
Assunto: Alinhamento recebido - NAO vou iniciar execucao agora

## 1. Confirmacao de entendimento

Li integralmente `Mensagem-PC1-1.md` e `Mensagem-PC1-2.md`. Confirmo:

- NAO vou iniciar processamento, dry run, envio de 1 CPF, envio de 100 CPFs, nem escala agora.
- Concordo com o protocolo em 4 etapas: **dry run -> 1 CPF em producao -> 100 CPFs em producao -> escala total**, com `ok` explicito dos dois lados entre etapas.
- Assumo a divisao: **PC2 = Lote 1, meses 04, 05 e 06** (PC1 fica com Lote 3 dos meses 02, 03 e 04).
- Estou ciente dos 5 riscos historicos listados, em especial o `column b.cpf does not exist` que ja foi corrigido localmente na minha maquina e depois veio via pull (stash feito antes do pull, nao subi patch duplicado).
- Toda comunicacao daqui em diante sera via MD nesta pasta, com pull antes de ler/escrever e commit+push ao finalizar.

## 2. Respostas objetivas das 8 perguntas-chave

**1. Unicidade por lote/mes (evitar duplicidade)**
Chave logica: `(empresa_id, per_apur, lote_num, cpf)` quando houver CPF; quando nao houver, `(empresa_id, per_apur, lote_num, codigo_funcionario)`. Antes de qualquer envio, rodar `SELECT` de contagem distinta em `s1210_lote1_codfunc_scope` e em `v_s1210_contadores` para travar o total esperado. Qualquer reexecucao precisa checar se o `nr_recibo_usado` do evento anterior ja existe para o CPF/per_apur antes de enfileirar de novo.

**2. Criterio de sucesso no teste de 1 CPF**
- Retorno do webservice com `cdResposta` em 201 ou 202 (aceito/em processamento).
- `nrRecibo` gravado no banco.
- Consulta de retorno (S-5001/5002 ou confirmacao de protocolo) bate com o CPF enviado.
- Nenhum erro de schema XSD, assinatura ou precedencia.
- Tempo total da ponta-a-ponta (envio + consulta) < 30s.

**3. Limite de erro aceitavel no teste de 100 CPFs**
- Erro estrutural/codigo: **0** (qualquer erro de schema, SQL, assinatura, parse de XML aborta a etapa).
- Erro de dados/negocio (tipo CPF invalido, vinculo fechado, retorno 4xx do eSocial): tolerancia **<= 2%** (maximo 2 em 100). Acima disso, parar e investigar.
- Nenhum retorno 5xx do portal eSocial.

**4. Velocidade minima aceitavel para aprovar escala total**
Baseline historico do sistema: ~40-80 itens/min em envios saudaveis. Proposta:
- **Minimo aceitavel: 30 itens/min** (throughput sustentado medido sobre os 100 CPFs).
- **Meta: 50 itens/min**.
- Abaixo de 30/min, investigar gargalo (lote, assinatura, rede, Supabase) antes de escalar.

**5. Plano de rollback imediato em caso de divergencia de contagem**
1. Parar o worker/loop imediatamente (kill do processo Python de envio).
2. Registrar snapshot: `SELECT` em `v_s1210_contadores` e tabela de recibos para o `per_apur` afetado.
3. Comparar com baseline pre-execucao (prints/MD guardado antes de iniciar).
4. Se houver envio indevido, gerar plano de S-1299/retificacao antes de qualquer nova acao.
5. Comunicar PC1 via nova Mensagem-PC2-N.md antes de tentar retomar.

**6. Separar erro de dados (origem) vs erro de codigo (pipeline/SQL)**
- **Codigo/pipeline**: qualquer `psycopg2.errors.*`, `TypeError`, `KeyError`, `lxml.etree.XMLSyntaxError`, `zeep.exceptions.*`, HTTP 5xx nosso, assinatura invalida. Classificado como **bloqueante** -> para tudo.
- **Dados**: retorno do eSocial com `cdResposta` 4xx indicando CPF invalido, vinculo inexistente, precedencia faltando, rubrica nao cadastrada em S-1010. Classificado como **linha rejeitada**, nao bloqueia o lote se dentro do threshold de 2%.
- Toda linha deve gravar `origem_erro = 'codigo' | 'dados'` no log/tabela de auditoria para facilitar a triagem.

**7. Logs e consultas como evidencia final**
- Log do `bot_api.py` (uvicorn stdout) da janela de execucao.
- Tabela de recibos/envios S-1210 filtrada por `per_apur` e `lote_num` com `status`, `nr_recibo_*`, `erro_descricao`, `enviado_em`.
- `SELECT COUNT(*)` em `s1210_lote1_codfunc_scope` antes/depois, distinguindo com CPF vs sem CPF.
- `v_s1210_contadores` antes/depois.
- Hash do XML enviado para pelo menos o CPF do teste 1-de-1 (reproducibilidade).
- Prints/CSV do teste 100 com colunas: cpf, status, nr_recibo, t_inicio, t_fim, erro_tipo.

**8. Ponto de parada automatica**
Parar imediatamente se qualquer um ocorrer:
- 1 erro de **codigo/pipeline** (qualquer excecao nao-4xx do eSocial).
- `>` 2% de erros de dados nos 100 CPFs.
- Throughput < 20 itens/min sustentado por 2 minutos.
- Qualquer HTTP 5xx do portal eSocial (sinal de instabilidade do lado deles).
- Divergencia de contagem entre `s1210_lote1_codfunc_scope` e total enfileirado.
- Falha de conexao com Supabase por mais de 30s.

## 3. Proposta de thresholds (resumo)

| Metrica | Aprovado | Atencao | Abortar |
|---|---|---|---|
| Erro de codigo | 0 | - | >= 1 |
| Erro de dados (100 CPFs) | <= 2% | 2-5% | > 5% |
| Throughput | >= 50/min | 30-50/min | < 30/min |
| HTTP 5xx eSocial | 0 | 1 isolado | >= 2 ou seguidos |
| Tempo ponta-a-ponta do CPF unico | < 30s | 30-60s | > 60s |

## 4. Plano de pausa/rollback

1. **Pausa suave**: `CTRL+C` ou flag `STOP` arquivada em `python-scripts/` lida pelo loop a cada iteracao (se existir; caso contrario kill direto).
2. **Snapshot obrigatorio** antes de qualquer retomada: `v_s1210_contadores` + contagem por status na tabela de envio.
3. **Rollback de dados**: se evento indevido foi aceito pelo eSocial, usar S-1299 (fechamento) ou retificacao do proprio S-1210 conforme o caso - nunca tentar "reenviar por cima" sem analise.
4. **Comunicacao obrigatoria**: escrever `Mensagem-PC2-N.md` descrevendo o que aconteceu, evidencias e proposta, antes de retomar.
5. **Gate de retomada**: so volto depois de `ok` explicito do PC1 em nova Mensagem-PC1-N.md.

## 5. Estado atual da minha maquina (PC2)

- Supabase conectado (session pooler).
- Backend Node 3333 OK, Frontend Vite 5173 OK, FastAPI bot_api 8000 OK.
- Rota `/api/s1210-repo/por-lote/1/2025-05` retornando 200 com 10.323 CPFs pendentes (Lote 1 / maio).
- Patch local do `b.cpf` foi substituido pelo vindo do pull (fast-forward sem conflito).
- XLSX de Mai/Jun ainda nao localizado no workspace; aguardo orientacao do PC1 sobre caminho/origem dos arquivos para os meses 05 e 06 antes de qualquer ingest.

## 6. Observacoes / itens em aberto para o PC1

1. Caminho/origem do XLSX de **maio e junho/2025** para Lote 1 - esta no repo, em pasta compartilhada, ou precisa gerar a partir da folha?
2. Confirmar que o mes **04/2025 Lote 1** ainda precisa ser enviado (pelo relatorio antigo ele aparece como enviado). Se ja foi, meu escopo real e so 05 e 06.
3. Confirmar empresa alvo (`empresa_id=1` APPA) e se havera alguma outra empresa no escopo desta rodada.
4. Quem executa o script de envio final: o mesmo `bot_api.py` via endpoint, ou script dedicado tipo `_envia_lote1_mes.py`? Preciso saber antes do dry run.

Pronto para iniciar comunicacao operacional.
