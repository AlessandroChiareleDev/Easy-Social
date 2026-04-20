# PROBLEMA: planSaude Sindicato vs Empresarial (FAQ 14.4)

**Data descoberta:** 14-15/04/2026  
**Status:** ESTRATÉGIA DEFINIDA, IMPLEMENTAÇÃO PENDENTE  
**Impacto:** ~156 CPFs rejeitados pelo eSocial (erro [8])  
**Período afetado:** Janeiro/2025 em diante

---

## Descrição

O eSocial exige o bloco `<planSaude>` no S-1210 SOMENTE para **plano coletivo empresarial**. Segundo o FAQ 14.4 do eSocial:

### NÃO deve ter planSaude:
- Plano por adesão (sindicato) — mesmo que a empresa desconte em folha
- Autogestão
- Administradora de benefícios
- Plano 100% pago pela empresa

### DEVE ter planSaude:
- Plano coletivo empresarial (contratado diretamente pela empresa)

---

## Evidência

**Setembro/2025 (Bahia):** 1.014 CPFs com rubricas de saúde → ZERO planSaude incluído  
Isso sugere que rubricas 774/775 são de **sindicato** (não empresarial).

---

## Rubricas Envolvidas

| Rubrica | Nome | Natureza | Tipo |
|---------|------|----------|------|
| 607 | Desc. Assistência Médica | 9219 | Empresarial (~18 CPFs) |
| 774 | Desc. Plano de Saúde | 9219 | Sindicato? (maioria) |
| 775 | Desc. Assistência Odontológica | 9219 | Sindicato? |
| 516 | ? | 9219 | A confirmar |
| 522 | Desc. Plano Saúde | 9219 | Empresarial (751 CPFs) |

---

## O Problema Técnico

~156 CPFs têm rubrica 775/522 com natureza 9219 (exige `cnpjOper` + `regANS`), mas **NÃO têm operadora cadastrada** (é repasse ao sindicato).

### Tentativas que falharam:
1. **Enviar evento 775 sem operadora** → eSocial rejeita (erro [8]: "Plano de saúde deve ser preenchido")
2. **Mudar número do evento** para separar sindicato → eSocial bloqueia (interdependência com S-1200)

---

## Solução Aprovada

Para CPFs **sem** código de operadora → **NÃO transmitir** o bloco `<planSaude>` no S-1210:

```
Se cnpjOper != NULL → inclui bloco planSaude
Se cnpjOper == NULL → envia S-1210 SEM planSaude
```

### Distribuição:
- ~1.500 CPFs COM operadora → inclui planSaude
- ~156 CPFs SEM operadora (sindicato) → S-1210 sem planSaude
- ~9.000 CPFs SEM saúde nenhuma → S-1210 normal

---

## Confirmação Pendente

- Ana/Marcos confirmarem: rubricas 774/775 = sindicato ou empresarial?
- Giovana (Bahia) confirmar se tem valores de plano por CPF
- Dra. Cintia aprovou a estratégia na call de 15/04
