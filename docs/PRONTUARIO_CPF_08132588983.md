# Prontuário de Teste — CPF 08132588983

## 1. Identificação

| Campo               | Valor                                |
| ------------------- | ------------------------------------ |
| **CPF**             | 08132588983                          |
| **Matrícula**       | 001-001-056502                       |
| **Estabelecimento** | 05.969.071/0001-10                   |
| **Período**         | 2024-12 (Dezembro 2024)              |
| **Status**          | ✅ ATIVO (sem S-2299)                |
| **Salário base**    | R$ 2.501,20                          |
| **INSS (rubr 566)** | R$ 301,11                            |
| **IRF (rubr 570)**  | R$ 39,63                             |
| **Dependente IRRF** | CPF 14020816930 (dedução R$ 189,59)  |
| **Fonte dos XMLs**  | `C:\Users\xandao\Downloads\29076329` |

---

## 2. Eventos eSocial Encontrados

### Linha do Tempo

| #   | Data envio | Evento | perApur | indRetif     | nrRecibo                        | Status                 |
| --- | ---------- | ------ | ------- | ------------ | ------------------------------- | ---------------------- |
| 1   | 2025-01-07 | S-1200 | 2024-12 | 1 (original) | 1.1.0000000030047992060         | Substituído pela retif |
| 2   | 2025-01-13 | S-1210 | 2024-12 | 1 (original) | 1.1.0000000030222629402         | Substituído            |
| 3   | 2025-01-20 | S-3000 | 2024-12 | —            | excluiu nrRecEvt ...30324097296 | Processado             |
| 4   | 2025-01-20 | S-1200 | 2024-12 | 2 (retif)    | ref: 1.1.0000000030047992060    | Substituído (retif 2)  |
| 5   | 2025-01-20 | S-1210 | 2024-12 | 1 (novo)     | 1.1.0000000030328525269         | Substituído (retif 2)  |
| 6   | 2026-06    | S-3000 | 2025-01 | —            | 1.1.0000000039598957342         | ✅ Excluiu S-1210 bloq |
| 7   | 2026-06    | S-1200 | 2024-12 | 2 (retif 2)  | 1.1.0000000039598957701         | **VIGENTE**            |
| 8   | 2026-06    | S-1210 | 2024-12 | 2 (retif 2)  | 1.1.0000000039598958189         | **VIGENTE**            |
| 9   | 2026-06    | S-1210 | 2025-01 | 1 (incluir)  | 1.1.0000000039598958954         | **VIGENTE**            |

### Totalizadores Gerados

| Evento | Vinculado a             | Status anterior | Status pós-pipeline          |
| ------ | ----------------------- | --------------- | ---------------------------- |
| S-5001 | S-1200 original         | Supersedido     | Supersedido                  |
| S-5001 | S-1200 retif 1          | VIGENTE         | Supersedido pela retif 2     |
| S-5001 | S-1200 retif 2 (novo)   | —               | **VIGENTE** (recalculado)    |
| S-5002 | S-1210 original         | Supersedido     | Supersedido                  |
| S-5002 | S-1210 excluído (S-3000)| Vazio/excluído  | Vazio/excluído               |
| S-5002 | S-1210 retif 1          | VIGENTE         | Supersedido pela retif 2     |
| S-5002 | S-1210 retif 2 (novo)   | —               | **VIGENTE** (recalculado)    |
| S-5003 | S-1200 original         | Supersedido     | Supersedido                  |
| S-5003 | S-1200 retif 1          | VIGENTE         | Supersedido pela retif 2     |
| S-5003 | S-1200 retif 2 (novo)   | —               | **VIGENTE** (recalculado)    |

### Recibos-Chave

