# Easy e-Social — Missão Atual

## Status Geral

| Missão                                      | Status                             |
| ------------------------------------------- | ---------------------------------- |
| Upload e processamento DIRF.xlsx            | ✅ Concluído                       |
| 4 tabelas no banco (PostgreSQL)             | ✅ Concluído                       |
| Detecção de divergências (Ponto 1)          | ✅ 385 divergências detectadas     |
| Frontend reconstruído (Painel/Tabelas/Robô) | ✅ Concluído                       |
| Bot eSocial — calibração e automação        | ⏸️ PAUSADO                         |
| **Missão atual**                            | 🔴 Pendente (aguardando definição) |

---

## ⏸️ Robô eSocial — PAUSADO

O bot está 90% pronto. Falta apenas calibrar e rodar.

**O que já foi feito:**

- `python-scripts/bot_esocial.py` — Bot completo com PyAutoGUI
- `python-scripts/bot_api.py` — API FastAPI de controle (porta 8000)
- Frontend `BotView.vue` — Painel com start/stop/log/progresso
- Modo de calibração (`--calibrate`) — 7 pontos via F2
- Fluxo: buscar rubrica → Alterar → mudar dropdowns INSS/IRRF/FGTS → salvar → voltar
- 385 rubricas pendentes na tabela `rubrica_corrections`

**Para retomar:**

1. Logar no eSocial com certificado
2. Ir em Tabela de Rubricas e pesquisar qualquer rubrica
3. Rodar: `cd python-scripts && .\venv\Scripts\activate && python bot_esocial.py --calibrate`
4. Iniciar pelo frontend (`/bot`) ou `python bot_esocial.py --run`

---

## 🔴 Missão Atual — Módulo Validador de Naturezas + Normalização

### Fluxo Completo do Sistema (entendimento profundo)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UPLOAD DIRF.xlsx                                  │
│         Popula 4 tabelas + naturezas_esocial (206 do governo)       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              TABELAS DE DADOS (estado atual)                        │
│                                                                     │
│  analise_natureza (455 registros) — TABELA PRINCIPAL                │
│    col_a = CódigoEvento (ex: 13)                                    │
│    col_b = NomeEvento (ex: REEMB. VALE TRANSPORTE)                  │
│    col_c = Natureza eSocial atual (ex: 1629-Ressarcimento...)       │
│    col_d = Status: OK (360) ou VERIFICAR (91) ← PRECISA TRIM!      │
│    col_e = Observação (inconsistência INSS/IRRF/FGTS)              │
│    col_f = SUGESTÃO DE NATUREZA! (75 de 91 VERIFICAR já têm!) ←OURO│
│    → 91 rubricas com natureza errada/duvidosa                       │
│    → NÃO PRECISA da tabela dinamica (col_f idêntica aqui)          │
│                                                                     │
│  tabela_eb (1224 registros) — TABELA DE INCIDÊNCIAS (EB)            │
│    col_a = CódigoEvento (1056 distintos, 191 são sub-linhas)        │
│    col_b = NomeRubrica                                              │
│    col_c = Natureza atribuída (formato "XXXX - Nome")               │
│    col_d/e/f = Códigos incidência (INSS/IRRF/FGTS esperados)       │
│    col_h/i/j = Incidência real no eSocial (com fundamentação)       │
│    → D vs H, E vs I, F vs J = Ponto 1 (385 divergências)           │
│                                                                     │
│  naturezas_esocial (206 registros) — TABELA GOVERNO                 │
│    codigo, nome, descricao, data_inicio, data_fim                   │
│    → Referência oficial do que é válido/vigente                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
┌──────────────────────┐         ┌──────────────────┐
│ RELAÇÃO:             │         │ RELAÇÃO:         │
│ AN.col_a = EB.col_a  │         │ AN.col_c código  │
│ (447 match)          │         │ = naturezas_     │
│                      │         │ esocial.codigo   │
└──────────┬───────────┘         └────────┬─────────┘
           │                              │
           └──────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PASSO 1: VALIDADOR DE NATUREZAS (ATUAL)                │
