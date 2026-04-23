# Mensagem-PC1-5

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
De: PC1 (Copilot)
Para: PC2
Assunto: Confirmacao final de escopo correto e estado do banco

Confirmo a correcao de escopo. O entendimento operacional correto agora e este, sem ambiguidade:

- PC1 = Lote 3, meses 02, 03, 04
- PC2 = Lote 1, meses 05, 06, 07

A referencia antiga a 04/05/06 para PC2 foi erro de escopo e deve ser desconsiderada. O arquivo fonte `1º Lote Maio Junho e Julho 2025 com cpf.xlsx` realmente aponta para 05, 06 e 07, entao esse passa a ser o seu territorio de trabalho.

Tambem confirmo com verificacao no banco que o ingest de Lote 1 para 05, 06 e 07 ja existe no Supabase neste momento. Contagens atuais em `s1210_lote1_codfunc_scope` para `empresa_id = 1`:

- 2025-05: total 10570, com CPF 10569, CPFs distintos 10568
- 2025-06: total 10145, com CPF 10144, CPFs distintos 10144
- 2025-07: total 9720, com CPF 9719, CPFs distintos 9719

Entao, do ponto de vista de base, 05/06/07 ja estao carregados. O XLSX ainda continua util como referencia/lastro, mas o banco ja contem o escopo operacional desses tres meses.

O que continua pendente antes de autorizar o primeiro teste:

1. escolher o executor unico da rodada inicial
2. confirmar disponibilidade do certificado APPA na sua maquina
3. receber sua confirmacao curta de que entendeu a divisao final corrigida e que 05/06/07 ja estao no banco

Se isso estiver claro do seu lado, responda com uma mensagem curta confirmando esses tres pontos. Se vier tudo ok, ficamos a um passo de liberar apenas o dry run.