| Uso                                    | nrRecibo                                                  |
| -------------------------------------- | --------------------------------------------------------- |
| S-1010 rubrica 566 (codIncIRRF 11→41)  | `1.1.0000000039598012258`                                 |
| S-1010 rubrica 596 (codIncIRRF 12→42)  | `1.1.0000000039598028920`                                 |
| S-1200 retif vigente (Dez/2024)        | `1.1.0000000039598957701`                                 |
| S-1210 retif vigente (Dez/2024)        | `1.1.0000000039598958189`                                 |
| S-1210 reincluído (Jan/2025)           | `1.1.0000000039598958954`                                 |
| S-3000 exclusão S-1210 bloq (Jan/2025) | `1.1.0000000039598957342`                                 |
| S-1299 fechamento Dez/2024             | `1.1.0000000039598960033`                                 |
| S-1299 fechamento Jan/2025             | `1.1.0000000039598961340`                                 |

---

## 3. Demonstrativos (S-1200 vigente)

### DmDev 1 (possivelmente 13º salário)

| Rubrica | Descrição                | Valor     | Fator |
| ------- | ------------------------ | --------- | ----- |
| 9276    | _(não cadastrada no DB)_ | R$ 231,00 | —     |
| 9284    | _(não cadastrada no DB)_ | R$ 667,80 | —     |

> ⚠️ Rubricas 9276 e 9284 NÃO existem na tabela `cruzamento_eb`. Não serão corrigidas pelo pipeline.

### DmDev 2 (remuneração mensal)

| Rubrica | Descrição                | Tipo         | Valor         | Fator   | incid_irrf atual | incid_irrf correto |
| ------- | ------------------------ | ------------ | ------------- | ------- | ---------------- | ------------------ |
| 2       | SALARIO MES              | Provento     | R$ 2.501,20   | x30     | 11 ✅            | 11                 |
| 10      | GRATIFICAÇÃO             | Provento     | R$ 125,06     | —       | 11 ✅            | 11                 |
| 105     | HORAS EXTRAS 50%         | Provento     | R$ 585,62     | x34.34  | 11 ✅            | 11                 |
| 160     | D.S.R. S/HORA EXTRA      | Provento     | R$ 140,55     | —       | 11 ✅            | 11                 |
| 273     | ARREDONDAMENTO           | Provento     | R$ 0,70       | —       | 9 ✅             | 9                  |
| 541     | DESC. ARREDONDAMENTO     | Desconto     | R$ 1,20       | —       | 9 ✅             | 9                  |
| **566** | **DESC. I.N.S.S.**       | **Desconto** | **R$ 301,11** | **x12** | **11 ❌**        | **41**             |
| 570     | DESC. I.R.F.             | Desconto     | R$ 39,63      | x7.5    | 31 ✅            | 31                 |
| 672     | DESC. VALE-TRANSPORTE 6% | Desconto     | R$ 150,07     | —       | 9 ✅             | 9                  |
| 776     | DESC. VALE ALIMENTACAO   | Desconto     | R$ 108,12     | —       | 9 ✅             | 9                  |
| 273     | ARREDONDAMENTO           | Provento     | R$ 0,44       | —       | 9 ✅             | 9                  |
| 480     | ADIC. S/13º SALARIO      | Provento     | R$ 70,94      | —       | 12 ✅            | 12                 |
| **596** | **DESC. I.N.S.S. S/13º** | **Desconto** | **R$ 6,38**   | **x9**  | **12 ❌**        | **42**             |

---

## 4. Diagnóstico de Incidência

### Rubricas com BUG confirmado

| Rubrica | Descrição            | incid_irrf ATUAL          | incid_irrf CORRETO    | base_legal_irrf           |
| ------- | -------------------- | ------------------------- | --------------------- | ------------------------- |
| **566** | DESC. I.N.S.S.       | 11 (rend. tributável)     | 41 (dedução IRRF)     | Art. 4º, IV, Lei 9.250/95 |
| **596** | DESC. I.N.S.S. S/13º | 12 (rend. 13º tributável) | 42 (dedução IRRF 13º) | Art. 4º, IV, Lei 9.250/95 |

**Impacto:**

