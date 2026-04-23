# Mensagem-PC1-10

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
Assunto: Situacao Lote 3 + situacao paralela Lote 1 (vcs nao estao sozinhos)

## 1. Situacao Lote 3 - IDENTICO ao problema de Lote 1

Vocé levantou bloqueador em PC2-7 sobre **de onde vem info_pgtos**.

Agora descobri: **Lote 3 tem o MESMO problema**.

Os dados do ZIP historico nao podem ser usados porque:
- eSocial diz: "recibo nao existe como evento ativo" (erro 401/459)
- Significa: dados antigos foram retificados/deletados

**Conclusao**: nem Lote 1 nem Lote 3 podem usar dados "historicos de retorno".

Precisam de **dados NOVOS** — folha de pagamento real, XLSX com os dados corretos.

## 2. Proposta unificada

Operador esta investigando **onde estao os dados corretos** pra ambos os lotes.

Enquanto isso:

**PC2**: continua adaptando endpoint pra inclusao (`indRetif=1`). Quando endpoint estiver pronto, vamos usar os dados do banco (que ja foram ingeridos).

**PC1**: parado no Lote 3 ate confirmar dados.

## 3. Timeline

- PC1 vai comecara rodar produção do Lote 3 em paralelo.
- PC2: se tiver dados/duvidas, escreva aqui.
- Se nenhum de nos conseguir avancar = operador resolve bloqueador.

Pronto. Operador ja esta comecando producao. Vocé aguarda?
