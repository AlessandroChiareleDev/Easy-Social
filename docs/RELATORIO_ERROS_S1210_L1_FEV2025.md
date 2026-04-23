# Relatório de Erros — S‑1210 · Lote 1 · Fev/2025

> **Escopo:** rodada executada em 21/04/2026 no compartimento **Lote 1 · 2025-02**.
> **Status:** backfill do histórico legado + retificações em massa (S‑1210 com `indRetif=2`).
> **Propósito:** mapear todos os tipos de erro que apareceram, levantar hipóteses do que pode estar causando cada um, e apresentar opções de solução para discussão.
> **Instrução do usuário:** não implementar correção nenhuma ainda. Só relatório + perguntas no final.

---

## 1. Números gerais

| Status     | Qtd   | % do total |
| ---------- | ----- | ---------: |
| `ok`       | 643   |     62,2 % |
| `erro`     | 386   |     37,4 % |
| `enviando` | 4     |      0,4 % |
| **Total**  | 1.033 |      100 % |

> Observação: o compartimento inteiro tem **~9.470 CPFs** (8.443 ainda pendentes). Este relatório analisa só os 1.033 que já foram processados.

### Distribuição dos erros

| Etapa                                      | Qtd | % dos erros |
| ------------------------------------------ | --- | ----------: |
| `processamento_rejeitado` (cdResposta 401) | 343 |      88,9 % |
| `buscar_recibo` (pré‑eSocial)              | 43  |      11,1 % |

### Ocorrências dentro dos 343 rejeitados (cdResposta 401)

| Ocorrência | Qtd | Descrição curta                                                                                      |
| ---------: | --- | ---------------------------------------------------------------------------------------------------- |
|   **1089** | 216 | "Evento foi enviado ao mesmo tempo em mais de um lote" (duplicidade por simultaneidade)              |
|    **543** | 81  | "Já existe na base de dados do Ambiente Nacional um evento com mesmo identificador"                  |
|    **459** | 43  | "Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado" |
|      **8** | 3   | "Grupo 'Informação dos beneficiários da pensão alimentícia' deve ser preenchido"                     |

### Status dos OK (para referência)

- **641/643** com `nr_recibo_usado` preenchido → são retificações (`indRetif=2`) que o AN aceitou.
- **2/643** sem `nr_recibo_usado` → provavelmente **backfill do histórico legado** (registro criado sem passar pelo webservice — ver `descricao_resposta = "backfill do histórico legado"`).

---

## 2. Erro 1089 — 216 casos (56 % de todos os erros)

### O que o eSocial diz

> "Um evento foi enviado ao mesmo tempo em mais de um lote ou dois ou mais eventos foram gerados e enviados para o mesmo identificador."

### Padrão observado nos dados

- **216/216** têm `nr_recibo_usado` preenchido (são retificações).
- Os recibos estão numa **faixa muito próxima**: `1.1.0000000039950751756`, `1.1.0000000039950752369`, `1.1.0000000039950753553`, `1.1.0000000039950756607`, `1.1.0000000039950760062` …
- Todos os recibos que batem no 1089 começam com **`3995075...` / `3995076...`** — aparentam ter sido **transmitidos originalmente no mesmo lote físico do eSocial** (sequencial contíguo de milhares de recibos).
- Os 216 casos foram registrados em `enviado_em` num intervalo de poucos minutos (17:54 → 18:30 do dia 21/04).

### Hipóteses (por ordem de probabilidade subjetiva)

1. **Concorrência do nosso próprio bot** — o player roda com `CONCURRENCY=3` workers simultâneos. Se dois workers pegarem CPFs que compartilham o mesmo recibo-base no AN, o AN rejeita o 2º com 1089. Isso explicaria o pico: faixa contígua + horário muito próximo.
2. **Retificação concorrente do próprio AN** — o AN processa por lotes internos; se dois eventos nossos chegam antes dele fechar o processamento do primeiro, o 2º cai em 1089. Pouco provável com envio sequencial.
3. **Duplicidade interna no legado** — o próprio recibo antigo pode ter sido usado em mais de um S‑1210 original (bug antigo da APPA). O AN manteria duas cadeias e nossa retificação "empata".