│                                                                     │
│  Para cada rubrica VERIFICAR (91 em analise_natureza):              │
│                                                                     │
│  1. PRIMEIRO: Verificar se analise_natureza.col_f tem sugestão     │
│     → 75 de 91 VERIFICAR já têm sugestão humana na col_f!          │
│     → Mostrar essa sugestão em DESTAQUE CHAMATIVO no topo           │
│                                                                     │
│  2. SEGUNDO: Buscar por score (algoritmo de matching)               │
│     → Até 15 naturezas com score > 0                                │
│                                                                     │
│  3. TERCEIRO: Completar até 30 com as mais comuns                   │
│     → TOP naturezas que já aparecem nos registros OK                │
│     → As 30 mais frequentes: 1003(48x), 1205(31x), 1000(23x)...   │
│                                                                     │
│  4. Usuário escolhe a natureza correta → salva                      │
│  5. Quando TODAS as 91 estiverem corrigidas → passo 2               │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│           PASSO 2: NORMALIZAR TABELA_EB (FUTURO)                    │
│                                                                     │
│  Com naturezas corretas em analise_natureza:                        │
│  - Atualizar tabela_eb.col_c com a natureza corrigida              │
│  - Recalcular col_d/e/f (incidências esperadas pela natureza)      │
│  - Re-comparar com col_h/i/j (incidências reais)                   │
│  - Gerar NOVA lista de divergências (pode mudar os 385)             │
│  - tabela_eb fica NORMALIZADA                                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│           PASSO 3: BOT eSocial (SÓ DEPOIS DE NORMALIZAR)           │
│                                                                     │
│  Bot SÓ pode agir com tabela_eb normalizada porque:                 │
│  - Ele busca cada rubrica por código no eSocial                     │
│  - Compara os 3 parâmetros (INSS/IRRF/FGTS)                        │
│  - Muda os que estão divergentes (D≠H, E≠I, F≠J)                   │
│  - Se a natureza estiver errada, os parâmetros esperados            │
│    (D/E/F) estão errados → bot mudaria pra coisa errada!            │
│                                                                     │
│  BLOQUEIO: Bot não roda até passo 2 estar completo ✋               │
└─────────────────────────────────────────────────────────────────────┘
```

### Observações da analise_natureza (col_e) — Tipos encontrados

| Observação                                        | Qtd VERIFICAR | Qtd OK | Significado                  |
| ------------------------------------------------- | ------------- | ------ | ---------------------------- |
| `-` (sem obs)                                     | 46            | 257    | Sem problema adicional       |
| `Rubrica com inconsistência de IRRF`              | 27            | 89     | Parâmetro IRRF errado na EB  |
| `Rubrica com inconsistência de INSS, IRRF e FGTS` | 9             | 8      | Todos 3 parâmetros errados   |
| `Natureza da Rubrica sujerida - XXXX ...`         | 6             | 0      | Sugestão já definida (na AN) |
| `Rubrica com inconsistência de INSS e IRRF`       | 1             | 1      | 2 parâmetros errados         |
| `None` (null)                                     | 2             | 0      | Sem dado                     |

### Sugestões na analise_natureza.col_f — PRÉ-EXISTENTES

75 de 91 VERIFICAR na `analise_natureza` **já têm sugestão de natureza na col_f!**  
(A tabela `dinamica` tem os mesmos dados — não precisa ser consultada)

Exemplos:

- cod 13 REEMB. VALE TRANSPORTE → `"Natureza da Rubrica sugerida - 1810 Transporte"`
- cod 35 DIF. D.S.R. → `"Natureza sugerida 1020, pois o 1002 foi inativado em 30.04.2024"`
- cod 135 D.S.R. S/HORA EXTRA → `"1012 - Descanso semanal remunerado - DSR e feriado"`
- cod 19 REEMB. EXAME ADMISSIONAL → `"Natureza 1299 encerrada - sujerida 1629"`

### Naturezas mais comuns nos registros OK (para fallback)

| Código | Nome                               | Frequência |
| ------ | ---------------------------------- | ---------- |
| 1003   | Horas extraordinárias              | 48x        |
| 1205   | Adicional noturno                  | 31x        |
| 1000   | Salário, vencimento, soldo         | 23x        |
| 1211   | Gratificações                      | 16x        |
| 1806   | Alimentação ticket/cartão PAT      | 14x        |
| 9299   | Outros descontos                   | 12x        |
| 1202   | Adicional de insalubridade         | 10x        |
| 9243   | Cesta básica/refeição PAT - Desc   | 10x        |
| 9253   | Empréstimos eConsignado - Desc     | 10x        |
| 9232   | Contribuição Sindical Assistencial | 10x        |

---

## Infraestrutura

| Serviço         | Porta | Comando                                                             |
| --------------- | ----- | ------------------------------------------------------------------- |
| Backend Node.js | 3333  | `cd backend && npm run dev`                                         |
| Frontend Vue 3  | 5173  | `cd frontend && npm run dev`                                        |
| Bot API Python  | 8000  | `cd python-scripts && .\venv\Scripts\activate && python bot_api.py` |
| PostgreSQL      | 5432  | `easy_social_db` / `easy_social_user`                               |
