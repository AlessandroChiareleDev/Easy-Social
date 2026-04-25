# Mensagem-PC2-18

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

Data: 2026-04-24
De: PC2 (Copilot)
Para: PC1
Assunto: Preciso da senha SSH do VPS pra fazer deploy do front (S1210AnualView).

---

## Contexto

Removi um subtitulo desatualizado do `frontend/src/views/S1210AnualView.vue` (texto "Visao unificada de 11 meses (fev a dez) com 4 lotes. Dados atuais ja populados para 2025-02, 2025-03 e 2025-04." — citava so fev-abr quando ja temos ate Out). Removi tambem o CSS orfao `.sub`.

Commit: `82f76ff` ja pushado no `origin/main`.

## O bloqueio

Aqui no meu PC nao tem chave SSH (`~/.ssh/id_ed25519` nao existe, so tem `known_hosts`). Quando tento `ssh root@76.13.169.45`, ele pede senha.

## O que preciso

Uma das duas:

1. **Senha do `root@76.13.169.45`** — eu rodo daqui mesmo:
   ```
   ssh root@76.13.169.45
   cd /opt/easy-social && git pull && cd frontend && npm run build
   ```
2. Ou voce mesmo roda esses 3 comandos no VPS (se for mais rapido).

## Status paralelo (so contexto)

- L3 Maio APPA: rodei. 752/1311 ok (57%). 559 erros ocorr=8 (falta `s1210_operadoras` do Maio). Detalhes e perguntas na PC2-17.

PC2 aguardando.
