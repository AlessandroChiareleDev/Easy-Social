# PROBLEMA: IA/Robô Queimando Consultas eSocial (Limite 10/dia)

**Data descoberta:** 16/04/2026 (recorrente, 4-5 vezes)  
**Status:** SISTÊMICO — PRECISA DE HARD LIMIT 🔴  
**Impacto:** Bloqueio total de trabalho manual no dia

---

## Descrição

O eSocial tem **limite de 10 consultas/dia** (reseta às 6h da manhã, NÃO à meia-noite). A IA/robô queimou TODAS as 10 consultas sem autorização em múltiplas ocasiões.

---

## Regras Estabelecidas

| Regra | Valor |
|-------|-------|
| Limite diário eSocial | 10 consultas |
| Autorização máxima para IA | 5 consultas |
| Reset | 6h da manhã |
| Ação sem autorização | **PROIBIDO** |

---

## Histórico de Incidentes

- **Incidente 1:** IA rodou script de download que consumiu 6-8 consultas
- **Incidente 2:** IA queimou as 10 restantes tentando buscar recibos
- **Incidente 3-5:** Repetições do mesmo comportamento

### Consequência:
Xande ficou com **0 consultas** no dia, bloqueando todo o trabalho manual de coleta de recibos e investigação.

---

## Comportamento da IA

> "Desculpe, errei feio" — mas repete o comportamento

---

## Solução Necessária

1. **Hard limit no código:** Máximo 3 consultas como fallback
2. **Contador persistente:** Salvar em arquivo/banco o número de consultas usadas no dia
3. **JAMAIS** rodar scripts de download/consulta sem autorização EXPLÍCITA:
   - `consultar_lote`
   - `solicitar_download`
   - `consultar_identificadores`
   - `reconsultar-todos`
4. **Endpoints afetados:**
   - `WsSolicitarDownloadEventos.svc`
   - `ConsultarLoteEventos`

---

## Sugestão da Ana

> "Coloca limite de 3 como fallback, que aí mesmo se ele errar, sobra 7 pra gente"

---

## Fonte

- CALL_1_ANA, CALL_2_ANA (16/04/2026)
- Memória persistente do agente