- Com `incid_irrf=11`, a rubrica 566 (INSS) é tratada como "rendimento tributável" em vez de "dedução"
- No informe de rendimentos (DIRF/IRPF), o rendimento tributável aparece inflado e a dedução de INSS aparece zerada/incorreta
- O eSocial reconhece a natureza 9201 (Contribuição Previdenciária) e PODE gerar tpInfoIR=7900 independentemente do incid_irrf, mas a classificação fica inconsistente

### Rubricas OK (sem necessidade de correção)

Todas as demais 12 rubricas têm incidências corretas. Nenhuma outra rubrica deste CPF precisa de ajuste.

---

## 5. Totalizador S-5002 (Vigente)

Referência: S-5002 vinculado ao S-1210 vigente (nrRecibo ...30328525269)

| tpInfoIR | Descrição                                   | Valor       |
| -------- | ------------------------------------------- | ----------- |
| 11       | Rendimento tributável                       | R$ 3.219,33 |
| 7900     | Contribuição previd. oficial (INSS dedução) | -R$ 270,99  |
| 31       | IRRF efetivamente retido                    | R$ 65,34    |
| 7900     | Contribuição previd. oficial (outra)        | R$ 0,40     |
| 12       | Rendimento 13º salário                      | R$ 2.106,33 |

**Dependente IRRF:**
| tpRend | CPF Dependente | vlrDedDep |
|---|---|---|
| 11 (rend. tributável) | 14020816930 | R$ 189,59 |
| 12 (rend. 13º) | 14020816930 | R$ 189,59 |

### S-5001 (INSS — vigente)

| tpCR   | vrCpSeg   | vrDescSeg |
| ------ | --------- | --------- |
| 108201 | R$ 307,49 | R$ 307,49 |

---

## 6. Plano de Correção — Pipeline Completo

### Pré-condições

- [x] Rubricas 566 e 596 já corrigidas via S-1010 (verificar `corrigido=true`)
- [x] Período 2024-12 está FECHADO (confirmar que precisa S-1298 de reabertura)

### Passos do Pipeline (`pipeline_recovery.py` — 8 etapas)

O plano original de 5 passos (S-1298 → S-1200 retif → S-1210 retif → S-1299) falhou na prática porque a retificação do S-1210 de Janeiro/2025 com dados idênticos NÃO libera as referências dmDev (erro 989). Foi necessário redesenhar o pipeline para 8 etapas, incluindo exclusão S-3000 e reinclusão do S-1210 bloqueador.

| Passo | Evento | Ação                                              | Dados necessários                                     |
| ----- | ------ | ------------------------------------------------- | ----------------------------------------------------- |
| 0     | S-1010 | *(Pré-requisito)* Alterar rubrica 566: 11→41      | Já executado — recibo `1.1.0000000039598012258`        |
| 0     | S-1010 | *(Pré-requisito)* Alterar rubrica 596: 12→42      | Já executado — recibo `1.1.0000000039598028920`        |
| 1     | S-1298 | Reabertura Jan/2025                               | perApur=2025-01                                       |
| 2     | S-1298 | Reabertura Dez/2024                               | perApur=2024-12                                       |
| 3     | S-3000 | Excluir S-1210 bloqueador Jan/2025                | nrRecEvt do S-1210 bloqueador, grupo=2                |
| 4     | S-1200 | Retificar remuneração Dez/2024 (indRetif=2)       | nrRecibo=`1.1.0000000030324738244`, mesmo payload     |
| 5     | S-1210 | Retificar pagamentos Dez/2024 (indRetif=2)        | nrRecibo=`1.1.0000000039598280881`, mesmos infoPgto   |
| 6     | S-1210 | Reincluir pagamentos Jan/2025 (indRetif=1)        | Mesmos infoPgto do S-1210 excluído no passo 3         |
| 7     | S-1299 | Fechamento Dez/2024                               | perApur=2024-12                                       |
| 8     | S-1299 | Fechamento Jan/2025                               | perApur=2025-01                                       |

### Resultado esperado

