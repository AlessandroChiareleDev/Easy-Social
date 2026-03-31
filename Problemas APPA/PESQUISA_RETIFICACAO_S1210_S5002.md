# PESQUISA — Retificação de Eventos Periódicos (S-1210, S-1200, S-1298, S-1299) e Totalizador S-5002

> Pesquisa realizada via web em jul/2026 — Fontes: IOB Aprendo, Londrisoft, MGP Consultoria, Sankhya, gov.br

---

## 1. Como Funciona a Retificação no eSocial

### Princípio Geral

Todo evento periódico no eSocial pode ser **retificado** após o envio. Para retificar:

1. Enviar novo evento com **`indRetif = 2`** (indicativo de retificação)
2. Informar o **`nrRecibo`** do evento original que está sendo retificado
3. O novo evento deve se referir ao **mesmo CPF** e ao **mesmo período de apuração**

> **"Para retificar um evento, a empresa deve enviar o mesmo evento com a tag indRetif=2 e indicar o número do recibo do evento original."** — Londrisoft

### O que é o nrRecibo

- É o número de protocolo retornado pelo eSocial quando um evento é aceito
- Formato: string alfanumérica (ex: `1.2.2024.0000000000123456789`)
- Está no XML de retorno do eSocial, dentro de `<recibo><nrRecibo>`
- **Sem o nrRecibo, é impossível retificar**
- Nosso sistema já captura e armazena na coluna `nr_recibo` da tabela `esocial_envios`

---

## 2. Eventos Periódicos Relevantes — Hierarquia

```
S-1200 (Remuneração)       ← define os valores pagos ao trabalhador
    ↓ depende de
S-1210 (Pagamentos)        ← quando/como foi pago, com deduções de IR
    ↓ gera automaticamente
S-5002 (Totalizador IRRF)  ← retorno do eSocial com totalização de IR
    ↓
S-1299 (Fechamento)        ← fechamento do período
```

### Regras de Dependência

| Ação                  | Pré-requisito                                              |
| --------------------- | ---------------------------------------------------------- |
| Retificar S-1200      | Se existir S-1210 vinculado, **excluir o S-1210 PRIMEIRO** |
| Retificar S-1210      | Pode retificar diretamente (indRetif=2 + nrRecibo)         |
| Retificar após S-1299 | **Precisa enviar S-1298 (Reabertura) antes**               |
| Excluir S-1200        | Excluir S-1210 vinculado primeiro                          |

> **"Se o evento S-1200 a ser excluído tem S-1210 relacionado, o S-1210 deve ser excluído PRIMEIRO"** — IOB Aprendo

---

## 3. S-1298 — Reabertura dos Eventos Periódicos

### Quando é necessário

O S-1298 é necessário quando:

- Já foi enviado S-1299 (fechamento) do período
- E é necessário **retificar ou excluir** algum evento periódico daquele período

### Como funciona

1. Enviar S-1298 para o período desejado → "reabre" o período
2. Enviar a retificação ou exclusão desejada
3. Enviar novo S-1299 para fechar novamente o período

### Considerações

- Não é necessário se o período ainda não foi fechado (S-1299 não enviado)
- A reabertura permite qualquer alteração nos eventos daquele período
- Pode ser feito para meses passados (retroativo)

---

## 4. S-5002 — Imposto de Renda Retido na Fonte por Trabalhador

### O que é

- **NÃO é um evento que a empresa envia**
- É um **retorno automático** do eSocial gerado após cada S-1210 transmitido
- Contém a totalização dos rendimentos tributáveis, não tributáveis, IRRF, deduções, isenções
- Gerado por CPF + período de apuração

> **"Este evento não deve ser enviado, é um retorno do eSocial para cada evento S-1210 transmitido. Constará totalização dos rendimentos tributáveis e não tributáveis e do IRRF, deduções do rendimento tributável bruto, isenções, demandas judiciais"** — MGP Consultoria

### Como o S-5002 Totaliza

#### Para pagamento total (tpPgto = 1):

