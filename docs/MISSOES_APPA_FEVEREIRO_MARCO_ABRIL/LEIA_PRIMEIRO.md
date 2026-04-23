# ⛔ LEIA ANTES DE QUALQUER COISA — MISSÃO S-1210 APPA

**Data de abertura:** 21/04/2026
**Status:** ATIVA

---

## 🚫 REGRAS INEGOCIÁVEIS (agente: memorize)

1. **NUNCA usar `explorador_eventos` como fonte de escopo.**
   Essa tabela é só auditoria de XMLs baixados manualmente. Não sabe de lote, plano, operadora.
   Se você (agente) está prestes a escrever `FROM explorador_eventos` pra descobrir quem enviar — **PARE**.

2. **NUNCA enviar pro eSocial sem OK explícito do usuário.** Limite 10 consultas/dia no Download Cirúrgico.

3. **NUNCA escrever nem enviar S-1200.** Só S-1210 (e depois fechamento/reabertura quando o usuário pedir).

4. **Fonte ÚNICA de escopo = XLSX da Ana** (`02. Fevereiro_2025_APPA certa.xlsx`, `03. Marco_2025_APPA.xlsx`, `04. Abril_2025_APPA.xlsx`), aba **`Geral para envio de lotes`** (scope) + **`Operadoras`** (apenas pra lotes 2 e 3).

5. **Totais esperados do Lote 1** (validação do parser):
   - Fev/2025: **9.472** CPFs
   - Mar/2025: **8.165** CPFs
   - Abr/2025: **7.142** CPFs

6. **Vocabulário da missão (usar SEMPRE):** `lote 1/2/3/4`, `planSaude sim/não`, `operadora 774/775/522`, `ja_feito`/`pendente`/`erro`.
   Vocabulário proibido (pipeline antigo): `encontrado`, `duplicidade ok`, `bug 106`, `_is_duplicate_ok`, `explorador_eventos`.

7. **4 lotes** (do transcript da call):
   - **Lote 1**: CPFs **sem** planSaude.
   - **Lote 2**: planSaude com operadora **775 (odonto) coletivo empresarial**; 774/522 **não** coletivo empresarial.
   - **Lote 3**: **inverso** do 2 — 774 é coletivo empresarial; 775/522 não.
   - **Lote 4**: 3 pessoas manuais, sem planSaude.

---

## 📚 Arquivos desta pasta

- [STATUS_LOTE1_22-04-2026.md](STATUS_LOTE1_22-04-2026.md) — **STATUS ATUAL** — Lote 1 (3 meses) fechado a 89 % OK; breakdown dos 2.733 erros (buscar_recibo / pensão / recibo stale / planSaude) + plano de resolução
- [FONTES_MISSAO.md](FONTES_MISSAO.md) — **LER PRIMEIRO** — as 2 fontes legítimas (3 XLSX + 3 ZIPs), localização, como ler cada uma, regras dos 4 lotes
- [NORTE_S1210.md](NORTE_S1210.md) — 2 vertentes, 4 lotes × 3 meses, terminal, pausar/retomar
- [MISSAO_VISUALIZACAO_COMPLETA_21-04-2026.md](MISSAO_VISUALIZACAO_COMPLETA_21-04-2026.md) — **próxima construção** — spec das 2 vertentes (Por Lote + Mensal), drill-down até lista de CPFs com ações (ver/baixar XML, reenviar), XLSX persistido no sistema
- [RESOLUCAO_S1210_3_MESES.md](RESOLUCAO_S1210_3_MESES.md) — **A BÍBLIA** — 12 porcarias, missão real, transcrição da call, parser rules (nome antigo: `RESOLUCAO_S1200_3_MESES.md` — estava errado, S-1200 nunca deve ser tocado)
- [INVESTIGACAO_ENVIOS.md](INVESTIGACAO_ENVIOS.md) — resultado da investigação: nada do mega lote passou (0 recibos em fev/mar/abr)
- [TAREFAS.md](TAREFAS.md) — checklist da execução atual (vai sendo atualizado)

---

## 🧠 Por que eu (agente) errei antes

Meu reflexo: ver `explorador_eventos` no schema → usar como escopo. É ATALHO PREGUIÇOSO.
O escopo **real** está nos XLSX da Ana, que é externo ao repo. Só existe quando o usuário faz upload pela tela.

**Antídoto:** sempre que eu pensar "de onde vêm os CPFs da missão?" — resposta única: **do upload do XLSX do usuário na tela**.
