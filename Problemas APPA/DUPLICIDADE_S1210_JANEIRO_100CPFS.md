# PROBLEMA: Duplicidade S-1210 Janeiro — 100 CPFs (Erro [106])

**Data descoberta:** 15-16/04/2026  
**Status:** BLOQUEADO (precisa download dez/2024) 🔴  
**Impacto:** 100 CPFs com S-1210 duplicado  
**Período afetado:** Janeiro/2025

---

## Descrição

100 CPFs estão com erro [106] (duplicidade) no S-1210 de janeiro/2025. Isso significa que já existe um S-1210 aceito no eSocial para esses CPFs nesse período, e o sistema tentou enviar outro.

---

## Causa Provável

Os S-1210 originais de dezembro/2024 podem estar interferindo — possivelmente o `perRef` se sobrepõe entre dezembro e janeiro.

---

## Investigação Necessária

- [ ] Baixar/analisar ZIPs de dezembro/2024
- [ ] Verificar se há S-1210 com `perRef=2024-12` que conflitam
- [ ] Identificar recibos originais para retificação correta

---

## Bloqueador

Precisa do download de dezembro/2024 para investigar. ZIPs disponíveis:
- `Janeiro 2025 ou dezembro sei la voce vai ter q ver qual mes e.zip` (596MB) — possivelmente dez/2024
- `29692114.zip` (596MB) — confirmado como dez/2024

---

## Fonte

- CONCLUSOES_15-04-2026.md
- MISSAO.md (seção M4)