- Os valores vêm dos **eventos de remuneração (S-1200)** referentes àquele período
- Usa o `codIncIRRF` de cada rubrica para classificar

#### Para pagamento parcial (tpPgto = 2):

- Todas as informações vêm do **S-1210** diretamente

### Classificação pelo codIncIRRF no S-5002

| Grupo codIncIRRF   | Classificação no S-5002             | Destino                                         |
| ------------------ | ----------------------------------- | ----------------------------------------------- |
| 11, 12, 13, 14     | Rendimentos tributáveis             | Base de cálculo IRPF                            |
| 31, 32, 33, 34, 35 | **IRRF efetivamente descontado**    | **Alimenta sistemas internos da RFB para IRPF** |
| 41-48              | Deduções da base tributável         | Reduz base de cálculo                           |
| 51-55              | Pensão alimentícia                  | Dedução específica                              |
| 61-66              | FAPI                                | Dedução                                         |
| 67                 | Plano de saúde                      | Declaração de ajuste                            |
| 68                 | Desconto simplificado               | Dedução mensal                                  |
| 70-79              | Rendimentos isentos/não tributáveis | "Rendimentos Isentos e Não Tributáveis"         |
| 9xxx               | Exigibilidade suspensa              | **Apenas parâmetros de malha fiscal**           |
| 9 (puro)           | Verba transitória                   | **NÃO ENTRA EM NENHUM GRUPO**                   |

> **"Os valores informados cujos codIncIRRF sejam [31,32,33,34,35] = efetivamente descontado pelo empregador = alimentam sistemas internos da RFB para IRPF"** — MGP Consultoria

> **"Valores cujos códigos de incidência sejam iniciados com numeral '9' (exigibilidade suspensa) = utilizados apenas como parâmetros de malha fiscal"** — MGP Consultoria

### Previdência Complementar no S-5002

Para que previdência complementar apareça corretamente:

- O codIncIRRF deve ser **46, 47, 48, 61, 62, 63, 64, 65 ou 66**
- E o tpRubr deve ser **2** (desconto)
- Se não atender ambos critérios, não é considerada como dedução

---

## 5. Correção de IRRF para Períodos Anteriores — InfoIRComplem

### A Descoberta Crucial (Sankhya)

Existe um mecanismo no eSocial para corrigir dados de IRRF de **anos-calendário anteriores SEM reabrir a folha de pagamento**:

> **"Correções são realizadas SEM reabertura da folha e enviadas no S-1210 de janeiro de cada ano no grupo Informações Complementares de IR dos Períodos Anteriores (InfoIRComplem)"** — Sankhya

### Como funciona

1. As correções são feitas **exclusivamente no mês de janeiro**
2. Referem-se sempre ao **ano-calendário anterior**
3. São enviadas dentro do S-1210 de janeiro
4. Usam o grupo XML `InfoIRComplem`
5. **Máximo de 13 ocorrências** do grupo InfoIRComplem por evento
6. **Não impactam o cálculo da folha do período de origem**

> **"As correções devem ser realizadas exclusivamente no mês de janeiro, sempre referentes ao ano-calendário anterior"** — Sankhya

> **"As alterações feitas nessa tela não impactam o cálculo da folha do período de origem. Existem apenas para ajuste e envio correto das informações ao eSocial"** — Sankhya

### Características importantes

- Funciona mesmo para **empregados não mais ativos** na empresa
- Cada InfoIRComplem representa um mês do ano anterior (jan-dez + 13º = 13 ocorrências)
- Pode corrigir: rendimentos tributáveis, deduções, isenções, retenções
- **É apenas um ajuste declaratório** — não altera folha de pagamento

### Implicação para a APPA

Se o ano-calendário corrente pode ser corrigido via retificação direta do S-1210, E o ano anterior via InfoIRComplem em janeiro, então:

- Para 2025: retificar S-1210 diretamente (indRetif=2 + nrRecibo)
- Para 2024: usar InfoIRComplem no S-1210 de janeiro/2026
- **MAS PRIMEIRO**: o S-1010 (rubricas) precisa estar correto

---

