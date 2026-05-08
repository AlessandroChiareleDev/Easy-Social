# Easy e-Social

---

## 📊 LEITURA DO DASHBOARD S-1210 ANUAL (2026-05-06)

O painel S-1210 ANUAL separa o escopo total em 4 cards. Para a APPA hoje:

```
Total escopo:  110.651
  ├─ OK:          105.768   (4.619 deles N/A real)
  ├─ Erro:            107
  └─ Pendente:        157   ← ATENÇÃO: NÃO é erro do eSocial
```

**O que é "Pendente: 157":** são CPFs marcados no DB com `status='na'` + `codigo_resposta='MOVIDO_L3'` (descrição "Movido para Lote 3 - aguarda correção rubricas"). Estão aguardando a Ana corrigir rubricas no Domínio antes de reprocessar como Lote 3 — **não é falha técnica, é workflow contábil**.

**Auditoria de recibos** (script `python-scripts/_audit_status_correto.py`):

- Dos 105.768 OK, 105.093 (99,36%) têm `nr_recibo_novo` salvo
- 675 OK estão sem recibo gravado (parse falhou na resposta) — concentrados em mai/2025 L2 a dez/2025 L2
- Maiores buracos: set/2025 L1 (189), jun/2025 L2 (172), ago/2025 L1 (65), dez/2025 L1 (64)

**IMPORTANTE — diferença entre tabelas:**

- `s1210_cpf_envios` é LOG (1 linha por POST) → 218.953 linhas para APPA, com retentativas/chain walk
- `s1210_cpf_scope` é a lista mestre única (1 linha por CPF+período) → 110.651 (= total escopo do painel)
- Sempre auditar com `DISTINCT ON (cpf, per_apur) ORDER BY enviado_em DESC` para pegar o último estado real

---

## 🔴 ERROS PENDENTES HOJE (107 CPFs — verificado 2026-05-06)

- **jan/2025 L1: 10 CPFs em erro** (último envio = `status='erro'`)
- **set/2025 L2: 97 CPFs em erro**
- Demais meses (fev/mar/abr/mai/jun/jul/ago/out/nov/dez 2025): zero erro pendente

---

## 🟡 PENDÊNCIA — SYNC RECIBOS jun/2025 L2 plansaude (2026-05-05)

**163 retificações S-1210 plansaude jun/2025 L2 enviadas em PROD (todas cod=201 aceito).**

- Marcadas `status='ok'` no DB com flag `RECIBO_PENDENTE_SYNC|jun L2 plansaude` em `descricao_resposta`
- `nr_recibo_novo` está NULL — não foi consultado para não esgotar cota diária do eSocial
- Validado em 2026-05-06: ainda 163 com flag, 172 OK total sem recibo em jun/2025 L2
- Após fechamento do mês, rodar para popular recibos:
  ```sql
  SELECT cpf, protocolo FROM s1210_cpf_envios
  WHERE descricao_resposta LIKE 'RECIBO_PENDENTE_SYNC%' AND nr_recibo_novo IS NULL;
  ```
- Loop: para cada protocolo, GET `/api/esocial/consultar/{proto}?ambiente=1` e UPDATE `nr_recibo_novo`
- Arquivos: `python-scripts/saida_plansaude_jun_l2.json` (envios), `_marca_ok_jun_l2.py`, `_flag_recibo_pendente.py`

### ✅ 42 CPFs erro jun/2025 L2 — RESOLVIDO (2026-05-06)

Os 42 CPFs com erro 401/459 ("recibo entregue inválido / retificado") em jun/2025 L2 não existem mais. Auditoria do dia 2026-05-06 confirma **zero erro pendente em jun/2025 L2**.

---

## �🚨🔴 ALERTA CRÍTICO — XMLs DE RETORNO PERDIDOS (2026-04-25)

**LEIA ANTES DE RODAR QUALQUER ENVIO:** [ALERTA_CRITICO_XMLS_RETORNO_PERDIDOS.md](ALERTA_CRITICO_XMLS_RETORNO_PERDIDOS.md)

Resumo: todos os envios S-1210 até hoje (Fev–Out/2025) foram processados, mas o backend NÃO salvou os XMLs de retorno em disco — só os campos parseados no banco. **Ana precisa dos XMLs.** A partir do **L1 Novembro/2025** todo envio DEVE capturar os XMLs em `ARQUIVOS_RETORNO/<YYYY-MM>/`. Detalhes, plano de recuperação e patches no arquivo acima.

---

## ✅ MISSÃO S-1210 APPA fev/mar/abr 2025 — CONCLUÍDA (2026-05-06)

A missão dos 3 meses (fev/mar/abr 2025) está **fechada**. Auditoria 06/05 mostra zero erro pendente nesses períodos:

```
2025-02 → todos OK ou N/A (8 lotes, ~11 mil CPFs)
2025-03 → todos OK ou N/A (8 lotes, ~11 mil CPFs)
2025-04 → todos OK ou N/A (8 lotes, ~10 mil CPFs)
```

Documentação histórica da missão (manter para auditoria, regras ainda valem para qualquer envio S-1210 futuro): [docs/MISSAO_S1210_APPA_21-04-2026/LEIA_PRIMEIRO.md](docs/MISSAO_S1210_APPA_21-04-2026/LEIA_PRIMEIRO.md)

**Regra nº 1 permanente:** NUNCA usar `explorador_eventos` como fonte de escopo. Escopo vem do XLSX da Ana.

---

## Backup Operacional (Lote 1 Pre-envio)

Existe um backup operacional de estado 0 (pre-envio) separado por mes para o Lote 1.

- Documentacao do backup: [docs/backup_preenvio_lote1/README.md](docs/backup_preenvio_lote1/README.md)
- Pasta dos artefatos versionados: [docs/backup_preenvio_lote1](docs/backup_preenvio_lote1)

Esse backup serve para auditoria, rastreabilidade e rollback operacional antes de qualquer envio.

### Developed By Xandao

Sistema focado em eSocial e suas tabelas. Recebe o arquivo **Relatório DIRF.xlsx** (bíblia do sistema), divide em 6 tabelas normalizadas e disponibiliza para processamento, validação e integração com o portal eSocial.

## Stack

| Camada   | Tecnologia                               |
| -------- | ---------------------------------------- |
| Frontend | Vue 3 + TypeScript + Tailwind CSS (Vite) |
| Backend  | Node.js + Express + TypeScript           |
| Scripts  | Python + FastAPI + Pandas                |
| Banco    | PostgreSQL 16                            |

## Estrutura

```
easy-esocial/
├── backend/       → API Node.js/TS (porta 3000)
├── frontend/      → Vue 3 SPA (porta 5173)
├── python-scripts/ → FastAPI + processamento DIRF (porta 8000)
└── .env           → Variáveis de ambiente
```

## 6 Tabelas do DIRF

1. ANALISE NATUREZA
2. Dinamica
3. Base Ficha Financeira 2025
4. Planilha 1
5. Tabela Eventos Gl
6. Tabela EB

## Início Rápido

```bash
# Backend
cd backend && npm install && npm run dev

# Frontend
cd frontend && npm install && npm run dev

# Python
cd python-scripts && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt
python src/main.py
```
