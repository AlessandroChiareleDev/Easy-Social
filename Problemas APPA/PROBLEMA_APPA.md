# PROBLEMA APPA — Mapa Completo dos Problemas Reais

## Contexto da Empresa

- **Empresa:** APPA Serviços Temporários e Efetivos LTDA (CNPJ: 05.969.071/0001-10)
- **Volume:** ~16.000 a 20.000 funcionários/beneficiários
- **Setor:** RH / Departamento Pessoal
- **Responsável RH:** Ana
- **Consultoria Tributária:** Doutora Cynthia + Sandro (parte técnica eSocial)
- **Sistema de Folha:** GI (sistema interno de folha de pagamento)
- **Certificado A1:** APPA via AC SAFEWEB RFB v5 (válido até 09/2026)

---

## 🔴 PROBLEMA CENTRAL: Fim da DIRF e Transição para eSocial 2025

### O que mudou

A partir de 2025, **o sistema DIRF deixou de existir**. A DIRF era um sistema separado onde o RH:

1. Extraía informações da folha de pagamento
2. Tratava manualmente o que deveria pagar (pensão, deduções, tudo)
3. Podia olhar **pessoa por pessoa**, tirar planilha individual
4. Jogava os dados corretos no sistema

Agora **tudo tem que funcionar pelo eSocial**, que substituiu a DIRF. O eSocial foi liberado para conferência no final de janeiro/2025.

### O que não funciona

No portal do eSocial, a conferência de IR mostra os dados **consolidados por empresa inteira** (não por pessoa). A Ana verifica por mês:

- Rendimentos de janeiro → tem que bater
- Rendimentos de fevereiro → tem que bater
- E assim por diante

**Problemas encontrados:**

1. **Deduções zeradas** — A verba 566 (desconto INSS) deveria aparecer nas deduções de IR mas **não veio nada**
2. **Verbas indenizatórias de rescisão zeradas** — Houve várias rescisões mas os valores estão **zerados** no eSocial
3. **16-20 mil pessoas aguardando** a declaração de IR e os dados estão errados

### Raiz do problema

O **evento S-1210** (Pagamentos / Imposto de Renda) está transmitindo dados incompletos. As rubricas não estão configuradas com as incidências corretas para que o eSocial compute adequadamente os rendimentos e deduções de IR.

---

## 📋 Inventário de Problemas Técnicos

### 1. Rubricas com Incidências Erradas no eSocial (S-1010)

| Métrica                                 | Valor                      |
| --------------------------------------- | -------------------------- |
| Total de rubricas na base               | 448 (cruzamento EB Skills) |
| Rubricas com divergência INSS/IRRF/FGTS | 154 pendentes              |
| Rubricas com natureza errada/duvidosa   | 91 (analise_natureza)      |
| Naturezas expiradas na Tabela 3         | 2                          |
| De-Para mapeamentos pendentes           | 1.143+                     |

**Status:** Temos o Easy e-Social fazendo a correção das S-1010 (rubricas). O envio em homologação já funciona (201 - Lote Recebido com Sucesso).

### 2. Evento S-1210 — Pagamentos de IR Incorretos

O evento S-1210 é o que consolida as informações de IR que antes iam para a DIRF. Problemas:

- **Verba 566 (INSS):** Certeza absoluta que precisa ser corrigida. Deveria aparecer nas deduções de IR, está zerada.
- **Verba 47:** Não subiu errada, mas "não subiu completamente certa, ficou faltando um tiquinho de coisa"
- **Verbas indenizatórias de rescisão:** Deveriam estar nos rendimentos, estão zeradas
- Isso afeta **todos os meses retroativos** (janeiro, fevereiro, etc.)

### 3. Conflito S-1200 vs S-1210

| Evento                    | Responsabilidade         | Pode mexer?  |
| ------------------------- | ------------------------ | ------------ |
| S-1200 (Remuneração/INSS) | Doutora Cynthia + Sandro | ❌ NÃO MEXER |
| S-1210 (Pagamentos/IR)    | Ana + Easy e-Social        | ✅ Retificar |

