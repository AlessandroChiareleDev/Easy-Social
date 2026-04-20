# PROBLEMA: eSocial — Instabilidade do Portal (502)

**Data ocorrência:** 16/04/2026  
**Status:** INTERMITENTE (fora do nosso controle) ⚠️  
**Impacto:** Bloqueio de coleta de recibos e consultas

---

## Descrição

O portal do eSocial apresentou erro **502 Bad Gateway** durante a coleta manual de recibos, impedindo todo o trabalho.

---

## Incidentes Registrados

### 16/04/2026
- Ana coletando recibos manualmente → portal caiu
- ~66 recibos coletados antes do crash
- ~94 restantes ficaram bloqueados
- "Todo mundo reclamando" — problema generalizado

### 16/04/2026 (outro incidente)
- Xande não conseguiu acessar portal → erro de navegador/computador (não o portal)
- Ana confirmou que acessava normalmente da máquina dela

---

## Impacto no Fluxo

Quando o eSocial cai:
- Consultas diárias são desperdiçadas (se enviou request antes do 502)
- Coleta manual para completamente
- Pipeline de envio fica bloqueado
- Limite de 10 consultas/dia NÃO é restaurado

---

## Mitigações

1. Tentar em horários de menor uso (manhã cedo, antes das 8h)
2. Salvar progresso frequentemente
3. Ter fallback com ZIPs já baixados (não depender de consulta online)

---

## Fonte

- CALL_2_ANA, CALL_3_ANA (16/04/2026)
