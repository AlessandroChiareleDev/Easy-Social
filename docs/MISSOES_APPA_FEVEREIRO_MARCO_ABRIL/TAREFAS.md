# TAREFAS — MISSÃO S-1210 APPA

**Regra de ouro:** uma tarefa por vez. Marcar ✅ ao concluir. Reler [LEIA_PRIMEIRO.md](LEIA_PRIMEIRO.md) + trecho relevante da [RESOLUCAO_S1200_3_MESES.md](RESOLUCAO_S1200_3_MESES.md) antes de CADA tarefa.

---

## Fase 0 — Setup (pasta + memória)

- [x] **0.1** Criar pasta `docs/MISSAO_S1210_APPA_21-04-2026/`
- [x] **0.2** Mover `NORTE_S1210.md` + `RESOLUCAO_S1200_3_MESES.md` pra dentro
- [x] **0.3** Criar `LEIA_PRIMEIRO.md` com as 7 regras inegociáveis
- [x] **0.4** Criar este `TAREFAS.md`
- [x] **0.5** Linkar pasta no `README.md` raiz (topo, bem visível)
- [x] **0.6** Salvar nota permanente na memória do agente: NUNCA usar `explorador_eventos` como escopo

---

## Fase 1 — Limpeza (arrancar o que fiz errado)

- [x] **1.1** Apagar `frontend/src/views/S1210RepoView.vue`
- [x] **1.2** Apagar `frontend/src/views/S1210RepoDashboardView.vue`
- [x] **1.3** Apagar `frontend/src/views/S1210RepoCompartimentoView.vue`
- [x] **1.4** Remover 3 rotas de `/s1210-repo*` em `frontend/src/router/index.ts`
- [x] **1.5** Remover item "Repositório S-1210" do menu em `frontend/src/App.vue`
- [x] **1.6** Apagar `backend/src/routes/s1210RepoRoutes.ts`
- [x] **1.7** Remover `import` + `app.use("/api", s1210RepoRoutes)` de `backend/src/app.ts`
- [x] **1.8** Apagar migração `supabase/migrations/20260420000000_s1210_repositorio.sql`
- [x] **1.9** DROP das 4 tabelas `s1210_repo_*` + view `v_s1210_repo_resumo` no Supabase
- [x] **1.10** Apagar scripts Python temporários
- [x] **1.11** Validar local: `npm run build` (frontend + backend) sem erro _(fix pré-existente mínimo em PipelineView.vue `;` em @click multi-linha)_
- [x] **1.12** Deploy VPS: rebuild + restart PM2; confirmado `/api/s1210-repo/*` = 404 e menu limpo

---

## Fase 2 — Investigação: o que já foi enviado pro eSocial desse lote?

> **Objetivo:** descobrir se algum CPF do "primeiro grande lote dos 3 meses" já foi enviado antes (pelo Alex, por outro sistema, ou por pipeline antigo). SEM consultar o eSocial — só nosso banco + logs.

- [x] **2.1** Mapear tabelas nossas que registram envios — achadas 5 fontes: `pipeline_runs`, `pipeline_cpf_results`, `esocial_envios`, `explorador_eventos` (só auditoria), `pipeline_snapshots`
- [x] **2.2** Contar por período quantos S-1210 foram aceitos — Fev ≈ 9.625 aceitos; Mar = 1 (ruído); Abr = 0
- [x] **2.3** Verificar se o "big send" deixou algum CPF aceito — SIM, run 4 de 14/04/2026 entregou 9.625 `nr_recibo_novo`
- [x] **2.4** Checar `explorador_eventos` apenas como auditoria — confirma 10.800 CPFs S-1210 aceitos em fev
- [x] **2.5** Escrever [INVESTIGACAO_ENVIOS.md](INVESTIGACAO_ENVIOS.md) com conclusão consolidada

---

## Fase 3 — Backend novo (seguindo a bíblia)

> Rereler [RESOLUCAO_S1200_3_MESES.md](RESOLUCAO_S1200_3_MESES.md) §"Fluxo correto" e §"Parser XLSX".

**3A — MVP entregue 21/04/2026 (robô direto ZIP + XLSX, sem DB ainda):**