### Dica técnica

A ocorrência 1089 **é recuperável**: basta **reenviar o mesmo CPF depois de alguns minutos**. O AN processa o lote anterior e libera a retificação.

---

## 3. Erro 543 — 81 casos (21 % dos erros)

### O que o eSocial diz

> "Já existe na base de dados do Ambiente Nacional um evento com mesmo identificador (Identificador: ID…)."

### Padrão observado

- **81/81** têm `nr_recibo_usado` preenchido.
- Recibos na faixa `3995077...` / `3995086...` — semelhante ao 1089, porém mais dispersos.
- Todos são retificações que **caíram duas vezes** na mesma cadeia.

### Hipóteses

1. **Reenvio duplicado nosso** — o bot enviou a mesma retificação duas vezes (crash/retry sem checagem). Na 2ª vez o AN rejeita com 543 porque o ID do evento é idempotente.
2. **O evento já existia** — o CPF já tinha sido retificado em algum momento (manual ou por outra rodada) e agora estamos tentando de novo.
3. **Identificador Evento colidindo** — o `Id` do XML (padrão `ID + tpInsc + nrInsc + timestamp`) está sendo gerado com o **mesmo timestamp** para dois XMLs diferentes.

### Diferença crítica 543 vs 1089

- **1089** = "chegou ao mesmo tempo, reprocesse" → recuperável só reenviando.
- **543** = "já está gravado, não precisa reenviar" → pode ser tratado como **sucesso** (o evento está lá, só não é o nosso recibo).

---

## 4. Erro 459 — 43 casos (11 % dos erros)

### O que o eSocial diz

> "Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado."

### Padrão observado

- **43/43** têm `nr_recibo_usado` preenchido.
- Os recibos são muito **mais antigos**: `1.1.0000000031450225924`, `1.1.0000000031450251693`, `1.1.0000000031450224499`, `1.1.0000000031450336242` — começam com **`3145...`** em vez de `3995...`.
- Essa faixa `3145...` é **cronologicamente muito anterior** à dos recibos que estão dando OK.

### Hipóteses

1. **O recibo anterior já foi excluído ou substituído** — alguém (nós ou o cliente via outro sistema) enviou depois do legado um `S‑3000` excluindo, ou retificou com outro recibo que passou por cima.
2. **Recibo inválido no legado** — a origem do `nr_recibo_usado` no banco está errada: o banco da APPA pode ter gravado recibo de outro período/CPF.
3. **Evento retificado em cadeia** — o recibo `3145...` foi retificado por outro sistema e virou `3995...`; nosso S‑1210 tenta retificar o antigo e o AN diz "esse você já mexeu, use o mais novo".

### Como validar

Para cada CPF 459, seria preciso:

- Solicitar download cirúrgico (S‑5001) do mês para pegar o recibo **vigente** do CPF, e
- Comparar com `nr_recibo_usado` que está no banco.

> **⚠️ Consumo de quota** — validação exige consultas ao eSocial. A minha orientação persistente é **não consultar sem autorização explícita do usuário**, por causa do limite de 10/dia do Download Cirúrgico.

---

## 5. Erro 8 — 3 casos (<1 % dos erros)

### O que o eSocial diz

> "Grupo 'Informação dos beneficiários da pensão alimentícia' deve ser preenchido. Verifique as condições…"

### Padrão observado

- Todos os 3 CPFs têm rubrica de pensão alimentícia na folha.
- O XML não incluiu o grupo `<infoBenef>` com CPF/nome do beneficiário.

### Hipótese única

- O **gerador de XML** não está preenchendo o grupo `infoBenef` quando detecta rubrica 1801/1809 ("Desconto de pensão"). Isso é um **bug de conteúdo**, não de integração.

### Implicação

- Esses 3 CPFs pertencem logicamente ao **Lote 4** (pensão alimentícia), não ao Lote 1. Provavelmente foram classificados errado no compartimentamento inicial, ou o Lote 1 está capturando CPFs com folha mista (remuneração normal + pensão).

---

