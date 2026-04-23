# Plano de Resolução — Erros Restantes do S-1210 Fev/2025

> **Contexto:** Lote 1 de Fev/2025 foi 100% processado (9.471 CPFs). Resultado: **8.540 OK (90,2 %)** · **931 erro (9,8 %)** · **0 pendente**.
> **Este documento:** estratégia para tratar os 931 erros **sem gastar consultas desnecessárias** ao eSocial.
> **Data:** 22/04/2026.
> **Base:** comparação com o [RELATORIO_ERROS_S1210_L1_FEV2025.md](../RELATORIO_ERROS_S1210_L1_FEV2025.md) de 21/04.

---

## 1. Quadro atual dos 931 erros

| Tipo                                      | Qtd | % dos erros | Natureza                     |
| ----------------------------------------- | --: | ----------: | ---------------------------- |
| **buscar_recibo** (ZIP sem S-1210 do CPF) | 780 |      83,8 % | Pré-envio (antes do eSocial) |
| **401/459** (recibo excluído/retificado)  |  94 |      10,1 % | Rejeitado pelo AN            |
| **401/8** (falta `<infoBenef>` de pensão) |  57 |       6,1 % | Rejeitado pelo AN — bug XML  |
| **Total**                                 | 931 |       100 % |                              |

### O que sumiu da rodada anterior (21/04)

| Tipo     | Tinha em 21/04 | Agora | Por quê sumiu                                     |
| -------- | -------------: | ----: | ------------------------------------------------- |
| **1089** |            216 |     0 | Rodada sequencial atual não reproduz concorrência |
| **543**  |             81 |     0 | Sem reenvio duplicado, idempotência não dispara   |

---

## 2. Estratégia geral — ordem e custo

> **Princípio orientador:** nenhum dos 3 tipos exige consulta ao eSocial como pré-requisito. Consulta só entra no **fallback opcional** do 459. O limite de 10 downloads cirúrgicos/dia é preservado.

| Ordem | Tipo                | Ação                                       | Consulta ao eSocial?         |                           Impacto esperado |
| ----: | ------------------- | ------------------------------------------ | ---------------------------- | -----------------------------------------: |
| **1** | 401/8 (57)          | Corrigir gerador `xml_s1210.py` e reenviar | **Zero**                     |                                    57 → OK |
| **2** | buscar_recibo (780) | Enviar como `indRetif=1` (envio original)  | **Zero**                     | ~600-780 → OK (resto pode cair em 543/459) |
| **3** | 401/459 (94)        | Reenviar como `indRetif=1`                 | **Zero** (fallback opcional) |                                    Parcial |

---

## 3. Tratamento — erro 401/8 (pensão alimentícia)

### Diagnóstico

Erro do eSocial:

> "Grupo 'Informação dos beneficiários da pensão alimentícia' deve ser preenchido. Verifique as condições…"

O gerador `python-scripts/esocial/xml_s1210.py` **não inclui** o bloco `<infoBenef>` dentro de `<infoIRCR>` quando o CPF tem rubrica de pensão alimentícia (códigos 1801/1809 ou equivalentes). O eSocial exige esse grupo sempre que existe valor de pensão alimentícia na folha.

### Estrutura XML exigida

```xml
<infoIRCR>
  <tpCR>...</tpCR>
  <vrCR>...</vrCR>
  <infoBenef>
    <cpfDep>XXXXXXXXXXX</cpfDep>
    <vlrPensao>NNN.NN</vlrPensao>
  </infoBenef>
</infoIRCR>
```

### Fonte dos dados do beneficiário

- Tabela de dependentes cadastrados do colaborador (CPF do beneficiário + valor de pensão daquele mês).
- Dado já existe no banco do legado APPA / no sistema de folha; precisa ser propagado até o builder do XML.

### Plano

1. Localizar em `xml_s1210.py` o ponto onde se monta `<infoIRCR>`.
2. Detectar rubrica de pensão alimentícia na lista de itens do S-1200/S-1210 do CPF.
3. Carregar os beneficiários (CPF + valor) a partir da fonte de dados correspondente (tabela de dependentes ou campo já extraído no XML legado original).
4. Emitir um `<infoBenef>` por beneficiário dentro do `<infoIRCR>` apropriado.
5. Reenviar os 57 CPFs.

### Risco

Baixo. É bug de conteúdo do XML, sem dependência externa. A validação é pelo próprio eSocial na resposta.

---

## 4. Tratamento — buscar_recibo (780 CPFs sem S-1210 original no ZIP)

### Diagnóstico

Nosso pipeline tenta localizar o `nrRecibo` do S-1210 original do CPF dentro do ZIP de downloads cirúrgicos. Para 780 CPFs **não existe** S-1210 original no ZIP — então não dá pra **retificar** (`indRetif=2`) porque não tem o que retificar.

Isso significa uma de duas coisas:

- **O CPF nunca teve S-1210 enviado** em Fev/2025 (provável em 90%+ dos casos, porque o legado da APPA pulou estes meses para parte da base).
- O ZIP que temos é incompleto (improvável — o ZIP cobre o mês todo).

