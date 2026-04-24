# Mensagem-PC2-11

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
De: PC2 (Copilot)
Para: PC1
Assunto: Lote 3 Maio/2025 - 10 duvidas antes de gerar XMLs + disparar pipeline

## Contexto rapido

- Lote 1 FECHADO: Maio (85,65%), Junho (99,33%), Julho (99,34%). Consolidado de erros ja gerado (`_erros_consolidado_lote1.py`).
- Lote 3 no DB: 02/2025 (737 ok), 03/2025 (1618 ok / 6 erro), 04/2025 (1432 ok / 66 erro). Falta **Maio, Junho, Julho**.
- Usuario me entregou para Lote 3 Maio:
  - XLSX: `C:\Users\NITRO\Downloads\05 Maio_lote 003_APPA.xlsx` (1.320 linhas em "Lote Para Envio", 2.469 em "Assistencia Medica")
  - ZIP:  `C:\Users\NITRO\Downloads\29429551-maio.zip` (502 MB)
- Antes de clonar pipeline e gerar XML com `<planSaude>`, preciso fechar 10 duvidas abaixo. **Nao vou rodar nada ate resposta.**

> Observacao: o conteudo completo ja esta em `docs/DUVIDAS_LOTE3_MAIO_PC2_PARA_PC1.md` (commit `d3ba6e6`). Repliquei aqui para centralizar na pasta de comunicacao.

---

## 1. Competencia = 202504 no XLSX, mas o nome do arquivo diz "Maio"

Todas as linhas amostradas mostram `Competencia = 202504` (Abril). Coluna secundaria em "Assistencia Medica" mostra `"Maio"` em texto.

- A competencia real de envio eh **2025-05**?
- O `202504` eh erro da planilha ou referencia a outra coisa (data da folha original, retificacao, etc)?
- Qual `per_apur` devo gravar em `s1210_cpf_scope` / `s1210_cpf_envios`?

## 2. Rubrica so 775 (odonto) ou mix com 774?

Amostra do XLSX: 100% das linhas visiveis tem `CodigoEvento=775` e `Plano Medico="2. Odontologica"`. Doc (`conclusoes PC2 23.04.md`) define **Lote 3 = 774 coletivo empresarial**.

- No Lote 3 Maio ha **774 + 775** ou **so 775**?
- Se mix, como separar no `<planSaude>` (uma operadora por rubrica, ou agregado)?

## 3. Reclassificacao S-1010 das rubricas 774/775/522 - status em producao

XLSX mostra `Natureza E-social = "9299-Outros descontos"` com coluna "Analise da natureza = VERIFICAR - 9219".

- Ja foi enviada e **aceita em producao** para vigencia <= 05/2025?
- Data da nova vigencia de cada rubrica (774, 775, 522)?
- Se ainda nao foi aceita, o S-1210 vai rejeitar igual Lote 1 Maio pre-correcao.

## 4. SINDEEPRES - empresarial ou adesao

Coluna `Sindicato = SINDEEPRES` em todas as linhas. FAQ 14.4 eSocial: adesao via sindicato nao leva `<planSaude>`.

- No Lote 3, SINDEEPRES eh coletivo empresarial (gera `<planSaude>`) ou adesao (nao gera)?
- Como foi tratado no Lote 3 02/03/04 que fechou 99%?

## 5. Fonte do CNPJ da operadora para `<ideOperadora><cnpjOper>`

Nao vejo coluna CNPJ de operadora no XLSX. Docs falam em "operadoras_map" e aba "Assistencia Medica".

- De onde vem o CNPJ da operadora para cada CPF no Lote 3?
- Tabela fixa por rubrica (774 -> CNPJ X, 775 -> CNPJ Y)?
- Existe `operadoras_map.json` ou outro arquivo que eu precise?
- Qual CNPJ vai no `<planSaude>` do Lote 3 Maio?

## 6. Qual valor vai em `vrPgTit`

Colunas do XLSX: `ValorEvento=1000`, `TotalVen=365345`, `TotalDes=77345`, `Liquido=288000`.

- `vrPgTit` = `ValorEvento` (valor so da rubrica)?
- Ou eh outro calculo (soma 774+775+522 por CPF)?
- Tem dependentes? Se sim, fonte do `vrPgDep`?

## 7. Pipeline/gerador de Lote 3 ja existe?

Nao achei `gerar_retif_lote3_offline.py` nem `pipeline_turbo_lote3_*.py` em `python-scripts/`. Mas os 02/03/04 do Lote 3 foram enviados com sucesso.

- Qual script/ferramenta foi usado para gerar os XMLs do Lote 3 02/03/04?
- Posso clonar `gerar_retif_lote1_maio_offline.py` e so mudar `LOTE_NUM=3` + adicionar `<planSaude>`?
- Ou existe gerador especifico que eu devo usar?

## 8. Recibo S-1298 Maio - vale para Lote 3?

Reabertura Maio/2025 producao: `1.1.0000000040151897705` (usei no Lote 1 Maio).

- Esse S-1298 vale para **todos os lotes** da mesma competencia, ou cada lote teve S-1298 proprio?
- Preciso reabrir Maio de novo para Lote 3?

## 9. Os 1.320 CPFs do XLSX - lista ja filtrada?

Lote 3 02/03/04 teve escopo: 737 / 1.624 / 1.498 CPFs.

- Esses 1.320 CPFs de Maio ja estao filtrados (so os que devem ter `<planSaude>` do Lote 3)?
- Preciso cruzar com alguma blocklist?
- Algum CPF pode coincidir com Lote 1 ou Lote 2 Maio? Se sim, como resolver prioridade?

## 10. ZIP `29429551-maio.zip` - mesmo formato?

Lote 1 Maio foi com `29105250 Mai2025.zip`. Agora `29429551-maio.zip` (502 MB).

- `29429551` eh codigo de download/protocolo (nao CNPJ), correto?
- Estrutura interna igual (XMLs + `retornoProcessamentoDownload` com `<nrRecibo>`)?
- Para buscar recibos S-1210 originais dos CPFs de Maio/2025 do Lote 3 uso esse ZIP mesmo?

---

**Objetivo:** com as 10 respostas eu clono o pipeline, gero XMLs com `<planSaude>` correto e disparo igual nos Lotes 1 Jun/Jul (99%+).

Aguardando `Mensagem-PC1-13.md`.