## 6. `buscar_recibo` — 43 casos (11 % dos erros)

### O que significa

Etapa **antes** do envio ao eSocial. O nosso pipeline tenta buscar o `nr_recibo_usado` em um ZIP de S‑5001 baixado previamente, e não encontra o CPF lá dentro.

### Padrão observado

- **43/43** sem `nr_recibo_novo` **e** sem `nr_recibo_usado` — a etapa de busca falhou antes de montar o XML.
- A mensagem é sempre: `"Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF XXXXX"`.

### Hipóteses

1. **O ZIP do S‑5001 não foi completo** — o download cirúrgico pegou um subconjunto do mês e esses CPFs não estavam nele.
2. **CPFs sem envio original** — o legado nunca enviou S‑1210 pra esses 43 CPFs em Fev/2025. Consequentemente não tem recibo para retificar — deveria ser **envio original** (`indRetif=1`), não retificação.
3. **CPFs inativos / desligados** — estavam afastados no mês, não geraram folha, mas foram incluídos no lote pelo critério atual.

### Pista

No relatório antigo do compartimento todo, aparecem 2 CPFs OK com `descricao_resposta = "backfill do histórico legado"`. Esses pareciam sem recibo também, mas foram marcados como OK "manualmente" (sem passar no webservice). Isso indica que já existe uma saída tratada em algum ponto, mas não está sendo aplicada a esses 43.

---

## 7. Visão consolidada — "O que dá pra fazer a mais"

| Tipo          | Qtd | Recuperável?                           | Ação sugerida (rascunho)                             |
| ------------- | --- | -------------------------------------- | ---------------------------------------------------- |
| 1089          | 216 | **Sim**, reenviando depois de ~5 min   | Loop de retry automático com back‑off                |
| 543           | 81  | **Não precisa** — evento já existe     | Marcar como "ok_idempotente" e seguir                |
| 459           | 43  | **Talvez** — precisa recibo atualizado | Rebuscar recibo vigente do CPF (custa quota)         |
| 8             | 3   | **Não** — é bug de XML                 | Gerar com grupo `infoBenef` ou mover p/ L4           |
| buscar_recibo | 43  | Parcial — depende do caso              | Diferenciar "sem envio anterior" vs "ZIP incompleto" |

---

## 8. Hipóteses transversais (por que uns passam e outros não?)

Observando que **62 % passa** e **37 % falha**, o determinante não é o XML em si (senão falharia tudo). Os padrões sugerem:

1. **Concorrência do próprio bot** — CONCURRENCY=3 pode estar criando choque no AN em faixas contíguas de recibo.
2. **Qualidade dos dados no banco legado** — `nr_recibo_usado` em alguns CPFs está obsoleto (459) ou vazio (buscar_recibo).
3. **Classificação dos lotes** — alguns CPFs do Lote 1 pertencem a Lote 4 (pensão alimentícia, ocorrência 8).
4. **Idempotência invisível** — retificações que já rodaram em outra sessão voltam como 543; não é "erro" de verdade.

---

## 9. Opções de solução (rascunhos para discutir)

Cada opção abaixo é **um candidato**, não uma recomendação definitiva. Você decide pela resposta que virá no próximo arquivo.

### Opção A — Classificar 543 como sucesso

- Tratar cdResposta 401 + ocorrência 543 como `ok` com marcação especial (`idempotente`).
- **Prós:** zera 81 erros imediatamente.
- **Contras:** perdemos o `nr_recibo_novo` desse envio (fica só o `usado`). Auditoria pode questionar.

### Opção B — Retry automático para 1089

- Guardar CPFs 1089 numa fila e reenviar N minutos depois (5, 10, 20 em back‑off).
- **Prós:** recupera ~216 casos sozinho.
- **Contras:** gasta mais tempo por CPF; se o AN demorar muito a processar, a fila cresce.

### Opção C — Reduzir concorrência

- Baixar `CONCURRENCY` de 3 para 1 (envio serial).
- **Prós:** elimina causa raiz do 1089.
- **Contras:** triplica o tempo total (de 6 min / 38 CPFs → 18 min / 38 CPFs).

