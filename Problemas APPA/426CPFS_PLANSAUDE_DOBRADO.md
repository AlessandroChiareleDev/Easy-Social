# PROBLEMA: 426 CPFs — planSaude com Valores Dobrados

**Data descoberta:** 16-17/04/2026  
**Data correção:** 17/04/2026  
**Status:** RESOLVIDO ✅  
**Impacto:** 426 CPFs com valores de planSaude dobrados no S-1210

---

## Descrição

426 CPFs tiveram os valores de `<planSaude>` **dobrados** no S-1210 retificado. A causa foi a planilha "S_Tabela - certo" que tinha linhas duplicadas.

---

## Correção

- **Script:** `C:\tmp\correcao_426_dobrado.py`
- **Fonte de verdade:** Planilha 1600 cpfs.xlsx
- **Método:** S-1210 retificação (indRetif=2) com valores corretos da Planilha 1600

### Resultado:
| Métrica | Valor |
|---------|-------|
| Total CPFs | 426 |
| OK | **426** |
| ERRO | **0** |
| Lotes enviados | 9 |

---

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `C:\tmp\correcao_426_envio.json` | 426 CPFs com valores corretos |
| `C:\tmp\correcao_426_resultados.json` | Resultados — todos OK |
| `C:\tmp\plansaude_mapa_1600.json` | Mapa correto (1429 CPFs da Planilha 1600) |

---

## Fonte

- Investigação e correção de 17/04/2026