- Novo S-5002 gerado com rubrica 566 classificada como tpInfoIR=7900 (dedução INSS) com codIncIRRF=41
- Novo S-5002 gerado com rubrica 596 classificada com codIncIRRF=42 (dedução INSS 13º)
- Informe de rendimentos corrigido para declaração IRPF do trabalhador

---

## 7. Observações

1. **Período Dezembro 2024**: Sandro recomendou "retifique um CPF de teste em Janeiro". Este download (29076329) tem pouquíssimos CPFs ativos com IRRF em Janeiro 2025. Dezembro 2024 valida o mesmo mecanismo do pipeline.

2. **Rubricas 9276 e 9284**: Existem no DmDev 1 mas NÃO na tabela `cruzamento_eb`. São possivelmente rubricas de 13º ou parcelas específicas. Não serão afetadas pelo pipeline.

3. **S-1200 já retificado**: O S-1200 vigente já é uma retificação (indRetif=2). Nossa nova retificação será a SEGUNDA retificação, referenciando o recibo da retificação anterior (...30324738244).

4. **S-3000 intermediário**: Foi excluído um evento com nrRecEvt=...30324097296, gerando S-5002 vazio. Isso não afeta o estado atual.

5. **IRRF divergente**: A rubrica 570 (DESC. IRF) mostra R$ 39,63, mas o S-5002 (tpInfoIR=31) mostra R$ 65,34 de IRRF retido. A diferença (R$ 25,71) pode vir do IRRF sobre 13º salário.

---

## 8. Log de Execução

### 8.1 Etapa 0 — Correção S-1010 (Pré-requisito)

Executada em produção antes do pipeline. Alteração dos códigos de incidência IRRF nas rubricas 566 e 596 via evento S-1010 (evtTabRubrica).

| Data       | Rubrica | Campo      | De  | Para | nrRecibo                          | Status     |
| ---------- | ------- | ---------- | --- | ---- | --------------------------------- | ---------- |
| 2026-04-05 | 566     | codIncIRRF | 11  | 41   | `1.1.0000000039598012258`         | ✅ Sucesso |
| 2026-04-05 | 596     | codIncIRRF | 12  | 42   | `1.1.0000000039598028920`         | ✅ Sucesso |

### 8.2 Pipeline de Recuperação — 8 Etapas

**Execução:** Produção (ambiente=1), via endpoint `/api/pipeline/recuperar`  
**Resultado final:** ✅ COMPLETO — 8/8 etapas OK

| Passo | Evento | Período | Status | Código | nrRecibo / Detalhe                     |
| ----- | ------ | ------- | ------ | ------ | -------------------------------------- |
| 1     | S-1298 | 2025-01 | ✅ OK  | 715    | (JÁ ABERTO) Folha já estava aberta    |
| 2     | S-1298 | 2024-12 | ✅ OK  | 715    | (JÁ ABERTO) Folha já estava aberta    |
| 3     | S-3000 | 2025-01 | ✅ OK  | 201    | `1.1.0000000039598957342`             |
| 4     | S-1200 | 2024-12 | ✅ OK  | 201    | `1.1.0000000039598957701`             |
| 5     | S-1210 | 2024-12 | ✅ OK  | 201    | `1.1.0000000039598958189`             |
| 6     | S-1210 | 2025-01 | ✅ OK  | 201    | `1.1.0000000039598958954`             |
| 7     | S-1299 | 2024-12 | ✅ OK  | 201    | `1.1.0000000039598960033`             |
| 8     | S-1299 | 2025-01 | ✅ OK  | 201    | `1.1.0000000039598961340`             |

### 8.3 Problemas Encontrados e Soluções

#### Problema 1 — Erro 989 (Plano Original)
O plano original de 5 passos falhava porque retificar o S-1210 de Janeiro/2025 com dados idênticos NÃO libera as referências `dmDev` (10711955 / 10711965) no eSocial. O governo retorna erro 989: "Existe evento de pagamento para o trabalhador no período de apuração informado referenciando o demonstrativo."

