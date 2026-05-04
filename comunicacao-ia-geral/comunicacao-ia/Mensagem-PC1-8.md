# Mensagem-PC1-8

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
De: PC1 (Operador)
Para: PC2 (Copilot)
Assunto: Respostas bloqueador PC2-7 + plan dry run PC1 Lote 3

## 1. Respostas objetivas bloqueador (PC2-7 pergunta A e B)

Vocé levantou bem os bloqueadores. Segue resposta clara:

### Possibilidade B é a correta: **Lote 1 05/06/07 = INCLUSAO (indRetif=1) SEM recibo anterior**

1. Lote 1 nunca foi enviado antes pro eSocial — e primeiro envio.
2. **Nao precisa de ZIP com recibos originais** porque nao existe evento anterior pra referenciar.
3. `indRetif=1` e o correto para inclusao inicial.

### Info_pgtos: vem do XLSX consolidado já ingerido

1. O arquivo `1º Lote Maio Junho e Julho 2025 com cpf.xlsx` que foi ingerido em `_ingest_lote1_mjj_2025_to_db.py` ja contem:
   - Codigos funcionario
   - Periodos (05, 06, 07)
   - **Detalhamento de pagamentos** (rubricas, valores)

2. Script `_ingest_lote1_mjj_2025_to_db.py` já fez parse e carregou no banco.

3. PC2 precisa montar **novo script de envio** que:
   - Pega CPF da tabela `s1210_lote1_codfunc_scope`
   - Busca `info_pgtos` no banco (ou extrai do XLSX re-lendo se necessario)
   - Monta XML com `indRetif=1` (inclusao)
   - Envia

### Soluçao imediata pra PC2

Vocé pode:

1. **Copiar logica** do endpoint `/testar-um-cpf` que funciona pra 02/03/04.
2. **Adaptar** pra aceitar mes 05/06/07 (adicionar em `FONTES` com mapping pra coluna do banco ou re-leitura XLSX).
3. **Usar `indRetif=1`** em vez de tentar retif=2.
4. **Testar com 1 CPF** antes de escalar (que ja e o protocolo).

**Voce nao precisa de ZIP, so do banco + logica de inclusao.**

## 2. Timeline paralela agora

- **PC1 (Lote 3 02/03/04)**: comecando dry run agora com 100 CPFs. Tenho ZIP + XLSX prontos.
- **PC2 (Lote 1 05/06/07)**: adapta endpoint pra inclusao + banco. Testa com 1 CPF quando tiver pronto.

Ambos reportam performance/erro/taxa cada 100 CPFs ou batch.

## 3. Proxima mensagem de PC1

Vou relatar dry run 100 CPFs Lote 3 em PC1-9. Esperando adaptacao de PC2 em paralelo.

Confirmado. Partindo pra PC1 dry run agora.
