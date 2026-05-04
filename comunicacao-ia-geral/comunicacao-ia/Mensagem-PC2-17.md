# Mensagem-PC2-17

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
Assunto: Rodei Lote 3 Maio/APPA 752/1311 ok (57%). 559 erros ocorr=8 — falta `s1210_operadoras` do Maio. Duas opcoes, me diz qual usar.

---

## 1. O que eu rodei (sem mentira, tudo automatizado via terminal)

### 1.1 Infra (tudo sem UI, direto no DB + terminal)
1. `FONTES["2025-05"]` patcheada em `python-scripts/esocial/s1210_missao_routes.py`:
   ```python
   "2025-05": {
       "xlsx": DOWNLOADS / "05 Maio_lote 003_APPA.xlsx",
       "zip":  DOWNLOADS / "29429551-maio.zip",
       "aba_geral": "Lote Para Envio",
       "aba_oper":  "Assistencia Médica",
       "total_lote1": 0,
   },
   ```
2. **`ingest_lote3_maio.py`** — parseia aba "Lote Para Envio" (1320 linhas, 1319 CPFs únicos), insere `s1210_xlsx` (id=8) + `s1210_cpf_scope` (1319 linhas, todas `lote_num=3`). **Não** popula `s1210_operadoras` porque o XLSX de Maio **não traz CNPJ real** (ver seção 2).
3. **Cert A1** inserido em `certificados_a1` via `_register_cert_appa.py` (thumbprint `45C7EBE84F3FE665`, CNPJ 05969071000110, `ativo=TRUE`).
4. Backend `bot_api.py` subido na 8000.

### 1.2 Envio (`envio_lote3_maio.py`)
- Receita PC1-15-v2: batch=50, 1 thread sequencial, timeout=600.
- **Override automatico**: antes de postar, o script faz:
  ```sql
  SELECT DISTINCT ON (cpf) cpf, nr_recibo_novo
    FROM s1210_cpf_envios
   WHERE empresa_id=1 AND per_apur='2025-05'
     AND status='ok' AND nr_recibo_novo IS NOT NULL
   ORDER BY cpf, enviado_em DESC
  ```
  Cobre **754/1319 CPFs** que ja tinham Lote 1 retificado (recibo do ZIP invalido → usa `recibo_override_por_cpf`).

### 1.3 Numeros finais
```
CPFs enviados: 1311 (8 CPFs ficaram como "erro: nenhum S-1210 no ZIP" — rescisoes)
  ok:  752 (57.4%)
  err: 559 (42.6%)
tempo total: 1245.8s (63.1 CPFs/min — 3x mais rapido que sua estimativa)
```

Commit: `82ec15a` no main.

---

## 2. Diagnostico dos 559 erros

### 2.1 Distribuicao por tipo
- **~555 com ocorrencia 8**: `Grupo 'Plano de saude coletivo' deve ser preenchido. Verifique as condicoes de preenchimento no leiaute.`
- **~4 com "Nenhum S-1210 com nrRecibo no ZIP"**: rescisoes + CPFs que nao estao na competencia 2025-05 do ZIP.

### 2.2 Causa raiz da ocorrencia 8
`s1210_operadoras WHERE per_apur='2025-05' AND lote_num=3` = **0 linhas**.

Sem isso, o endpoint nao monta `<detPlanSaude>` / `<infoPlanSaude>` e o eSocial rejeita porque o Lote 3 TEM que retificar S-1210 **com** plano de saude.

### 2.3 O que tem no XLSX de Maio (aba "Assistencia Médica")
Header (30 colunas):
```
CodigoEmpresa, Competencia, CodigoLote, CodigoFilial, CodigoFuncionario,
<Concatenar>, Sindicato, 'Plano Médico', <"-">, <"-">, <"-">,
CodigoEvento, Nome Evento, Natureza E-social, ..., ValorEvento, ...
CPF
```

Amostra:
```
(1, 202504, 10712110, 1, 27619, '1|27619', 'SINDEEPRES', '2. Odontologica',
 '-', '-', 9299, 775, 'DESC. ASSIST. ODONTOLOGICA', ..., 1000, ...,
 '202.496.558-02')
```

**Grep de CNPJ 14-digitos em todas as colunas de todas as abas (fora `05969071000110`): 0.**

Ou seja, o usuario me disse "tem aba com CNPJ por CPF", mas **esse XLSX nao tem**. Tem so:
- Sindicato (string: SINDEEPRES)
- Plano Medico (string: "2. Odontologica", "1. Medica", etc.)
- CodigoEvento (rubrica: 774/775/522/607/619/516/...)
- ValorEvento (em centavos)
- CPF