**Solução:** Redesenhar para 8 etapas — excluir S-1210 Jan/2025 via S-3000 (evtExclusao), retificar os eventos alvo (Dez/2024), e re-incluir S-1210 Jan/2025 como evento novo.

#### Problema 2 — S-3000 Grupo Incorreto (Erro 101)
O evento S-3000 estava sendo enviado no grupo "3" (periódicos), mas o tipo evtExclusao exige grupo "2" (não-periódicos).

**Solução:** Alterar o grupo para "2" nas chamadas do pipeline (sync e streaming).

#### Problema 3 — S-3000 Campo indApuracao Rejeitado
O eSocial rejeitou o S-3000 porque o campo `indApuracao` dentro de `ideFolhaPagto` não é aceito para eventos de exclusão — apenas `perApur` é válido.

**Solução:** Remover `indApuracao` do XML gerado em `xml_s3000.py`.

#### Problema 4 — Instabilidade de Conexão
O webservice do eSocial apresentou quedas frequentes de conexão ("Remote end closed connection without response") tanto no envio quanto na consulta.

**Solução:** Implementar retry robusto:
- MAX_SEND_RETRIES: 3 → 5
- MAX_POLL_RETRIES: 5 → 8
- POLL_DELAY_SECS: 12 → 15
- SEND_RETRY_DELAY: 8 → 10
- Tratamento de erro de conexão no polling (antes fazia `break`, agora faz `continue`)

---

## 9. Verificação Pós-Pipeline

### 9.1 S-5002 Vigente Pré-Correção

Dados extraídos do arquivo `ID0020000000000000000000030328525269.S-5002.xml` (download cirúrgico anterior ao pipeline):

| Campo        | Valor                            |
| ------------ | -------------------------------- |
| nrRecArqBase | `1.1.0000000030328525269`        |
| perApur      | 2024-12                          |
| cpfBenef     | 08132588983                      |

**Demonstrativo 10711884 (perRef 2024-11, dtPgto 2024-12-06):**

| tpInfoIR | Descrição                        | Valor        |
| -------- | -------------------------------- | ------------ |
| 11       | Rendimento tributável            | R$ 3.219,33  |
| 7900     | Contribuição previd. (INSS)      | -R$ 270,99   |
| 31       | IRRF retido                      | R$ 65,34     |

**Demonstrativo 10711933 (perRef 2024, dtPgto 2024-12-20):**

| tpInfoIR | Descrição                        | Valor        |
| -------- | -------------------------------- | ------------ |
| 7900     | Contribuição previd. (INSS)      | R$ 0,40      |
| 12       | Rendimento 13º salário           | R$ 2.106,33  |

**Dependente IRRF:**

| tpRend | CPF Dep.    | Nome                    | vlrDedDep  | tpDep |
| ------ | ----------- | ----------------------- | ---------- | ----- |
| 12     | 14020816930 | LUIZA MARIA SILVA MOREIRA | R$ 189,59  | 03    |
| 11     | 14020816930 | LUIZA MARIA SILVA MOREIRA | R$ 189,59  | 03    |

### 9.2 S-5002 Pós-Correção (NOVO)

> ⛔ **NÃO DISPONÍVEL — Bloqueio eSocial dias 1-7**
>
> Tentativas em 04/04/2026:
> - `consultar_identificadores_trabalhador` → Erro 403: "Não é possível enviar solicitação de download entre os dias 1 e 7 do mês"
> - Conexões caindo com "Remote end closed connection without response"
>
> O S-5002 novo (gerado pelo S-1299 Dez/2024, recibo `1.1.0000000039598960033`) **existe no eSocial** mas só pode ser baixado **a partir de 08/04/2026**.

### 9.3 Por que o PRÉ e PÓS parecem iguais?

O S-5002 pré-correção (seção 9.1) já mostrava `tpInfoIR=7900` para INSS. Isso é esperado:

- O eSocial usa a **natureza da rubrica** (natRubr=9201, Contribuição Previdenciária) para classificar no S-5002, **não** o `codIncIRRF`
- Portanto, o `tpInfoIR=7900` aparece independente de o `codIncIRRF` ser 11 ou 41

**Então a correção não mudou nada no S-5002?** Provavelmente os valores ficarão muito parecidos. O efeito principal é:
1. **Conformidade cadastral** — a tabela de rubricas agora classifica corretamente INSS como dedução (41/42)
2. **Informe de rendimentos (DIRF/eFinanceira)** — sistemas externos que leem `codIncIRRF` diretamente agora recebem o valor correto
3. **Prevenção** — se o eSocial mudar o motor de cálculo para usar `codIncIRRF` em vez de `natRubr`, a classificação já estará correta

### 9.4 Verificação Pendente (após dia 8)

Executar para comparar PRÉ vs PÓS:

```bash
cd python-scripts
python download_s5002_retry.py
```

**O que verificar no S-5002 novo:**
- `nrRecArqBase` deve ser diferente do antigo (`1.1.0000000030328525269`)
- Valores de `tpInfoIR` devem ser recalculados (podem ou não mudar)
- Se houver diferença nos valores de `tpInfoIR=11` (rendimento tributável) ou `tpInfoIR=7900` (dedução INSS), documentar aqui

---

## 10. Resumo Executivo

### Problema
As rubricas 566 (DESC. I.N.S.S.) e 596 (DESC. I.N.S.S. S/13º) estavam cadastradas no eSocial com `codIncIRRF` incorreto — classificando contribuição previdenciária como "rendimento tributável" (códigos 11 e 12) em vez de "dedução do IRRF" (códigos 41 e 42). Isso gerava inconsistência no informe de rendimentos para declaração IRPF.

### Solução Implementada
1. **Correção tabular (S-1010):** Alteração permanente dos códigos `codIncIRRF` das rubricas 566 (11→41) e 596 (12→42) em produção
2. **Pipeline de recuperação (8 etapas):** Reabertura das folhas de Dez/2024 e Jan/2025, exclusão do S-1210 bloqueador via S-3000, retificação do S-1200 e S-1210 de Dez/2024 com as rubricas corrigidas, reinclusão do S-1210 de Jan/2025, e fechamento de ambos os períodos — forçando recálculo dos totalizadores S-5001/S-5002

### Dados-Chave

| Item                     | Valor                                   |
| ------------------------ | --------------------------------------- |
| CPF                      | 081.325.889-83                          |
| Matrícula                | 001-001-056502                          |
| CNPJ empregador          | 05.969.071/0001-10                      |
| Período alvo             | Dezembro/2024                           |
| Período bloqueador       | Janeiro/2025                            |
| Dependente IRRF          | LUIZA MARIA SILVA MOREIRA (14020816930) |
| Pipeline                 | 8/8 etapas OK ✅                         |
| Certificado              | SAFEWEB (ID 139, A1)                    |

### Status Final

| Componente                | Status                                           |
| ------------------------- | ------------------------------------------------ |
| S-1010 rubrica 566        | ✅ Corrigida (codIncIRRF 11→41)                  |
| S-1010 rubrica 596        | ✅ Corrigida (codIncIRRF 12→42)                  |
| S-1200 Dez/2024           | ✅ Retificado (recibo `...39598957701`)           |
| S-1210 Dez/2024           | ✅ Retificado (recibo `...39598958189`)           |
| S-3000 S-1210 Jan/2025    | ✅ Excluído (recibo `...39598957342`)             |
| S-1210 Jan/2025           | ✅ Reincluído (recibo `...39598958954`)           |
| S-1299 Dez/2024           | ✅ Fechado (recibo `...39598960033`)              |
| S-1299 Jan/2025           | ✅ Fechado (recibo `...39598961340`)              |
| S-5002 novo (verificação) | ⏳ Aguardando download (bloqueio dias 1-7)       |