### Opção D — Revalidar recibos antes de montar XML (459)

- Antes de gerar o XML, comparar `nr_recibo_usado` com um `S‑5001` recém‑baixado.
- **Prós:** resolve os 459 e detecta inconsistências.
- **Contras:** custa **1 consulta por CPF** no eSocial → inviável para 8.443 CPFs pendentes (limite 10/dia).

### Opção E — Mover CPFs com pensão para Lote 4

- Detectar na geração do XML se o CPF tem rubrica 1801/1809 e, se sim, repor a classificação no banco.
- **Prós:** resolve os 3 erros de ocorrência 8 + evita mais no futuro.
- **Contras:** exige ajuste no critério de compartimento + rerodar o classificador.

### Opção F — Fluxo "envio original" para CPFs sem recibo

- Para os 43 `buscar_recibo`, tentar envio com `indRetif=1` (original) em vez de retificação.
- **Prós:** recupera casos de CPFs nunca enviados.
- **Contras:** se o CPF **já tem** um S‑1210 no AN (e o nosso ZIP é que está incompleto), vira ocorrência 543.

### Opção G — Não fazer nada com 459 e buscar_recibo

- Aceitar esses 86 casos como "pendência humana" e mover para uma aba separada de revisão manual.
- **Prós:** sem gasto de quota, sem risco de degradar mais.
- **Contras:** não fecha o compartimento.

---

## 10. Perguntas para você responder no próximo arquivo

> Escreva as respostas num MD separado e me devolve. Vou implementar o que você decidir.

### Q1 — Ocorrência 543 ("já existe")

Como quer tratar? Opções: **(a)** considerar sucesso e mover pra `ok`; **(b)** manter como erro e revisar manualmente; **(c)** outro.

### Q2 — Ocorrência 1089 ("simultaneidade")

**(a)** Implementar retry automático com back‑off (qual: 5/10/20 min? quantas tentativas?); **(b)** reduzir concorrência para 1; **(c)** combinação das duas; **(d)** outro.

### Q3 — Ocorrência 459 ("recibo excluído / retificado")

**(a)** Rebuscar recibo por CPF no eSocial (custa quota — aceitar); **(b)** marcar como pendência manual; **(c)** tentar envio original `indRetif=1` e ver o que volta; **(d)** outro.

### Q4 — Ocorrência 8 ("pensão alimentícia sem beneficiário")

**(a)** Mover CPFs pra Lote 4 e tratar em fluxo separado; **(b)** gerar o grupo `infoBenef` também no Lote 1 quando detectar rubrica de pensão; **(c)** outro.

### Q5 — `buscar_recibo` (43 CPFs sem recibo em ZIP)

**(a)** Enviar como original (`indRetif=1`); **(b)** baixar um S‑5001 novo cobrindo o mês inteiro; **(c)** mover para aba de pendência manual; **(d)** outro.

### Q6 — Concorrência do bot

Mantém `CONCURRENCY=3` ou reduz para 1/2?

### Q7 — Prioridade

Qual tipo de erro você quer atacar primeiro? (importa pra decidir por onde eu começo)

### Q8 — Fora do escopo de erros

Algum padrão que você notou e que eu não analisei aqui? (ex.: tem CPF que caiu em 1089 **duas vezes**? vale rastrear isso?)

---

## 11. Dados brutos usados neste relatório

- Query de contagem: `SELECT status, COUNT(*) FROM s1210_cpf_envios WHERE lote_num=1 AND per_apur='2025-02' GROUP BY status`
- Query de erros: `SELECT DISTINCT ON (cpf) ... WHERE status='erro' ORDER BY cpf, enviado_em DESC`
- Scripts geradores: [python-scripts/\_levantar_erros.py](python-scripts/_levantar_erros.py), [python-scripts/\_analise_padroes.py](python-scripts/_analise_padroes.py)
- Data da rodada: **2026-04-21 17:54 → 18:46 (UTC)**
- Backend: `bot_api.py` PID 26212, `localhost:8000`

---

_Fim do relatório. Não foram feitas alterações no código. Aguardando respostas para iniciar implementação._