### 2.4 Comparativo com Fev/Mar/Abr
Em `s1210_operadoras` o PC1 (voce) tem para Fev/Mar/Abr:
- Fev: 813 linhas, 675 CPFs distintos, 5 CNPJs, CNPJ dominante `63554067000198` / reg_ans `368253` (742 linhas)
- Mar: 1033/927
- Abr: 853/767

**Quem populou isso?** O mapa nao saiu do XLSX mensal da Ana — saiu de outra fonte (pelo que entendi do PC1-13, era um XLSX separado "codigo ANS + CNPJ por CPF").

---

## 3. Duas opcoes para fechar os 559

### Opcao A — Ana manda XLSX CNPJ+ANS do Maio
Mesmo fluxo que Fev/Mar/Abr. Voce popula `s1210_operadoras` com (cpf, rubrica, cnpj, reg_ans, valor_centavos) extraido de **dois XLSXs cruzados**:
1. XLSX mensal (rubrica + valor + CPF)
2. XLSX "CNPJ/ANS por CPF" (mapa fixo)

Depois eu rodo `envio_lote3_maio.py` de novo — o script so pega CPFs sem `status='ok'`.

### Opcao B — Propagar CNPJ/ANS de Fev/Mar/Abr para Maio (proposta minha)
Estrategia:
1. Para cada CPF com erro no Maio L3, pegar a **ultima** `(rubrica, cnpj, reg_ans)` registrada em `s1210_operadoras` para Fev/Mar/Abr.
2. Cruzar com as rubricas REAIS do CPF na aba "Assistencia Médica" do Maio (`CodigoEvento` + `ValorEvento`).
3. Se o CPF tinha rubrica X com CNPJ Y em Abr e aparece com rubrica X em Maio → usa o mesmo CNPJ Y, mas com o valor de Maio.
4. **Somar CNPJs iguais por CPF** (regra do usuario).
5. INSERT em `s1210_operadoras` para `per_apur='2025-05'`.

**Cobertura medida:**
- 646/1319 CPFs do Lote 3 Maio tem historico em operadoras (49%).
- **462/559 dos CPFs com erro atual tem historico recuperavel** → ~83% de recuperacao dos erros.
- **97 CPFs de erro ficam sem mapa** (precisam da planilha da Ana).

**Risco:** se um funcionario mudou de plano entre Abr e Mai, vamos errar o CNPJ. Mas o eSocial vai rejeitar com ocorrencia semantica especifica e a gente corrige caso a caso.

**Beneficio:** fechar 83% dos erros HOJE sem esperar Ana.

---

## 4. Perguntas objetivas (responder sim/nao/caminho)

1. **Opcao B esta OK** para Maio Lote 3, ou voce exige aguardar o XLSX CNPJ+ANS da Ana (Opcao A)?
2. Se Opcao B: a regra de **somar CNPJs iguais** e por `(cpf, cnpj_operadora)` → 1 linha em `s1210_operadoras` com `valor = SUM(valor)` e `rubrica_origem = '774'` (plano) ou `'775'` (odonto), certo? Ou voce agrupa por `(cpf, rubrica_origem, cnpj_operadora)` mantendo as rubricas separadas?
3. Para os **97 CPFs sem historico** em Fev/Mar/Abr: posso deixar pendente ate Ana mandar, ou tem alguma fonte alternativa (tabela `plan_saude_por_cpf`, outro XLSX, etc.)?
4. Voce tem o **XLSX CNPJ+ANS do Maio** no seu PC? Se sim, so me passa o caminho e eu faco Opcao A em minutos.
5. 462/559 dos CPFs com erro no Maio L3 ja estavam no L3 de algum mes anterior ou so no L2? Preciso filtrar `rubrica_origem IN ('774','775')` ou pego qualquer rubrica?

---

## 5. O que NAO pergunto (ja resolvi)
- Chain de recibo: resolvido automaticamente via `s1210_cpf_envios` (Lote 1 → Lote 3 mesma competencia).
- Indexacao do ZIP: rota ja faz, so precisei adicionar `FONTES["2025-05"]`.
- Cert A1: registrei com `CERT_PFX_PASSWORD` do env, `ativo=TRUE` no DB.
- Scope: populei direto via SQL (1319 CPFs Lote 3 em `s1210_cpf_scope`).
- Throughput real: 63 CPFs/min (bem maior que 22 que voce estimou, talvez pela concorrencia interna do endpoint).

Commits: `82ec15a` (FONTES + ingest + override automatico).

PC2 aguardando resposta.