**Regra absoluta da Ana:** "Não vou ter problema porque eu não vou mexer no 1200. Vou fechar sem mexer nos valores dela."

O S-1200 é INSS. A Doutora Cynthia já gerencia essa parte com o Sandro. Qualquer correção que fizermos tem que ser **isolada ao S-1210**, sem impactar o S-1200.

### 4. Retroatividade

- Os meses de janeiro e fevereiro já foram fechados
- **Dúvida crítica:** Dá para fazer retroativo pelo GI ou terá que ser mês a mês daqui para frente + retificação manual dos meses passados?
- **Estratégia da Ana:** Abrir um mês de uma empresa pequena, fechar e ver o que acontece

### 5. Escala do Problema

- **Não é só a APPA** — Várias empresas no Brasil estão com o mesmo problema
- O sistema do eSocial para conferência de IR foi liberado no final de janeiro
- Impossível conferir pessoa por pessoa (o sistema não permite como a DIRF permitia)
- Funcionários esperando que "vai clicar no botão e está tudo resolvido" (não é assim)

---

## 🔧 O que o Easy e-Social já resolve

| Problema                             | Solução                                    | Status                         |
| ------------------------------------ | ------------------------------------------ | ------------------------------ |
| Rubricas com natureza errada         | Validador de naturezas (analise_natureza)  | ✅ 75/91 com sugestão          |
| Rubricas com incidência errada       | Cruzamento EB Skills (448 rubricas)        | ✅ Divergências detectadas     |
| Envio S-1010 (alteração de rubricas) | Pipeline XML → Assinatura → SOAP → eSocial | ✅ Funcional (homologação 201) |
| De-Para de campos                    | Mapeamento natRubr, tpRubr, codIncPisPasep | 🔄 Em progresso                |
| Edição manual de incidências         | Edição inline INSS/IRRF/FGTS no painel     | ✅ Implementado                |
| Bot automático PyAutoGUI             | Correção via interface real do eSocial     | ⏸️ Pausado                     |

## ❌ O que o Easy e-Social ainda NÃO resolve

| Problema                           | Complexidade                         |
| ---------------------------------- | ------------------------------------ |
| Retificação do S-1210              | Alta — depende de resposta do Sandro |
| Retroatividade de meses fechados   | Alta — depende da capacidade do GI   |
| Verbas indenizatórias de rescisão  | Média — precisa mapear quais verbas  |
| Conferência de IR por beneficiário | Não existe no eSocial novo           |
| Escala de 16-20 mil funcionários   | Precisa automação pós-validação      |

---

## 🎯 Perguntas Pendentes para o Sandro

1. **Para corrigir as deduções de IR (verba 566 e verba 47), é obrigatório retificar o S-1210?**
2. **A retificação do S-1210 gera algum impacto nos valores já consolidados no S-1200 (INSS)?**
3. **Para os meses já fechados (janeiro e fevereiro), como proceder para as deduções aparecerem retroativamente nos totalizadores de IR?**
4. **Se retificarmos o S-1210, o eSocial passa a reconhecer automaticamente a verba 566 e as verbas indenizatórias de rescisão que hoje estão zeradas?**
5. **Podemos validar a retificação do S-1210 em uma empresa piloto antes de aplicar para toda a base?**

---

## 📊 Fluxo de Dependências

```
Corrigir S-1010 (rubricas)     ← Easy e-Social faz isso
        │
        ▼
Retificar S-1210 (IR)          ← Depende da resposta do Sandro
        │
        ▼
Validar em empresa piloto      ← Um mês, uma empresa pequena
        │
        ▼
Aplicar retroativo (jan/fev)   ← Depende se GI suporta ou manual
        │
        ▼
Escalar para toda a base       ← 16-20 mil pessoas
        │
        ▼
Funcionários fazem declaração IR ← Objetivo final
```