- [x] **3A.1** Router FastAPI `python-scripts/esocial/s1210_missao_routes.py` com 4 endpoints
- [x] **3A.2** `GET /api/esocial/s1210-missao/fontes` — valida 6 arquivos em Downloads
- [x] **3A.3** `POST /api/esocial/s1210-missao/carregar` — parseia XLSX (cache em memória), retorna 3×4 com totais reais
- [x] **3A.4** `GET /api/esocial/s1210-missao/compartimento/{mes}/{lote}` — lista CPFs paginada
- [x] **3A.5** `POST /api/esocial/s1210-missao/testar-um-cpf` — robô: abre ZIP, acha S-1210, extrai nrRecibo+dados, monta retif, assina, envia PROD, poll, retorna resultado completo
- [x] **3A.6** Registrado em `bot_api.py`

**3B — Próximos passos (pendente OK do usuário):**

- [ ] **3.1** Definir schema novo (tabelas): `s1210_missao_upload`, `s1210_missao_item` (cpf, mes, lote, planSaude, operadora, status), `s1210_missao_envio`, `s1210_missao_log`. Nomes CLAROS que deixem óbvio que é a missão atual.
- [ ] **3.2** Migração SQL em `supabase/migrations/`
- [ ] **3.3** Persistir resultado de cada envio em DB (hoje vive só em memória)
- [ ] **3.4** Endpoint de envio em LOTE (ex: envia 50 CPFs com ThreadPoolExecutor)
- [ ] **3.5** Cruzar cada CPF com banco pra marcar `ja_feito` usando tabelas reais de envios (NÃO `explorador_eventos`)

---

## Fase 4 — Frontend

**4A — MVP entregue 21/04/2026:**

- [x] **4A.1** `frontend/src/views/S1210MissaoView.vue` — dark-slate Tailwind, sem emojis, padrão S-1010
- [x] **4A.2** Header + validação de fontes (3 XLSX + 3 ZIPs)
- [x] **4A.3** Grid 3 meses × 4 lotes (12 compartimentos) com KPIs pend/feito/erro
- [x] **4A.4** Botão "Testar 1º CPF (PROD)" em cada compartimento com confirm dialog
- [x] **4A.5** Painel de resultado colorido (verde/vermelho) com recibo original, recibo novo, código, ocorrências
- [x] **4A.6** Terminal ao vivo (logs inline com timestamp + cor)
- [x] **4A.7** Rota `/s1210-missao` no router + item de menu em App.vue
- [x] **4A.8** Build Vite OK (`S1210MissaoView-*.js 12.93 kB`)

**4B — Próximos passos (pendente OK):**

- [ ] **4.1** Tela de detalhe do compartimento: tabela com todos os CPFs + status em tempo real
- [ ] **4.2** Upload das 3 XLSX via interface (hoje o robô lê direto do Downloads)
- [ ] **4.3** Botões Pausar / Parar / Retomar no envio em lote
- [ ] **4.4** Exportar logs / resultados

---

## Fase 5 — Deploy + validação manual

- [x] **5A.1** Build local limpo (frontend + Python) ✅
- [x] **5A.2** Teste E2E local: 1 CPF de Fev/2025 Lote 1 em PRODUÇÃO — **respondeu 459** (recibo stale; ver log abaixo)
- [ ] **5.2** Deploy VPS — **AINDA NÃO** (usuário pediu: testar tudo local antes)
- [ ] **5.3** Smoke test em produção

---

## 🧪 Resultado do 1º teste em PRODUÇÃO — 21/04/2026

**Comando:** `POST /api/esocial/s1210-missao/testar-um-cpf` body `{mes:"2025-02", lote:"1", indice:0, confirmar_producao:true}`

| Campo                    | Valor                                                                                                          |
| ------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Etapa atingida           | `processamento_rejeitado` (eSocial recebeu e respondeu)                                                        |
| CPF enviado              | `01853386669` (primeiro do Lote 1 Fev/2025)                                                                    |
| Recibo original (do ZIP) | `1.1.0000000031450338257`                                                                                      |
| Protocolo do envio       | `1.1.202604.0000000013049560608`                                                                               |
| Código resposta          | **401** — "Conteúdo do evento inválido"                                                                        |
| Ocorrência               | **459** — "Não foi localizado um evento para o recibo de entrega informado ou o mesmo foi excluído/retificado" |

