# MISSÃO — Visualização Completa do Repositório S-1210

**Data de abertura:** 21/04/2026
**Status:** ATIVA
**Pré-requisito lido:** [LEIA_PRIMEIRO.md](LEIA_PRIMEIRO.md) · [NORTE_S1210.md](NORTE_S1210.md) · [FONTES_MISSAO.md](FONTES_MISSAO.md) · [RESOLUCAO_S1210_3_MESES.md](RESOLUCAO_S1210_3_MESES.md)

> Este MD aterrissa o que o usuário pediu em 21/04/2026 às ~11h07: a **visualização completa** do Repositório S-1210 — com as **2 vertentes** (por Lote e Mensal), o drill-down até **lista de CPFs** dentro de cada compartimento, e a persistência dos XLSX **dentro do sistema** (nunca mais re-upload).
>
> Nada de terminal. Nada de script manual. Nada de "abrir DB na mão". Só tela.

---

## 0. Fontes da missão (definitivo — 21/04/2026)

### 0.1 As 3 planilhas da Ana — **onde mora a divisão dos 4 lotes**

As 3 XLSX da Ana têm muitas abas, mas **só uma** interessa pra definir o escopo dos lotes. Essa aba tem uma **coluna G (7ª coluna)** onde cada linha traz o texto do lote daquele CPF (`1º Lote`, `2º Lote`, `3º Lote`, `4º Lote`). É essa coluna que o parser lê pra montar os 4 compartimentos. Não existe aba separada por lote — todo mundo está numa única aba, e o lote é só uma coluna.

**Problema:** a Ana nomeou essa aba **com grafia diferente em cada mês**. Mesma aba, mesma função, nome escrito diferente:

| Mês     | Nome exato da aba no arquivo | Coluna do lote | Coluna do CPF |
| ------- | ---------------------------- | -------------- | ------------- |
| 2025-02 | `Geral Para Envio_Lotes`     | G (índice 6)   | H (índice 7)  |
| 2025-03 | `Geral Para envio de Lotes`  | G (índice 6)   | H (índice 7)  |
| 2025-04 | `Geral Envio para Lotes`     | G (índice 6)   | H (índice 7)  |

O parser mapeia cada mês → nome exato da aba num dicionário `FONTES` (em `python-scripts/esocial/s1210_missao_routes.py`). Se a Ana mandar nova versão com outro nome, basta atualizar esse dicionário.

### 0.2 Aba das operadoras (só lotes 2 e 3)

Na mesma XLSX há uma segunda aba com o mapa de operadora por CPF (códigos ANS + CNPJ da operadora) — usada só para **Lote 2** (operadora da rubrica 775) e **Lote 3** (operadora da rubrica 774). Também tem nome diferente por mês:

| Mês     | Nome exato da aba   |
| ------- | ------------------- |
| 2025-02 | `Operadoras_012025` |
| 2025-03 | `Operadora 022025`  |
| 2025-04 | `Operadoras 032025` |

### 0.3 Os 3 ZIPs do eSocial (Download Cirúrgico) — **onde moram os recibos e dados de envio**

Além das 3 XLSX, a missão depende de 3 ZIPs enormes baixados do eSocial em 10/04/2026. Cada ZIP tem ~51.000 XMLs do mês (S-1200, S-1210, S-5001, S-5002, S-5011, S-5012). O ZIP do S-1210 traz, pra cada CPF, o **nrRecibo do último S-1210 conhecido** naquele download, as rubricas, `detPgtos`, `infoIRComplem`, tudo que a gente precisa pra montar a retificação.

| Mês     | Arquivo ZIP oficial      | Tamanho |
| ------- | ------------------------ | ------- |
| 2025-02 | `29429415 fev2025.zip`   | ~524 MB |
| 2025-03 | `29429449 marc2025.zip`  | ~524 MB |
| 2025-04 | `29429512 abril2025.zip` | ~554 MB |

Pasta: `C:\Users\xandao\Downloads`. São lidos em **streaming** (sem extrair) com `zipfile.ZipFile + lxml.iterparse`.

### 0.4 Sincronização ZIP × eSocial — o porquê dos recibos "virem de outro lugar"

Os ZIPs foram baixados em **10/04/2026**. Hoje é **21/04/2026**. Nesses 11 dias, **retificações novas de S-1210 podem ter acontecido** (o próprio GPT antigo fez massa de envios entre 13–17/04 em janeiro e 20/04 em fevereiro). Consequência: o `nrRecibo` que aparece dentro do ZIP **pode estar desatualizado** — ou seja, aquele S-1210 já não é mais o ativo, foi retificado por um recibo mais novo que o ZIP não viu.

