# PROBLEMA: Recibos Não Encontrados — Janeiro (~94 CPFs)

**Data descoberta:** 16/04/2026  
**Status:** EM ANDAMENTO (coleta manual) 🟡  
**Impacto:** ~94 CPFs sem recibos corretos para retificação  
**Período afetado:** Janeiro/2025

---

## Descrição

~160 CPFs de janeiro não tinham recibos corretos (GI desatualizado). Sem o recibo correto, não é possível enviar retificação (indRetif=2) ao eSocial.

---

## Método de Coleta

### Tentativa 1: Script automático (50 CPFs por vez)
- Xande desenvolveu script para consultar 50 CPFs de uma vez
- **Problema:** IA queimou as 10 consultas diárias antes de testar
- **Problema 2:** Reset diário não é à meia-noite, é às 6h da manhã

### Tentativa 2: Coleta manual
- Ana e Xande coletando recibos manualmente pelo portal eSocial
- Ana de cima para baixo, Xande de baixo para cima
- ~3 recibos por operação (lento)

---

## Progresso

| Etapa | Quantidade |
|-------|-----------|
| Total inicial | ~160 CPFs |
| Coletados | ~66 |
| **Restantes** | **~94** |

---

## Bloqueador

eSocial caiu com **erro 502** (Bad Gateway) durante a coleta, pausando o trabalho.

---

## Plano

- Continuar coleta manual quando eSocial voltar
- Possível uso do certificado Cintia APA para ganhar +10 consultas/dia
- Script de 50 em 50 pronto para testar quando houver consultas disponíveis

---

## Fonte

- CALL_2_ANA, CALL_3_ANA (16/04/2026)
