# Dúvidas Lote 3 Maio/2025 — PC2 → PC1

**Contexto:** Preparando envio do Lote 3 Maio/2025 (APPA, empresa_id=1). Lote 3 02/03/04 já fechou 99%+. Recebi XLSX `05 Maio_lote 003_APPA.xlsx` (1.320 CPFs na aba "Lote Para Envio") + ZIP `29429551-maio.zip` (502 MB).

Antes de clonar o pipeline e gerar XMLs, preciso dessas respostas para não chutar:

---

## 1. Competência = 202504 no XLSX, mas o nome diz "Maio"

Todas as linhas mostram `Competencia = 202504` (Abril). Coluna secundária na aba Assistência Médica diz `"Maio"` em texto.

- A competência real de envio é **2025-05** mesmo?
- O `202504` é erro da planilha ou referência a outra coisa (data da folha original? retificação?)
- Qual `per_apur` devo gravar em `s1210_cpf_scope` / `s1210_cpf_envios`?

## 2. Rubrica só 775 (odonto) ou mix com 774?

Amostra do XLSX: 100% das linhas visíveis têm `CodigoEvento=775` e `Plano Médico="2. Odontologica"`. Mas a doc (`conclusoes PC2 23.04.md`) define **Lote 3 = 774 coletivo empresarial**.

- No Lote 3 Maio há **774 + 775** ou **só 775**?
- Se mix, como separar no `<planSaude>` (uma operadora por rubrica)?

## 3. Reclassificação S-1010 — status em produção?

XLSX mostra `Natureza E-social = "9299-Outros descontos"` com coluna "Analise da natureza = VERIFICAR - 9219".

- A reclassificação **já foi enviada e aceita** no eSocial prod para vigência ≤ 05/2025?
- Data da vigência nova da rubrica 774 e 775?
- Se ainda não aceita, o S-1210 vai rejeitar igual aconteceu no Lote 1 Maio pré-correção.

## 4. SINDEEPRES — empresarial ou adesão?

Coluna `Sindicato = SINDEEPRES` em todas as linhas. FAQ 14.4 eSocial diz: adesão via sindicato **não** leva `<planSaude>`.

- O SINDEEPRES no Lote 3 é coletivo empresarial (gera `<planSaude>`) ou adesão (não gera)?
- Como foi tratado no Lote 3 02/03/04 que fechou 99%?

## 5. Fonte do CNPJ da operadora para `<ideOperadora><cnpjOper>`

Não vejo coluna CNPJ de operadora no XLSX. Docs falam em "operadoras_map" e aba "Assistencia Médica".

- De onde vem o CNPJ da operadora para cada CPF no Lote 3?
- Tem tabela fixa por rubrica (774 → CNPJ X, 775 → CNPJ Y)?
- Tem `operadoras_map.json` ou aba extra no XLSX que eu não vi?
- Qual CNPJ vai no `<planSaude>` do Lote 3 Maio?

## 6. Qual valor vai em `vrPgTit`

XLSX tem: `ValorEvento=1000`, `TotalVen=365345`, `TotalDes=77345`, `Liquido=288000`.

- `vrPgTit` do `<planSaude>` = **ValorEvento** (valor só da rubrica)?
- Ou é outro cálculo (soma de 774+775+522 por CPF)?
- Tem dependentes? Se sim, de onde vem `vrPgDep`?

## 7. Pipeline de geração de Lote 3 — já existe?

Não achei `gerar_retif_lote3_offline.py` nem `pipeline_turbo_lote3_*.py` em `python-scripts/`. Mas os 02/03/04 do Lote 3 foram enviados com sucesso.

- Qual script foi usado para gerar os XMLs do Lote 3 02/03/04?
- Posso clonar `gerar_retif_lote1_maio_offline.py` e só mudar `LOTE_NUM=3` + adicionar bloco `<planSaude>`?
- Ou tem gerador específico do Lote 3 que eu preciso pegar?

## 8. Recibo S-1298 Maio — vale para Lote 3?

Reabertura Maio/2025 produção: `1.1.0000000040151897705` (usei no Lote 1 Maio).

- Esse recibo S-1298 vale para **todos os lotes** da mesma competência, ou cada lote teve S-1298 próprio?
- Preciso reabrir Maio de novo para Lote 3, ou o que já foi reaberto cobre?

## 9. Os 1.320 CPFs do XLSX — já é lista filtrada?

Escopo do Lote 3 02/03/04 foi: 737 / 1.624 / 1.498 CPFs.

- Esses 1.320 CPFs de Maio já estão filtrados (só os que devem ter `<planSaude>` do Lote 3)?
- Ou preciso cruzar com alguma blocklist/XLSX de exclusão?
- Algum CPF desses pode coincidir com Lote 1 ou Lote 2 Maio? Se sim, como resolver prioridade?

## 10. ZIP `29429551-maio.zip` — mesmo formato?

502 MB, nome `29429551-maio.zip`. O do Lote 1 Maio foi `29105250 Mai2025.zip`.

- `29429551` é código de download/protocolo, não CNPJ, correto?
- Estrutura interna igual (XMLs + `retornoProcessamentoDownload` com `<nrRecibo>`)?
- Para buscar recibos S-1210 originais de cada CPF de Maio/2025 uso esse ZIP mesmo?

---

**Objetivo:** com essas 10 respostas fechadas, clono o pipeline, gero XMLs com `<planSaude>` correto e disparo igual fizemos nos Lotes 1 Jun/Jul (99%+ sucesso).