**Solução que funcionou nos 2 CPFs testados hoje** (sem gastar cota do eSocial de consulta — já gastamos muito):

1. O XML do S-1210 dentro do ZIP é parseado e extraído o `nrRecibo`, `ideDmDev` e campos de pagamento.
2. A função `_buscar_recibo_ativo(cpf, s1210)` anda a **cadeia de retificações** usando o `ideDmDev` (identificador do demonstrativo) + dados do envelope — se existe um S-1210 mais recente pro mesmo `ideDmDev` dentro do ZIP (indRetif=2 apontando pro original), ela pega o recibo mais novo.
3. O resultado é o "recibo ativo" efetivo no momento do envio. Foi assim que os 2 CPFs testados obtiveram os recibos originais corretos e fecharam a retificação:

| CPF         | Recibo do ZIP (10/04)     | Recibo ativo usado (chain walk) | Recibo novo após enviar hoje     |
| ----------- | ------------------------- | ------------------------------- | -------------------------------- |
| 01853386669 | `1.1.0000000031450338257` | `1.1.0000000039953737499`       | **`1.1.0000000040108461247`** ✅ |
| 55146015600 | `1.1.0000000031450352181` | `1.1.0000000039981313999`       | **`1.1.0000000040109775609`** ✅ |

A diferença entre "Recibo do ZIP" e "Recibo ativo usado" é exatamente o **problema de sincronização** — o ZIP de 10/04 não viu o que aconteceu depois. Quando a retificação nova sobe hoje, aponta pro recibo ativo verdadeiro e não pro que o ZIP cacheou, senão o eSocial devolveria erro [236]/[237] (recibo informado não é o atual).

**Implicação para o sistema:**

- Persistir no banco **tanto** `nr_recibo_zip` (o que estava no ZIP) **quanto** `nr_recibo_usado` (o que a chain walk escolheu) — importante pra auditoria.
- Quando mostrar "último recibo ativo" na tabela de CPFs, mostrar o `nr_recibo_novo` se já houve envio pela missão nova; se não, mostrar o `nr_recibo_usado` (chain walk do ZIP); se o ZIP nem teve esse CPF, mostrar `—` e marcar o CPF como "sem base no ZIP" (vai pra fila manual).
- Se futuramente o usuário autorizar `ConsultarIdentificadoresTrabalhador`, atualiza-se o `nr_recibo_eSocial_confirmado` e a tabela passa a refletir esse valor — mas enquanto a cota tá congelada, o ZIP + chain walk é a fonte.

### 0.5 Onde tudo isso está no código hoje

- Mapeamento das 3 XLSX + 3 ZIPs + abas: `python-scripts/esocial/s1210_missao_routes.py` → dicionário `FONTES` (linhas ~40–65).
- Parser da aba geral (coluna G = lote, coluna H = CPF): função `_parse_xlsx_escopo` no mesmo arquivo.
- Chain walk do recibo ativo: função `_buscar_recibo_ativo` em `python-scripts/esocial/s1210_batch.py`.
- Cache em memória enquanto não há persistência no banco: `_CACHE_XLSX` e `_CACHE_RECIBOS` (temporários — vão embora assim que a persistência da seção 1 for construída).

---

## 1. Regra zero — XLSX moram dentro do sistema

Hoje a página `/s1210-missao` lê os 3 XLSX direto da pasta `C:\Users\xandao\Downloads` toda vez que carrega. Isso é **errado e frágil** — se o arquivo sumir, mudar de nome, o usuário entrar em outra máquina, quebra.

**Regra nova:** os 3 XLSX oficiais (APPA / Fev-Mar-Abr 2025) ficam **persistidos no sistema**, vinculados à empresa APPA (CNPJ 05.969.071/0001-10), e o parseamento é feito **uma vez só** quando o arquivo entra. O resultado (os 4 lotes × 3 meses × lista de CPFs + operadoras) fica salvo no banco.

### Arquivos oficiais (fonte da verdade)

Confirmados em `C:\Users\xandao\Downloads` em 21/04/2026 11h09:

| Mês     | Nome                                 | Tamanho                      |
| ------- | ------------------------------------ | ---------------------------- |
| 2025-02 | `02. Fevereiro_2025_APPA certa.xlsx` | 42.013.370 bytes (~40,06 MB) |
| 2025-03 | `03. Marco_2025_APPA.xlsx`           | 38.727.752 bytes (~36,93 MB) |
| 2025-04 | `04. Abril_2025_APPA.xlsx`           | 37.927.023 bytes (~36,17 MB) |