## 6. Fluxo de Correção Completo para a APPA

### Passo 1: Corrigir S-1010 (Tabela de Rubricas) ← ESTAMOS AQUI

```
Para cada rubrica com codIncIRRF errado:
  1. Enviar S-1010 com indRetif=2 (alteração)
  2. Informar nrRecibo do S-1010 original
  3. Corrigir codIncIRRF para o valor correto
  4. eSocial aceita → rubrica atualizada
```

**Importante:** Alterar o S-1010 NÃO altera retroativamente os S-1210/S-5002 já enviados. O S-1010 só afeta **envios futuros**.

### Passo 2: Retificar S-1210 (Pagamentos)

```
Para cada período afetado:
  1. Se S-1299 já foi enviado → enviar S-1298 (reabertura) primeiro
  2. Enviar S-1210 com indRetif=2 + nrRecibo do S-1210 original
  3. O S-1210 retificado usará as rubricas já corrigidas no S-1010
  4. eSocial gera novo S-5002 com totais corretos
  5. Enviar novo S-1299 para fechar período
```

### Passo 3: Correção de anos anteriores (se necessário)

```
Em janeiro do ano seguinte:
  1. Montar S-1210 de janeiro com grupo InfoIRComplem
  2. Cada ocorrência = um mês do ano anterior
  3. Máximo 13 ocorrências (jan-dez + 13º)
  4. Enviar normalmente
  5. eSocial processa e gera S-5002 atualizado
```

---

## 7. Cenários para a APPA

### Cenário A — Só corrigir S-1010 (rubricas)

- **Prós:** Mais simples, previne erros futuros
- **Contras:** NÃO corrige períodos passados. Os Informes de Rendimentos do passado continuam errados.
- **Impacto:** Milhares de funcionários ainda com dedução de INSS zerada nos informes anteriores

### Cenário B — Corrigir S-1010 + Retificar S-1210

- **Prós:** Corrige passado e futuro
- **Contras:** Precisa retificar S-1210 de cada período afetado para cada trabalhador
- **Volume:** Se 16-20K funcionários × 12 meses = 192K-240K retificações
- **Complexidade:** Alta — precisa de nr_recibo de cada S-1210 original, possivelmente S-1298 se períodos fechados
- **Necessidade:** Confirmação do Sandro/Dra. Cynthia sobre viabilidade

### Cenário C — Corrigir S-1010 + InfoIRComplem em janeiro

- **Prós:** Não precisa reabrir folhas, mais limpo
- **Contras:** Só funciona em janeiro, máximo 13 períodos por envio
- **Viabilidade:** Depende de quando estamos — se passarmos de janeiro, esperar próximo

### Cenário D (recomendado) — Abordagem combinada

1. **Imediato:** Corrigir S-1010 (o que estamos fazendo)
2. **Ano corrente:** Retificar S-1210 do ano corrente via indRetif=2
3. **Ano anterior:** Usar InfoIRComplem no S-1210 de janeiro
4. **Mais antigos:** Avaliar com o Sandro se há obrigação legal

---

## 8. Perguntas Pendentes para o Sandro

1. **Quais períodos estão com S-1299 fechado?** → Determina se precisamos de S-1298
2. **Temos os nrRecibo dos S-1210 originais?** → Sem eles, não podemos retificar
3. **A APPA já fez retificações de S-1210 antes?** → Para saber se já existe processo
4. **A consultoria considerou usar InfoIRComplem?** → Pode ser o caminho mais limpo
5. **Qual a prioridade: ano corrente ou anos anteriores?** → Define a estratégia

---

## 9. Fontes

1. **IOB Aprendo** — "Empregador: retificação de eventos periódicos no eSocial"
2. **Londrisoft** — "Como retificar eventos no eSocial: passo a passo"
3. **MGP Consultoria** — "Entenda o Evento S-5002 — Imposto de Renda Retido na Fonte"
4. **Sankhya** — "Correção de dados do IRRF de anos-calendário anteriores"
5. **gov.br** — Manual de Orientação do eSocial (MOS), versão S-1.3
