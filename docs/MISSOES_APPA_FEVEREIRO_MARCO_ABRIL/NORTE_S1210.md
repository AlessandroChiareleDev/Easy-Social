# NORTE — Repositório S-1210 (Retificações 3 Meses)

> Este MD é o **norte** do que o usuário pediu na conversa. Sem invencionice. Sem especificação técnica. Só **como vai ficar na tela** e **como vai ser dividido**. Antes de codar qualquer coisa, volto aqui, releio, confirmo que estou seguindo.

---

## 1. Onde vai ficar

Do lado do **Repositório S-1010** que já existe. É o irmão do S-1010 só que pra S-1210. A pessoa entra no sistema, vê os dois lado a lado: "Repositório S-1010" e "Repositório S-1210". Mesma cara, mesma lógica, mesmo jeito de operar.

---

## 2. Como vai ser dividido — 2 VERTENTES

Quando a pessoa clica no Repositório S-1210, **antes de qualquer dashboard, aparecem 2 opções** (2 vertentes). A pessoa escolhe uma e entra num dashboard **diferente** pra cada uma.

### Vertente A — Por Lote

Dashboard organizado por **Grande Lote**. Dentro de cada lote, os 3 meses.

```
Grande Lote 1 (sem plano de saúde)
  ├── 2025-02
  ├── 2025-03
  └── 2025-04

Grande Lote 2 (operadora A)
  ├── 2025-02
  ├── 2025-03
  └── 2025-04

Grande Lote 3 (operadora B)
  ├── 2025-02
  ├── 2025-03
  └── 2025-04

Grande Lote 4 (manuais)
  ├── 2025-02
  ├── 2025-03
  └── 2025-04
```

Use quando a pessoa quer focar em **1 lote inteiro** ao longo dos 3 meses.

### Vertente B — Mensal

Dashboard organizado por **Mês**. Dentro de cada mês, todos os 4 grandes lotes juntos.

```
2025-02
  ├── Grande Lote 1
  ├── Grande Lote 2
  ├── Grande Lote 3
  └── Grande Lote 4

2025-03
  ├── Grande Lote 1
  ├── Grande Lote 2
  ├── Grande Lote 3
  └── Grande Lote 4

2025-04
  ├── Grande Lote 1
  ├── Grande Lote 2
  ├── Grande Lote 3
  └── Grande Lote 4
```

Use quando a pessoa quer focar em **1 mês inteiro**, vendo todos os lotes daquele mês lado a lado.

### Resumo

- 2 vertentes = 2 dashboards distintos.
- Mesmos dados, **arrumação diferente**.
- Cada compartimento final (lote × mês) é o mesmo em qualquer vertente.

---

## 3. O que cada compartimento mostra

Dentro de "Grande Lote 1 → 2025-02" (exemplo), a pessoa vê:

- **Contador em cima:** quantos CPFs no total / quantos já OK / quantos com erro / quantos pendentes.
- **Tabela de CPFs:** cada linha é um funcionário, com status colorido (OK verde, erro vermelho, pendente cinza, em envio amarelo).
- **Botão "Enviar este lote":** dispara só esse compartimento.
- **Botão "Retry só os erros":** reenvia só quem falhou.
- **Botão "Pausar envio":** trava tudo que tá rolando agora.
- **Botão "Retomar":** continua de onde parou.
- **Botão "Parar":** mata o envio.

Quem já foi (tem S-1210 aceito no eSocial) **sai da contagem de pendentes**. Não reprocessa. Só aparece na lista como "feito" pra registro histórico.

---

## 4. Terminal de erro em tempo real

Dentro do próprio sistema, uma **aba/painel de terminal** que roda do lado:

- Mostra em tempo real: cada CPF que está sendo enviado, resposta do eSocial, erro retornado, motivo.
- Cor por severidade (erro vermelho, aviso amarelo, sucesso verde).
- Enquanto a pessoa olha o terminal rodando, ela pode **pausar / parar / retomar** com os botões.
- Filtra o terminal por lote ou mês — só mostra o que interessa.
- Pode exportar o log pra arquivo depois.

Isso é o que hoje eu fico olhando no PowerShell. Vai virar painel dentro do sistema.

---

## 5. Banco de dados — pra que serve aqui

O banco **não é a interface**. A interface é o front. Mas o front precisa de um lugar pra guardar tudo isso, então o banco precisa estar preparado pra receber:

- A lista dos CPFs de cada Grande Lote × Mês (vem da XLSX da Ana quando a pessoa sobe o arquivo).
- O status atual de cada CPF (pendente, em envio, OK com nrRecibo, erro com mensagem).
- Histórico de cada tentativa (quando mandou, o que o eSocial respondeu).
- Quem já tem S-1210 anterior aceito (pra marcar como "feito" e tirar da contagem).
- A operadora de plano de saúde de cada grande lote 2 e 3 (vem da aba `Operadoras` da XLSX).

**O banco é o alicerce. A tela é a obra.** Sem o banco preparado, a tela não tem o que mostrar nem onde salvar.

---

## 6. Entrada do fluxo (como a pessoa começa)

1. Abre o "Repositório S-1210".
2. Sobe as 3 XLSX da Ana (Fev, Mar, Abr).
3. O sistema parseia, monta os 4 grandes lotes × 3 meses automaticamente, e cruza com o que já existe (pra marcar quem já foi).
4. Mostra a árvore toda preenchida, com os contadores certos.
5. A partir daí, a pessoa escolhe: vou mexer no Grande Lote 1 de Fevereiro → clica → vê os CPFs → manda enviar → acompanha no terminal.

---

## 7. O que a pessoa consegue fazer (resumo)

- Ver tudo dividido por Grande Lote e por Mês.
- Filtrar 1 mês, 1 lote, ou 1 mês de 1 lote só.
- Disparar envio por compartimento.
- Acompanhar em tempo real pelo terminal interno.
- Pausar, parar, retomar.
- Retry só dos erros.
- Quem já foi fica marcado como feito e não entra na conta.

---

## 8. O que NÃO vai ter aqui

- Nada de rodar script Python na mão.
- Nada de olhar tabela do banco direto.
- Nada de ficar no PowerShell lendo log.
- Nada de CPF avulso fora da árvore de grande lote × mês (exceção: Grande Lote 4, que é o compartimento dos manuais).

---

## 9. Próximo passo

Com este norte aprovado pelo usuário, vou:

1. Preparar o banco pra aguentar tudo que está descrito aqui.
2. Depois construir a tela do Repositório S-1210 do lado da do S-1010.
3. Depois o terminal em tempo real.
4. Depois os botões de pausar / parar / retomar.

**Aguardando leitura e aprovação do usuário deste norte antes de começar.**