Qualquer XLSX com nome diferente é **ignorado**. O sistema aceita só esses 3.

### Como persistir (sem re-upload)

Fluxo de entrada:

1. Usuário abre **Repositório S-1210** → botão **"Carregar XLSX oficiais"** (aparece só se ainda não existe nenhum no banco).
2. Tela lista os 3 arquivos que o sistema encontrou em `Downloads` com os nomes oficiais.
3. Um clique → sistema copia/ingere os 3 arquivos pra storage interno, parseia as abas `Geral para envio de lotes` + `Operadoras`, monta a estrutura dos 4 lotes × 3 meses, cruza com os ZIPs pra marcar quem já tem S-1210 aceito, e salva **tudo no banco**.
4. A partir desse momento, o usuário **nunca mais precisa subir os XLSX**. Entrar na tela = já tá tudo carregado, contadores certos, lista de CPFs pronta.
5. Se o arquivo mudar (Ana mandar uma versão nova), aparece um banner **"Atualizar XLSX da competência X"** pedindo confirmação explícita.

### O que vai no banco (apoio do front)

| Tabela lógica      | Pra que serve                                                                    |
| ------------------ | -------------------------------------------------------------------------------- |
| `s1210_xlsx`       | 1 linha por XLSX oficial ingerido: competência, nome, tamanho, hash, data upload |
| `s1210_cpf_scope`  | 1 linha por CPF × competência × lote (vindo da aba Geral)                        |
| `s1210_operadoras` | mapa CPF × rubrica (774/775/522) × operadora (só lotes 2 e 3)                    |
| `s1210_cpf_envios` | histórico de envios por CPF (data, status, recibo, erro, XML enviado, resposta)  |
| `s1210_cpf_recibo` | último recibo S-1210 ativo conhecido por CPF × competência                       |

Esses nomes são **lógicos** (vão virar tabelas concretas no próximo passo). Nada é mexido em `pipeline_runs` / `pipeline_cpf_results` — aquilo é histórico antigo.

---

## 2. Vertente A — Visualização por Grande Lote

Quando usuário clica **"Por Lote"** na porta de entrada do Repositório S-1210, entra no dashboard orientado a lote.

### Nível 1 — os 4 grandes lotes

```
┌─────────────────────────────────────────────────────────┐
│ Grande Lote 1 — sem plano de saúde                      │
│   2025-02: 9.471 · feito 2 · pend 9.469 · erro 0        │
│   2025-03: 8.164 · feito 0 · pend 8.164 · erro 0        │
│   2025-04: 7.142 · feito 0 · pend 7.142 · erro 0        │
│   TOTAL:  24.777 · feito 2 · pend 24.775 · erro 0       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Grande Lote 2 — 775 odonto coletivo empresarial         │
│   2025-02: 1.390 · feito 0 · pend 1.390 · erro 0        │
│   2025-03: 1.395 · …                                    │
│   2025-04: 1.376 · …                                    │
└─────────────────────────────────────────────────────────┘

... Lote 3 e Lote 4 no mesmo formato ...
```

### Nível 2 — drill no compartimento (Lote X / Mês Y)

Um clique num mês dentro do lote → abre o compartimento. Aqui mora a lista de CPFs.

**Cabeçalho do compartimento:**

- Título: `Grande Lote 1 · Fev/2025 · 9.471 CPFs`
- Contadores grandes (coloridos): `feito 2` (verde) · `pend 9.469` (cinza) · `erro 0` (vermelho) · `enviando 0` (amarelo)
- Botões de ação do compartimento:
  - **▶ Enviar este compartimento** (respeita pausar/retomar)
  - **🔁 Retry só os erros**
  - **⏸ Pausar** / **▶ Retomar** / **⏹ Parar**
- Barra de progresso em tempo real (%)

**Tabela de CPFs** (1 linha por CPF):

