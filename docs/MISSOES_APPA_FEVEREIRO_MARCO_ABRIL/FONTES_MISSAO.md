# FONTES DA MISSÃO — o que ler, onde está, como usar

**Data:** 21/04/2026
**Autoridade:** trechos da call transcritos em [RESOLUCAO_S1200_3_MESES.md](RESOLUCAO_S1200_3_MESES.md) §"Transcrição da Call (íntegra)" e §"Decisões extraídas da call".

---

## Resumo de uma frase

Existem **2 grupos de fontes**, **3 arquivos em cada grupo** (um por mês). **TODAS** ficam em `C:\Users\xandao\Downloads`. Não existe mais nenhuma fonte de escopo legítima — `explorador_eventos` **está proibido** (memória permanente do agente).

---

## Grupo 1 — XLSX da Ana (ESCOPO: quem enviar, em qual lote)

| Mês     | Arquivo                              |  Tamanho | Recebido         |
| ------- | ------------------------------------ | -------: | ---------------- |
| 2025-02 | `02. Fevereiro_2025_APPA certa.xlsx` |   ~42 MB | 20/04/2026 16:18 |
| 2025-03 | `03. Marco_2025_APPA.xlsx`           | ~38,7 MB | 20/04/2026 15:51 |
| 2025-04 | `04. Abril_2025_APPA.xlsx`           | ~37,9 MB | 20/04/2026 15:52 |

Todos em `C:\Users\xandao\Downloads`. Fevereiro tem sufixo `certa` — é a versão final, ignorar anteriores.

### Abas e regras (extraídas da call)

A call é explícita sobre como usar as abas:

> [01:32] SPEAKER_00 (Alex): _"As tabelas têm abas. A aba mais importante é a aba **geral para envio de lotes**, que é a ÚNICA aba que a IA tem que acessar para puxar as informações. [...] A IA não tem que mexer em nada de incidência. As incidências e as naturezas, quem vai mudar é a gente mesmo."_

> [02:20] SPEAKER_01 (Ana): _"No lote 2 e 3 a gente vai precisar da indicação das operadoras para que faça as consolidações e as transmissões do plano coletivo de saúde empresarial."_

> [02:40] SPEAKER_00: _"Para o evento 2, lote 2 e 3, ele vai ter que trocar de aba. Ele vai para a aba **operadoras** também, vai buscar as informações que ele precisa lá e vai trabalhar junto com a aba geral."_

**Regras derivadas:**

| Aba                         | Quando usar                              | O que extrair                         |
| --------------------------- | ---------------------------------------- | ------------------------------------- |
| `Geral para envio de lotes` | **SEMPRE** (todos os lotes, todos meses) | CPF, lote (1/2/3/4), colunas de envio |
| `Operadoras`                | **SÓ lotes 2 e 3**                       | CPF → operadora (774 ou 775)          |
| Outras abas                 | **NUNCA**                                | —                                     |

**Proibições:**

- ❌ Não tocar em incidências
- ❌ Não tocar em naturezas
- ❌ Não ler outras abas

### Os 4 lotes (também da call)

> [00:13] SPEAKER_01 (Ana): _"O lote 1 é onde não contém nenhuma informação de assistência médica. O lote 2 contém verbas onde a 774 e a 522 não podem ser plano de saúde coletivo empresarial. Porém, a 775 sim, ela é um plano de saúde coletivo empresarial que é odontológica. E o lote 3 já é o processo inverso. A 775 não é um plano coletivo empresarial e a 774 passa a ser para as pessoas que estão dentro do lote 3. O lote 4 tem 3 pessoas onde a gente vai ter que analisar e liberar sem incidência nenhuma de plano de saúde."_

|  Lote | Escopo                                                      | `planSaude` no S-1210                        |
| ----: | ----------------------------------------------------------- | -------------------------------------------- |
| **1** | CPFs sem assistência médica                                 | **Não enviar planSaude**                     |
| **2** | 775 É coletivo empresarial (odonto); 774 e 522 não são      | Enviar planSaude **só com operadora de 775** |
| **3** | Inverso do 2: 774 É coletivo empresarial; 775 e 522 não são | Enviar planSaude **só com operadora de 774** |
| **4** | 3 pessoas manuais, sem plano                                | **Não enviar planSaude** (liberação manual)  |

### Totais esperados (validação do parser)

| Mês     | Registros | **CPFs únicos (Lote 1)** | Batches de 50 |
| ------- | --------: | -----------------------: | ------------: |
| 2025-02 |     9.473 |                **9.472** |           190 |
| 2025-03 |     8.165 |                **8.165** |           164 |
| 2025-04 |     7.142 |                **7.142** |           143 |