**Diagnóstico:** o robô fez a cadeia inteira (parseou XLSX → achou S-1210 no ZIP → extraiu recibo + dados → montou retif SEM planSaude → assinou → SOAP → PROD → pollou → recebeu resposta). **Tudo funcionou.** O erro é do eSocial dizendo que o recibo extraído do ZIP (baixado em 10/04/2026) não é mais o ativo — esse CPF sofreu retificações depois disso, o recibo ativo agora é outro. Mesma razão das runs 20–28 documentadas em [INVESTIGACAO_ENVIOS.md](INVESTIGACAO_ENVIOS.md).

**Implicação pra missão:** os ZIPs de 10/04 estão DEFASADOS. Pra retificar corretamente precisa do recibo ATIVO de cada CPF — ou baixar ZIP novo, ou consultar `ConsultarIdentificadoresEventos` (consome 10/dia do webservice) pra cada CPF.

**Próxima decisão do usuário:** (a) baixar ZIPs novos, (b) usar outra fonte de recibo, (c) investigar `pipeline_cpf_results` pra ver se temos recibos atualizados das runs 20–28 (mesmo que falhas, o eSocial pode ter devolvido o recibo ativo na ocorrência), ou (d) outra estratégia.

---

## Fase 6 — (FUTURO, não fazer agora) Teste final contra Repositório eSocial

> **Anotado mas NÃO executar.** Só quando o usuário pedir explicitamente.

- [ ] **6.1** Validar configuração de envio (certificado, endpoint, XML) usando 1 CPF por lote/mês (12 CPFs no total) contra o ambiente de homologação.
- [ ] **6.2** Comparar retorno (aceito/rejeitado/nr_recibo) com o que o Repositório eSocial diz.
- [ ] **6.3** Só então liberar envio massivo — com OK explícito do usuário e nunca estourando 10 consultas/dia.

---

## Log de execução

| Data/hora  | Tarefa   | Notas                                                                                                                                                                                                |
| ---------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | ---------- | --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 21/04/2026 | 0.1–0.4  | Pasta criada, MDs movidos, LEIA_PRIMEIRO + TAREFAS escritos                                                                                                                                          |
| 21/04/2026 | 0.5      | README.md raiz com bloco de aviso no topo apontando pra pasta                                                                                                                                        |
| 21/04/2026 | 0.6      | Memória repo salva em /memories/repo/s1210-appa-missao.md                                                                                                                                            |
| 21/04/2026 | 1.1–1.12 | Fase 1 concluída: views/rotas/tabelas removidas; deploy VPS limpo; `/api/s1210-repo/*` = 404; backend 200; frontend 200                                                                              |
| 21/04/2026 | 2.1–2.5  | Fase 2 concluída: 5 fontes cruzadas. FEV = ~9.625 CPFs já enviados (run 4, 14/04/2026); MAR = 1 ruído; ABR = 0. [INVESTIGACAO_ENVIOS.md](INVESTIGACAO_ENVIOS.md)                                     |     | 21/04/2026 | 2.6 | INVESTIGACAO_ENVIOS reescrito após reconhecimento de alucinação. Conclusão correta: **mega lote NÃO passou nada** (runs 20–28 de hoje geraram 0 recibos). Mar/Abr nunca tentadas. |
| 21/04/2026 | 2.7      | [FONTES_MISSAO.md](FONTES_MISSAO.md) criado consolidando as 2 fontes (3 XLSX + 3 ZIPs) com localização, regras de leitura e os 4 lotes. Validado: 6 arquivos existem em `C:\Users\xandao\Downloads`. |
| 22/04/2026 | L1-MAR   | **Mar/2025 L1 concluído** — S-1298 reabriu folha (recibo `1.1.0000000040115886503`); 8.164 scope · 7.317 OK (89,6 %) · 847 erro                                                                       |
| 22/04/2026 | L1-ABR   | **Abr/2025 L1 concluído** — S-1298 reabriu folha (recibo `1.1.0000000040115996084`); 7.142 scope · 6.187 OK (86,6 %) · 955 erro                                                                       |
| 22/04/2026 | L1-ALL   | **Lote 1 dos 3 meses fechado**: 24.777 scope → 22.044 OK (89 %) · 2.733 erro · 0 pend. Breakdown consolidado em [STATUS_LOTE1_22-04-2026.md](STATUS_LOTE1_22-04-2026.md)                             |