| CPF            | Nome | Status        | Último recibo ativo                | Data envio       | Ações                                            |
| -------------- | ---- | ------------- | ---------------------------------- | ---------------- | ------------------------------------------------ |
| 018.533.866-69 | …    | ✅ ok         | `1.1.0000000040108461247`          | 21/04/2026 13:55 | 👁 ver XML · 📥 baixar XML · 🔁 reenviar         |
| 551.460.156-00 | …    | ✅ ok         | `1.1.0000000040109775609`          | 21/04/2026 13:55 | 👁 · 📥 · 🔁                                     |
| 106.410.616-17 | …    | ⚪ pendente   | `1.1.0000000031450345770` (do ZIP) | —                | ▶ enviar                                         |
| 123.456.789-00 | …    | ❌ erro [202] | `1.1.…`                            | 20/04/2026 20:05 | 👁 ver erro · 🔁 reenviar · 📥 baixar último XML |

**Colunas da tabela:**

- **CPF** — formatado `000.000.000-00`, clicável pra abrir ficha do CPF (histórico de envios daquele CPF).
- **Nome** — extraído do XLSX (aba Geral).
- **Status** — uma de: `pendente`, `enviando`, `ok`, `erro`, `já feito (histórico)`.
- **Último recibo ativo** — o `nrRecibo` atual do S-1210 no eSocial pra aquele CPF nesse mês (vindo do ZIP ou do último envio bem-sucedido).
- **Data envio** — timestamp do último envio feito **pela tela** (não conta envios antigos do pipeline legado).
- **Ações por linha:**
  - 👁 **Ver XML** — abre modal com o XML enviado (pretty-print + highlight).
  - 📥 **Baixar último XML** — download do `.xml` da última tentativa.
  - 🔁 **Reenviar** — dispara novamente só esse CPF.
  - 👁 **Ver erro** (só se status=erro) — modal com mensagem do eSocial, código, resposta bruta.

**Filtros em cima da tabela:**

- Busca por CPF/nome.
- Chips de status: `todos` · `só pendentes` · `só erros` · `só ok` · `só enviando`.
- Ordenar por: CPF, nome, data envio, status.
- Paginação (50 por página), com contador total.

---

## 3. Vertente B — Visualização Mensal

Quando usuário clica **"Mensal"** na porta de entrada, entra no dashboard orientado a mês.

### Nível 1 — os 3 meses

```
┌─────────────────────────────────────────────────────────┐
│ 2025-02 — Fev · 11.600 CPFs                             │
│   Lote 1: 9.471 · feito 2 · pend 9.469 · erro 0         │
│   Lote 2: 1.390 · feito 0 · pend 1.390 · erro 0         │
│   Lote 3:   737 · feito 0 · pend 737   · erro 0         │
│   Lote 4:     2 · feito 0 · pend 2     · erro 0         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 2025-03 — Mar · 11.185 CPFs                             │
│   (mesmo desenho)                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 2025-04 — Abr · 10.016 CPFs                             │
│   (mesmo desenho)                                       │
└─────────────────────────────────────────────────────────┘
```

### Nível 2 — lista geral do mês com 4 divisores

Um clique num mês → abre a **lista completa** daquele mês, uma tabela só, **com 4 divisores** (accordion expansível):

```
┌── Lote 1 — sem plano ──────────────── [9.471 CPFs] [▼] ┐
│  (tabela completa igual à do compartimento Vertente A) │
└────────────────────────────────────────────────────────┘

┌── Lote 2 — 775 odonto ─────────────── [1.390 CPFs] [▶] ┐  (fechado)
└────────────────────────────────────────────────────────┘

┌── Lote 3 — 774 coletivo ──────────────  [737 CPFs] [▶] ┐
└────────────────────────────────────────────────────────┘

┌── Lote 4 — manuais ───────────────────    [2 CPFs] [▼] ┐
│  (tabela)                                              │
└────────────────────────────────────────────────────────┘
```

Botões de compartimento (Enviar/Retry/Pausar/Parar) aparecem **em cada divisor**, pra usuário agir no lote direto sem sair da visão mensal.

Em cima da página, há ainda o botão **"Enviar TUDO deste mês"** (dispara os 4 lotes em sequência, com confirmação extra por envolver plano de saúde — Lote 4 sempre exige clique manual CPF-a-CPF).

---

## 4. Terminal ao vivo (já existe, refinar)

A faixa inferior da tela continua com o **terminal em tempo real** que já tá funcionando hoje. Refinamentos:

- Filtro por lote/mês (chips em cima do terminal).
- Cor por severidade (erro=vermelho, ok=verde, aviso=amarelo).
- Botão "exportar log do dia" (txt).
- Linha de log clicável → foca na linha do CPF na tabela acima.

---

## 5. Ficha do CPF (modal ao clicar no CPF)

Quando o usuário clica num CPF da tabela, abre um modal lateral:

- Identificação: CPF, nome, matrícula.
- Lote atual, competência.
- **Histórico completo** de envios daquele CPF (todas as tentativas, feitas pela tela): data, status, recibo, erro, XML.
- Último recibo ativo conhecido.
- Operadora (se lote 2 ou 3).
- Botão **Reenviar** destacado.
- Aba "Pagamentos" com `detPgtos` do último envio.
- Aba "IR Complem" com `infoIRComplem` do último envio.

---

## 6. Porta de entrada — escolha da vertente

Quando o usuário clica em "Repositório S-1210" no menu principal, **antes de qualquer dashboard**, cai numa tela de entrada simples:

```
┌──────────────────────────────────────────────┐
│    Repositório S-1210 · APPA (2025-02..04)   │
│                                              │
│  Como você quer ver?                         │
│                                              │
│   ┌────────────────┐  ┌──────────────────┐   │
│   │   POR LOTE     │  │     MENSAL       │   │
│   │  (4 grandes    │  │   (3 meses ×     │   │
│   │   lotes × 3    │  │    4 divisores)  │   │
│   │   meses)       │  │                  │   │
│   └────────────────┘  └──────────────────┘   │
│                                              │
│  Status geral: 2 feito · 35.774 pend · 0 erro│
│  Última ingestão XLSX: 21/04/2026            │
└──────────────────────────────────────────────┘
```

Dois cards grandes. Um clique → entra na vertente escolhida. A preferência fica salva por usuário (próxima vez entra direto na última usada, com botão "trocar visão" no canto).

---

## 7. Sobre "feito" (fidelidade)

Um CPF só é marcado **feito** quando **esta missão** enviou e o eSocial aceitou com `nrRecibo` válido. Ponto. Nada de herdar status de envio antigo (pipeline legado da sessão anterior — aquilo fica como "histórico", não conta aqui).

A tela hoje já aplica esse filtro (cutoff da missão). Na persistência via `s1210_cpf_envios` fica natural: a tabela nova só terá envios feitos via a nova tela.

---

## 8. O que precisa ser construído (ordem sugerida)

1. **Banco** — criar as 5 tabelas lógicas da seção 1 (nomes a definir junto com o usuário).
2. **Ingestão XLSX** — endpoint de upload + parseamento + gravação em `s1210_xlsx` + `s1210_cpf_scope` + `s1210_operadoras`. Com hash pra detectar mudança de arquivo.
3. **Porta de entrada** — rota `/repositorio-s1210` com os 2 cards (Por Lote / Mensal).
4. **Vertente A (nível 1)** — rota `/repositorio-s1210/por-lote` com as 4 caixas × 3 meses e contadores.
5. **Vertente A (nível 2)** — rota `/repositorio-s1210/por-lote/:lote/:mes` com tabela de CPFs, filtros, botões do compartimento e ações por linha.
6. **Vertente B (nível 1 e 2)** — rotas `/repositorio-s1210/mensal` e `/repositorio-s1210/mensal/:mes` (lista única com 4 divisores).
7. **Ficha do CPF** — modal com histórico de envios.
8. **Endpoints de envio/retry/pausar/retomar/parar** — já existem em `s1210_missao_routes.py` — ajustar pra gravar em `s1210_cpf_envios` além do resto.
9. **Terminal refinado** — filtro por lote/mês, exportar log, clique em log → foco na tabela.

---

## 9. O que NÃO entra nesta missão

- Nenhum envio automático sem clique explícito do usuário.
- Nenhum fechamento de período (S-1299).
- Nenhum toque em S-1200.
- Nenhum uso de `explorador_eventos` como fonte de escopo.
- Nenhum re-upload de XLSX toda vez que entra na tela.

---

## 10. Conferência das fontes (feita agora)

- [x] 3 XLSX oficiais existem em `C:\Users\xandao\Downloads`, tamanhos conferem com o registrado em [FONTES_MISSAO.md](FONTES_MISSAO.md).
- [x] 2 CPFs testados hoje estão no DB e aparecem na tela como `feito` (01853386669 e 55146015600, ambos com `nr_recibo_novo` válido).
- [x] Restante dos compartimentos aparecem zerados (lixo histórico do pipeline legado não conta).

---

## 11. Aguardando

- Aprovação do usuário sobre os **nomes das tabelas** da seção 1 (`s1210_xlsx`, `s1210_cpf_scope`, `s1210_operadoras`, `s1210_cpf_envios`, `s1210_cpf_recibo`) — se tudo OK, parto pro passo 1 da seção 8.