Se o parser retornar número diferente no Lote 1 → **ERRO claro**, não prosseguir.

---

## Grupo 2 — ZIPs do eSocial (DADOS: XMLs originais, recibos, rubricas)

| Mês     | Arquivo                  | Tamanho | Baixado em       |
| ------- | ------------------------ | ------: | ---------------- |
| 2025-02 | `29429415 fev2025.zip`   | ~524 MB | 10/04/2026 15:26 |
| 2025-03 | `29429449 marc2025.zip`  | ~524 MB | 10/04/2026 15:23 |
| 2025-04 | `29429512 abril2025.zip` | ~554 MB | 10/04/2026 15:08 |

Todos em `C:\Users\xandao\Downloads`. O número no nome (ex: `29429415`) é o protocolo do Download Cirúrgico no portal eSocial.

### O que tem dentro

Cada ZIP contém **milhares de XMLs** (~51.000/mês), um por evento eSocial:

- **S-1200** (remuneração) → rubricas 607/774/775/516/522 etc.
- **S-1210** (pagamentos) → recibos originais (é daqui que saem os `nrRecibo` pra retificação)
- **S-5001 / S-5002** (totais INSS / IRRF) → auto-gerados
- **S-5011 / S-5012** → totalizadores

### Regras de leitura (CRÍTICO — não negociável)

1. **NÃO extrair em disco.** Ler streaming com `zipfile.ZipFile` + `zf.open(name)`.
2. **Parse incremental** com `lxml.etree.iterparse`, `elem.clear()` após cada evento.
3. **Filtrar nomes** antes de abrir (só S-1200 e S-1210 interessam pra missão).
4. **Paralelismo** com `ThreadPoolExecutor` (4–8 workers); cada thread com seu próprio `ZipFile`.
5. **XPath namespace-agnostic** (`{*}tag` ou `local-name()`).
6. **Tolerar XML malformado** — logar e pular, não abortar.
7. **Custo esperado:** 5–15 min/mês em SSD, memória < 2 GB.

Esqueleto em [RESOLUCAO_S1200_3_MESES.md §"Como o parser deve funcionar"](RESOLUCAO_S1200_3_MESES.md) (~linha 270).

### Para que serve cada tipo de XML

| Evento | Uso na missão                                                         |
| ------ | --------------------------------------------------------------------- |
| S-1210 | **Fonte dos `nrRecibo` originais** — imprescindível pra retificação   |
| S-1200 | Fonte das rubricas (pra validar 774/775/522 do XLSX) — **só leitura** |
| S-500x | Ignorar (auto-gerados pelo eSocial)                                   |

---

## Checklist antes de qualquer envio

1. [ ] Os 3 XLSX da Ana estão em `C:\Users\xandao\Downloads` (validar via PowerShell)
2. [ ] Os 3 ZIPs do eSocial estão em `C:\Users\xandao\Downloads` (validar via PowerShell)
3. [ ] Parser XLSX extraiu exatamente 9.472 / 8.165 / 7.142 CPFs no Lote 1
4. [ ] Parser ZIP (streaming) achou S-1210 + `nrRecibo` para cada CPF do escopo
5. [ ] Lotes 2 e 3 cruzaram corretamente com a aba `Operadoras`
6. [ ] Teste com **1 CPF por lote/mês (12 CPFs)** antes do envio massivo
7. [ ] OK explícito do usuário antes de enviar

---

## Validação via PowerShell (reprodutível)

```powershell
# Os 3 XLSX
Get-ChildItem -Path "C:\Users\xandao\Downloads" -Filter "*APPA*.xlsx" |
    Select-Object Name, Length, LastWriteTime |
    Format-Table -AutoSize

# Os 3 ZIPs
Get-ChildItem -Path "C:\Users\xandao\Downloads" -Filter "*.zip" |
    Where-Object { $_.Name -match "fev2025|marc2025|abril2025" } |
    Select-Object Name, Length, LastWriteTime |
    Format-Table -AutoSize
```

Resultado esperado: 3 linhas em cada.

---

## Regra mestra (memorando do agente)

Quando pensar "de onde vêm os dados da missão?" — resposta única:

1. **Escopo (quem enviar):** XLSX da Ana, aba `Geral para envio de lotes` (+ aba `Operadoras` só pra lotes 2/3).
2. **Dados (recibo, rubricas):** ZIPs do eSocial, streaming sem extrair.

**Nada mais.** Nem `explorador_eventos`, nem `pipeline_cpf_results` como escopo (só como referência de "o que já tentamos enviar"), nem runs antigas.