### Plano — tentar envio original

Para cada um dos 780 CPFs:

1. Gerar XML com `indRetif=1` (envio original), **sem** `nrReciboEvtOriginal`.
2. Enviar em batch.
3. Processar o retorno:
   - **OK** → fim (estes CPFs entram pela primeira vez).
   - **Erro 543** ("já existe evento com mesmo identificador") → significa que o AN de fato já tinha um S-1210 para aquele CPF que nosso ZIP não capturou. Nesse caso o evento já está lá — tratar como `ok_idempotente` (não precisa retransmitir; pode criar campo `nr_recibo_encontrado` consultando apenas o essencial).
   - **Erro 459** → variante: o evento estava lá mas foi retificado. Tratar igual ao bloco 5 abaixo.
   - **Outros erros** → tratar caso a caso.

### Por que isso não custa consulta

O envio pelo `WsEnviarLoteEventos.svc` **não conta** para o limite de 10/dia do Download Cirúrgico. Só o `WsSolicitarDownloadEventos.svc` é limitado.

### Risco

Baixo-médio. A pior consequência de um envio original para um CPF que já tinha S-1210 no AN é receber 543 e marcar idempotente — não desconfigura nada.

---

## 5. Tratamento — erro 401/459 (recibo excluído/retificado)

### Diagnóstico

O `nr_recibo_usado` que está no banco do legado **não é o recibo vigente** do CPF no eSocial. O recibo foi excluído ou substituído por uma retificação anterior.

### Plano — opção sem consulta

Mesma estratégia do bloco 4:

1. Reenviar como `indRetif=1` (original).
2. Se voltar 543: o evento vigente está lá; marcar idempotente.
3. Se voltar 459 de novo: bloqueio real; mover para aba de pendência manual.
4. Se voltar OK: o evento anterior foi realmente excluído, e nosso envio substituiu.

### Plano — opção com consulta (fallback)

Só executar se o cliente autorizar explicitamente:

- Solicitar download cirúrgico dos 94 CPFs (limite de quota — distribuir em dias).
- Extrair o recibo vigente.
- Reenviar como retificação com o recibo correto.

### Risco

Baixo na opção sem consulta. O pior caso é 94 ficarem novamente em erro e virarem pendência manual.

---

## 6. Implementação por fases

### Fase 1 — Fix de conteúdo (57 CPFs)

- Arquivo: `python-scripts/esocial/xml_s1210.py`.
- Escopo: adicionar `<infoBenef>` quando detectar pensão alimentícia.
- Teste: gerar XML para 1 CPF conhecido, validar contra XSD do eSocial localmente.
- Envio: rodar para os 57 CPFs em batch.
- Esperado: 57 OK.

### Fase 2 — Envio original para buscar_recibo (780 CPFs)

- Arquivo: `python-scripts/esocial/s1210_repo_routes.py` (endpoint `/enviar-lote-cpfs`).
- Escopo: adicionar parâmetro / modo que permita `indRetif=1` para CPFs marcados como `buscar_recibo`.
- Envio: rodar em blocos de 1000 (já validado que o bot aguenta).
- Esperado: maioria OK, uma fração em 543 (tratar como idempotente), pequena fração em 459/outros.

### Fase 3 — Envio original para 459 (94 CPFs)

- Mesma lógica da Fase 2, aplicada aos 94 CPFs com erro 459.
- Esperado: parcial OK, parcial 543 idempotente, alguns em 459 persistente.

### Fase 4 — Consolidação

- CPFs que persistirem em erro após as 3 fases → aba separada de revisão manual.
- Esperado: bem abaixo de 100 CPFs.

---

## 7. Fora de escopo deste documento

Este plano cobre **apenas o Lote 1 de Fev/2025**. Os outros meses (Mar/2025, Abr/2025) e os lotes 2/3/4 de Fev/2025 — total de **23.330 CPFs pendentes** — precisam ser processados antes que este plano valha para eles. Mas os **mesmos 3 tipos de erro** provavelmente aparecerão proporcionalmente, e a mesma estratégia se aplica.

---

## 8. Tabela de decisão rápida

| Se o CPF está em…   | Fazer                                  | Consome quota?         | Resultado típico |
| ------------------- | -------------------------------------- | ---------------------- | ---------------- |
| 401/8               | Corrigir XML e reenviar                | **Não**                | OK               |
| buscar_recibo       | Enviar como original                   | **Não**                | OK ou 543        |
| 401/459             | Enviar como original                   | **Não**                | OK, 543 ou 459   |
| 401/543 (fase 2)    | Marcar idempotente                     | **Não**                | `ok_idempotente` |
| 401/459 persistente | Pendência manual ou download cirúrgico | **Sim** (se consultar) | Resolução manual |

---

## 9. Próxima ação sugerida

Implementar **Fase 1** (fix do 401/8 no gerador `xml_s1210.py`), rodar nos 57 CPFs, e apresentar resultado antes de avançar para a Fase 2.
