# Grupos/Lotes de Envio do S-1210 — Easy e-Social

## Resumo dos 4 Lotes

1. **Lote 1 — Sem plano de saúde**
   - CPFs sem operadora identificada.
   - S-1210 enviado **sem** bloco `<planSaude>`, apenas ajustes de IR/detPgtos conforme o original.

2. **Lote 2 — Plano de saúde (grupo A)**
   - CPFs com titular + operadora identificados.
   - Rubricas de saúde (516, 605, 607, 619, 631, 638, 774, 775) **já configuradas corretamente** no eSocial.
   - S-1210 gera `<planSaude>` agregando valores por CNPJ de operadora.

3. **Lote 3 — Plano de saúde (grupo B)**
   - Estruturalmente igual ao lote 2.
   - **Bloqueado**: Rubricas 774, 775 e 522 **ainda não estão com a natureza correta** no eSocial (ex: 774 deveria ser 9219, 775 deveria ser “outros descontos”, 522 deveria ser plano coletivo empresarial).
   - Para liberar o lote 3, é necessário:
     - Reclassificar as rubricas no S-1010 do eSocial para as naturezas corretas.
     - Garantir que as rubricas estejam parametrizadas como plano coletivo empresarial.
     - Após a reclassificação, o sistema poderá gerar `<planSaude>` corretamente para esses CPFs.

4. **Lote 4 — Casos manuais/especiais**
   - Situações que exigem tratamento individual (divergências, CPFs em blocklist, etc).

---

## O que precisa ser feito para liberar o Lote 3

- **Reclassificação das Rubricas no eSocial:**
  - Rubrica 774: Atualizar natureza para 9219 (Assistência médica).
  - Rubrica 775: Corrigir para natureza de saúde ou “outros descontos” conforme orientação.
  - Rubrica 522: Garantir que esteja como plano coletivo empresarial.
- **Atualizar S-1010:** Enviar eventos S-1010 retificando as rubricas para as naturezas corretas.
- **Homologação:** Validar no ambiente de homologação se o eSocial aceita as novas naturezas e permite geração do bloco `<planSaude>` para esses CPFs.
- **Só após essas mudanças o lote 3 poderá ser processado normalmente pelo pipeline.**

---

## Referências e Evidências

- O sistema só gera `<planSaude>` para rubricas corretamente classificadas como plano coletivo empresarial.
- FAQ 14.4 do eSocial: plano por adesão via sindicato **não** deve ter `<planSaude>`.
- Histórico mostra que Bahia nunca incluiu `<planSaude>` para 774/775, apenas para 607 (operadora direta).
- Toda a lógica do pipeline depende da correta classificação das rubricas no S-1010.

---

# Easy e-Social — Análise Conclusiva (23/04/2026)

## Visão Geral e Propósito

O **Easy e-Social** é um sistema web multi-tenant criado para gestão, validação e correção de rubricas do eSocial, com foco em corrigir divergências de incidência tributária (INSS, IRRF, FGTS) em grandes bases de folha de pagamento. O sistema surgiu para resolver problemas críticos após a extinção da DIRF em 2025, que transferiu toda a responsabilidade de parametrização tributária para o eSocial, afetando milhares de trabalhadores e empresas (ex: APPA, Objetiva).

O objetivo central é identificar, corrigir e enviar eventos S-1010 (Tabela de Rubricas) ao eSocial, garantindo conformidade tributária e eliminando bloqueios operacionais causados por múltiplos sistemas legados e falta de colaboração entre equipes.

---

## Contexto de Negócio

- **Problema-raiz:** Rubricas parametrizadas incorretamente (ex: codIncIRRF=11 ao invés de 41) resultavam em deduções zeradas no IR de milhares de funcionários.
- **Impacto:** Comprometimento de DIRF, bloqueios em sistemas legados (GI, Sandro), e necessidade de retificação massiva de eventos no eSocial.
- **Escopo:** Correção de até 20.000 trabalhadores, 18 meses de folha, potencial de 360.000 eventos retificados.

---

## Arquitetura e Tecnologias

### Stack Tecnológica

| Camada   | Tecnologia                                 |
| -------- | ------------------------------------------ |
| Frontend | Vue 3 + Vite + TypeScript + Tailwind CSS 4 |
| Backend  | Node.js + Express 5 + TypeScript           |
| Scripts  | Python + FastAPI + Pandas                  |
| Banco    | PostgreSQL 16                              |

