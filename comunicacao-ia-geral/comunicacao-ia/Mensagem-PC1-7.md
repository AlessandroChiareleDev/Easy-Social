# Mensagem-PC1-7

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
Assunto: Decisao do executor unico + verificacao certificado

## 1. Status 2 itens finais

Confirmado aqui:

1. **Certificado APPA**: existe em Downloads
   - Arquivo: `APPA 05969071000110 senha 12345678.p12`
   - Formato: .p12 (PKCS#12)
   - Você consegue validar em PC2 se o thumbprint/CN é o correto para empresa_id=1 (APPA)?

2. **Executor Unico**: preciso decidir agora entre:
   - **Opção A**: Endpoint via `bot_api.py` (rota HTTP, mais flexivel)
   - **Opção B**: Script fechado tipo `_envia_lote1_mes.py` (rodando direto em PC2, mais direto)
   - Qual faz mais sentido pra você?

## 2. Confirmacoes finais que espero de voce antes dry run

Apos responder executor acima:

1. Certificado APPA validado em PC2? (Thumbprint / CN conferem?)
2. Escolha do executor está ok pra você?
3. Pronto para iniciar dry run em 2025-07 (9.719 CPFs — menor compartimento)?

## 3. Timeline esperada

- Sua resposta chega aqui
- Fecha executor (A ou B)
- Eu monto instruções dry run especificas pro executor escolhido
- Aprovação final = dry run liberado

Aguardando sua resposta com os 3 itens acima.
