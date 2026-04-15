# MISSÃO ATUAL — Retificação S-1210 e Correção de IR no eSocial

> Baseado na reunião com Ana (APPA) transcrita via NotebookLM — Março 2026

---

## Resumo Executivo

A DIRF acabou em 2025. Agora tudo passa pelo eSocial. O evento S-1210 (Pagamentos / IR) está transmitindo dados incompletos — deduções de INSS (verba 566) e verbas indenizatórias de rescisão estão **zeradas** no portal. ~16-20 mil pessoas precisam da declaração de IR. A missão é: corrigir as rubricas (S-1010), retificar o S-1210, e fazer os totalizadores de IR baterem.

---

## O que a Ana disse (falas-chave da reunião)

### Sobre o problema:

> "As deduções não estavam batendo porque, que nem, ó, sabe aquela verba 566, que é o INSS? Deveria estar aqui, ó, e não veio nada. Aí, por exemplo, todas as verbas indenizatórias de rescisão deveriam estar aqui, e a gente teve um monte de rescisão e não veio nada, está zerado."

### Sobre o que perguntar para a Doutora Cynthia / Sandro:

> "A minha pergunta era para a doutora: se a gente vai conseguir fazer só mudando o evento sem passar de novo (ele vai calcular a folha) ou se eu vou ter que fazer uma retificação desse evento, porque foi dada a possibilidade de fazer retificação desse evento."

### Sobre a restrição do S-1200:

> "Se eu conseguir retificar a verba e fazer uma passada, e fazer uma retificação com o 1210, eu não vou ter problema porque eu não vou mexer no 1200."

### Sobre a estratégia de teste:

> "Se a gente tiver que retificar, a gente pega o quê? A gente abre um mês de uma empresa pequena, fecha e vê o que que vai dar."

### Sobre verbas para testar:

> "Se você for usar uma verba como exemplo para fazer retroativo, nem que for na base produção, usa a 566, que é o desconto do INSS, porque essa eu tenho tipo completa certeza que precisa ser mexida. A 47 também é outra verba que dá para mexer na fé."

### Sobre a escala:

> "Estou com mais ou menos umas quase 20.000 pessoas querendo a declaração de imposto de renda. Mas não somos só nós que estamos com problema, tá? Tem várias empresas que estão com problema no país."

---

## Missão FASE 1 — Corrigir S-1010 (Rubricas)

**Status: EM ANDAMENTO**

As rubricas precisam estar com natureza e incidências corretas ANTES de retificar o S-1210.

| Tarefa                                         | Status                     |
| ---------------------------------------------- | -------------------------- |
| Cruzamento EB Skills (448 rubricas)            | ✅ Feito                   |
| Divergências detectadas (INSS/IRRF/FGTS)       | ✅ 154 pendentes           |
| Validação de naturezas (91 VERIFICAR)          | ✅ 75/91 com sugestão      |
| Pipeline de envio S-1010 (XML→Assinatura→SOAP) | ✅ Funcional               |
| Envio homologação                              | ✅ 201 Lote Recebido       |
| Edição inline de incidências no painel         | ✅ Implementado            |
| De-Para mapeamentos                            | 🔄 Em progresso            |
| Envio em produção                              | ⏳ Após validação completa |

---

## Missão FASE 2 — Perguntas para o Sandro (Bloqueador)

Antes de qualquer ação no S-1210, precisamos das respostas técnicas:

1. **Para corrigir as deduções de IR (verba 566 e verba 47), é obrigatório retificar o S-1210?**
2. **A retificação do S-1210 gera algum impacto nos valores do S-1200 (INSS)?**
3. **Para os meses já fechados (jan/fev), como proceder para as deduções aparecerem retroativamente nos totalizadores de IR do eSocial?**
4. **Se retificarmos o S-1210, o eSocial reconhece automaticamente a verba 566 e verbas indenizatórias que hoje estão zeradas?**
5. **Podemos validar a retificação do S-1210 em uma empresa piloto antes de aplicar para toda a base?**

---

## Missão FASE 3 — Retificação S-1210 (Após resposta do Sandro)

Dependendo da resposta:

### Cenário A: Basta corrigir as rubricas (S-1010)

- Corrigimos todas as S-1010 → eSocial recalcula automaticamente o S-1210
- Mais simples, menos risco

### Cenário B: Retificação explícita do S-1210

- Construir pipeline de retificação do S-1210 no Easy e-Social
- Testar em empresa piloto (1 mês, empresa pequena)
- Validar que o S-1200 não é afetado
- Escalar para jan/fev retroativo
- Escalar para toda a base

### Cenário C: Retroativo não é possível pelo GI

- Correção do mês atual para frente
- Retificação manual mês a mês dos períodos anteriores
- Maior esforço, possível automação via Easy e-Social

---

## Regras Invioláveis

1. **NÃO MEXER NO S-1200** — É domínio da Doutora Cynthia com o Sandro. Valores de INSS já fechados não podem ser alterados.
2. **Testar antes em empresa piloto** — Nunca aplicar diretamente nos 16-20 mil funcionários.
3. **Verbas 566 e 47 são o ponto de partida** — Se essas duas funcionarem, temos o caminho para o resto.
4. **Não prometer "um botão resolve tudo"** — É um processo que precisa de validação técnica.

---

## Eventos eSocial — Referência Rápida

| Evento | Nome               | Responsável           | Ação                                  |
| ------ | ------------------ | --------------------- | ------------------------------------- |
| S-1000 | Empregador         | —                     | Dados da empresa (iniValid vem daqui) |
| S-1010 | Tabela de Rubricas | Easy e-Social           | ✅ Corrigir natureza + incidências    |
| S-1200 | Remuneração (INSS) | Dra. Cynthia / Sandro | ❌ NÃO MEXER                          |
| S-1210 | Pagamentos (IR)    | Ana / Easy e-Social     | 🎯 Retificar (pendente resposta)      |

---

## Verbas Prioritárias

| Verba                      | Descrição       | Prioridade | Certeza                                         |
| -------------------------- | --------------- | ---------- | ----------------------------------------------- |
| 566                        | Desconto INSS   | 🔴 Máxima  | "Completa certeza que precisa ser mexida"       |
| 47                         | (a identificar) | 🟡 Alta    | "Não subiu errada, mas não completamente certa" |
| Indenizatórias de rescisão | Várias verbas   | 🟡 Alta    | Zeradas no eSocial                              |