- **Design:** Dark theme glassmorphism (#0A1024, #0066FF)
- **Infraestrutura:** Multi-tenant, autenticação JWT, uploads massivos, integração com certificados A1.

### Estrutura Modular

- **Backend Node.js:** API REST para autenticação, upload, CRUD tabelas, validação e orquestração.
- **Frontend Vue:** SPA para visualização, validação, confirmação e acompanhamento de correções.
- **Python FastAPI:** Núcleo de integração com o webservice do eSocial (S-1010), assinatura digital, envio e consulta de eventos.
- **Bot PyAutoGUI:** (Pausado) Automação de correções via interface web do eSocial.
- **Banco de Dados:** Tabelas normalizadas para análise, staging, auditoria, histórico de envios e gestão de certificados.

---

## Fluxos e Componentes Principais

### Pipeline de Correção

1. **Upload DIRF.xlsx:** Importação de dados de rubricas.
2. **Análise e Cruzamento:** Detecção automática de divergências entre tabelas internas e oficiais do eSocial.
3. **Validação de Naturezas:** IA + sugestões humanas para corrigir naturezas e incidências.
4. **Confirmação e Staging:** Usuário revisa e confirma correções.
5. **Envio ao eSocial:** Geração, assinatura e envio de eventos S-1010 via webservice (em homologação).
6. **Retificação em Massa:** Pipeline automatizado para S-1298, S-1200, S-1210, S-1299 por CPF × mês.
7. **Validação Final:** Conferência de totalizadores (S-5001, S-5002, S-5012) e integração com DCTFWeb.

### Integrações

- **eSocial Web Service (SERPRO):** Envio de eventos S-1010, consulta de protocolos, assinatura digital com certificado A1.
- **Banco PostgreSQL:** Persistência de dados, staging, auditoria, histórico de envios e certificados.
- **APIs Internas:** Comunicação entre frontend, backend Node.js e FastAPI Python.

---

## Pontos Fortes

- **Automação Completa:** Pipeline de ingestão, análise, correção e envio massivo de eventos.
- **Arquitetura Modular:** Separação clara de responsabilidades entre frontend, backend e scripts Python.
- **Rastreabilidade:** Auditoria detalhada, backups operacionais, logs de todas as etapas.
- **Escalabilidade:** Suporte a grandes volumes de dados e múltiplos clientes (multi-tenant).
- **Conformidade Legal:** Alinhamento com as regras e tabelas oficiais do eSocial (S-1.3).

---

## Desafios e Limitações

- **Integração Produção:** Atualmente opera apenas em homologação (tpAmb=2). Envio em produção requer ajustes e validações adicionais.
- **Dependência de Certificados:** Gestão segura de certificados A1 é crítica e sensível.
- **Complexidade dos Pipelines:** Retificações em massa exigem controle rigoroso de ordem e dependências entre eventos.
- **Bot RPA:** Solução via automação de interface é frágil e foi preterida pelo webservice.
- **Parser XML Massivo:** Falta parser robusto para leitura e cruzamento de grandes volumes de XMLs baixados do eSocial.

---

## Recomendações

1. **Finalizar Integração Webservice:** Priorizar implementação e testes do pipeline completo de envio S-1010, S-1298, S-1200, S-1210, S-1299 via FastAPI.
2. **Expandir Parser XML:** Construir parser massivo para ingestão e análise de XMLs baixados, cruzando recibos GI × eSocial.
3. **Segurança:** Fortalecer criptografia e gestão de certificados, com rotação e armazenamento seguro.
4. **Monitoramento e Alertas:** Implementar dashboards de progresso, alertas de falha e relatórios automáticos.
5. **Documentação e Treinamento:** Manter documentação atualizada e promover treinamentos para usuários finais e equipe técnica.
6. **Planejar Migração para Produção:** Mapear requisitos e riscos para transição segura do ambiente de homologação para produção.

---

## Conclusão

O Easy e-Social é uma solução robusta e inovadora para gestão e correção de rubricas do eSocial, atacando um problema real e urgente do setor de folha de pagamento pós-extinção da DIRF. Sua arquitetura modular, automação de fluxos e foco em conformidade o tornam referência para projetos similares. O sucesso pleno depende da finalização dos módulos de integração, parser XML e migração para produção, além de contínua atenção à segurança e rastreabilidade.

---

**(FIM DO RELATÓRIO)**
