# Prints de Referência — Telas do eSocial

> Descrição detalhada dos 4 prints de tela do sistema eSocial que servem como referência visual para o fluxo de validação e correção de rubricas.

---

## Print 1: Tela de Busca no eSocial

**Localização no fluxograma**: Etapa 5 — "BUSCAR NO eSocial"

**URL/Navegação**: Empregador/Contribuinte > Tabelas > Tabela de Rubricas

**Cabeçalho do sistema**:

- Logo: eSocial — Módulo: Geral Pessoa Jurídica
- Titular do Certificado: 05.969.071/0001-10 - APPA SERVICOS TEMPORARIOS E EFETIVOS LTDA:05969071000110
- Menu: Empregador/Contribuinte | Empregado | Trabalhador sem Vínculo | Download | Folha de Pagamento | Ajuda

**Título da página**: Tabela de Rubricas

**Seção "Filtro de pesquisa"**:
| Campo | Valor |
|-------|-------|
| Identificador da Tabela de Rubricas | Todos (dropdown) |
| Código da rubrica | `11` (campo texto) |

**Botão**: "Cadastrar nova Rubrica"

**Rodapé**: Ministério da Previdência Social | Ministério do Trabalho e Emprego | Secretaria Especial da Receita Federal do Brasil

**Versão**: eSocial.RecepcaoEvento: 15.9.18 | eSocial.Web.Negocio: 3.15.35

---

## Print 2: Resultado da Busca (Validação Regex)

**Localização no fluxograma**: Etapa 6 — "VALIDAR RETORNO REGEX"

**Título da página**: Tabela de Rubricas

**Filtro aplicado**: Identificador da Tabela de Rubricas = Todos | Código da rubrica = `11`

**Seção "Resultado da pesquisa"**:

### Bloco 1: Identificador da Tabela: 1 - Código da Rubrica: 11

| Início da Validade | Término da Validade | Descrição da Rubrica                       | Natureza da Rubrica | Tipo da Rubrica | Incidência CP | Incidência IR | Incidência FGTS | Data de Recepção    | Ação              |
| ------------------ | ------------------- | ------------------------------------------ | ------------------- | --------------- | ------------- | ------------- | --------------- | ------------------- | ----------------- |
| 02/2018            | -                   | 1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao) | 6007                | Venc.           | 00            | 74            | 00              | 20/03/2026 14:08:54 | Alterar / Excluir |

Botão: "Incluir validade"

### Bloco 2: Identificador da Tabela: 1 - Código da Rubrica: 110

_(visível abaixo, demonstrando o comportamento regex da busca — buscou "11" e retornou também "110")_

Botão: "Incluir validade"

**CRÍTICO**: A busca por "11" retorna TANTO o código 11 quanto o 110 (e potencialmente 111, 1100, etc.). É obrigatória a validação dupla: código exato + descrição exata.

---

## Print 3: Tela de Edição (Estado com ERRO — D/E/F)

**Localização no fluxograma**: Etapa 8 — "ACESSAR EDIÇÃO" + Etapa 9 — "VALIDAR ESTADO ATUAL D/E/F"

### Seção "Identificação da Rubrica"

| Campo                                 | Valor     |
| ------------------------------------- | --------- |
| Código\*                              | `11`      |
| Início da Validade\*                  | `02/2018` |
| Término                               | _(vazio)_ |
| Identificador da Tabela de Rubricas\* | `1`       |

Botão: "Alterar"

### Seção "Informações da Rubrica"

| Campo                                            | Valor                                                           |
| ------------------------------------------------ | --------------------------------------------------------------- |
| Descrição\*                                      | `1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao)`                    |
| Natureza da Rubrica\*                            | `6007 - Férias vencidas na rescisão` (dropdown)                 |
| Tipo da Rubrica\*                                | `1 - Vencimento, provento ou pensão` (dropdown)                 |
| **Incidência Tributária - Previdência Social\*** | `00 - Não é base de cálculo` (dropdown) ← **D = INSS**          |
| **Incidência Tributária – IRRF\***               | _(VAZIO — campo em branco com bordas vermelhas)_ ← **E = IRRF** |
| **Incidência Tributária - FGTS\***               | `00 - Não é Base de Cálculo do FGTS` (dropdown) ← **F = FGTS**  |
| Incidência Tributária - CPRP                     | _(dropdown visível mas valor cortado)_                          |

**Erro visível**: "Campo de preenchimento obrigatório." abaixo do campo IRRF vazio.

**Estado D/E/F neste print**: `00 / (vazio) / 00` — **ERRADO**, precisa ser corrigido.

---

## Print 4: Valores Corrigidos (Estado correto — H/I/J)

**Localização no fluxograma**: Etapa 10 — "APLICAR CORREÇÃO"

### Seção "Identificação da Rubrica"

| Campo                                 | Valor     |
| ------------------------------------- | --------- |
| Código\*                              | `11`      |
| Início da Validade\*                  | `02/2018` |
| Término                               | _(vazio)_ |
| Identificador da Tabela de Rubricas\* | `1`       |

Botão: "Alterar"

### Seção "Informações da Rubrica"

| Campo                                            | Valor                                                                                                            |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Descrição\*                                      | `1/3 FERIAS VENCIDAS INDENIZADAS (Rescisao)`                                                                     |
| Natureza da Rubrica\*                            | `6007 - Férias vencidas na rescisão` (dropdown)                                                                  |
| Tipo da Rubrica\*                                | `1 - Vencimento, provento ou pensão` (dropdown)                                                                  |
| **Incidência Tributária - Previdência Social\*** | `00 - Não é base de cálculo` ← **H = INSS = 00**                                                                 |
| **Incidência Tributária – IRRF\***               | `74 - Indenização e rescisão de contrato, inclusive a título de PDV e acidentes de trabalho` ← **I = IRRF = 74** |
| **Incidência Tributária - FGTS\***               | `00 - Não é Base de Cálculo do FGTS` ← **J = FGTS = 00**                                                         |
| Incidência Tributária - CPRP                     | _(dropdown visível)_                                                                                             |

**Estado H/I/J neste print**: `00 / 74 / 00` — **CORRETO**, este é o estado-alvo.

**Campo corrigido**: IRRF foi de _(vazio)_ para `74 - Indenização e rescisão de contrato...`. O campo IRRF está com bordas azuis/verdes indicando que foi preenchido corretamente.

---

## Resumo da Correção Exemplo

| Campo                     | Antes (D/E/F) — Print 3 | Depois (H/I/J) — Print 4 |
| ------------------------- | ----------------------- | ------------------------ |
| INSS (Previdência Social) | 00                      | 00                       |
| IRRF                      | **(vazio)**             | **74**                   |
| FGTS                      | 00                      | 00                       |

**Regra de ouro**: D/E/F deve ser sempre igual a H/I/J. Quando não é, corrige-se D/E/F para igualar H/I/J.
