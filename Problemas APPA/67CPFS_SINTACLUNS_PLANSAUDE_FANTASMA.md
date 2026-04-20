# PROBLEMA: 67 CPFs SINTACLUNS — planSaude Fantasma

**Data descoberta:** 17/04/2026  
**Status:** DECISÃO PENDENTE 🟡  
**Impacto:** 67 CPFs com planSaude indevido no eSocial  
**Operadora:** SINTACLUNS (CNPJ 05597049000197, CodANS 415260)

---

## Descrição

67 CPFs receberam bloco `<planSaude>` com dados da SINTACLUNS no S-1210, mas **NUNCA tiveram planSaude** nos XMLs originais.

---

## Investigação Completa

| Fonte Verificada | Tem SINTACLUNS/planSaude? |
|------------------|--------------------------|
| ZIP jan2025 (141k XMLs) | **NÃO** |
| ZIP dez2024 (153k XMLs) | **NÃO** |
| ZIP 29692114 (153k XMLs) | **NÃO** |
| Explorador DB — S-1210 original | **NÃO** |
| Planilha "caso final" (1801 linhas) | **ZERO** SINTACLUNS |
| Planilha 1600 | **NENHUM** desses CPFs |
| Planilha "certo" duplicada (6074 linhas) | **SIM** — com valores |

---

## Origem do Problema

A planilha **"S_Tabela - Financeiro - 202412 - certo.xlsx"** (6074 linhas) é uma versão DUPLICADA que contém dados SINTACLUNS que NÃO existem na planilha correta **"caso final"** (1801 linhas).

Diferença: 6074 - 1801 = **4273 linhas de duplicação**.

O pipeline leu a planilha errada e injetou planSaude inexistente nesses 67 CPFs.

---

## Distribuição dos Valores (todos múltiplos de R$22)

| Valor Total | Qtd CPFs | Composição |
|-------------|----------|------------|
| R$44,00 | 31 | 1 titular (R$22) × 2 (duplicado) |
| R$88,00 | 16 | titular + 1 dep (R$22+R$22) × 2 |
| R$132,00 | 16 | titular + 2 dep × 2 |
| R$176,00 | 3 | titular + 3 dep × 2 |
| R$220,00 | 1 | titular + 4 dep × 2 |

Eventos usados:
- **631:** Titular (R$22,00 = 2200 centavos)
- **638:** Dependente (R$22,00 cada)

---

## 5 CPFs Testados em Detalhe

| CPF | Valor Dobrado | Originais (3 ZIPs) | DB Explorador |
|-----|--------------|---------------------|---------------|
| 02224718756 | R$44,00 | SEM planSaude | SEM planSaude |
| 00325551723 | R$88,00 | SEM planSaude | SEM planSaude |
| 01794034781 | R$132,00 | SEM planSaude | SEM planSaude |
| 01267009748 | R$176,00 | SEM planSaude | SEM planSaude |
| 13948026769 | R$220,00 | SEM planSaude | SEM planSaude |

---

## Ação Necessária

**REMOVER planSaude** inteiramente desses 67 CPFs (enviar S-1210 retificação SEM o bloco planSaude).

### Arquivo com todos os 67 CPFs:
`C:\tmp\fora_1600_67cpfs.json`

---

## Fonte

- Investigação de 17/04/2026
- Scripts: `buscar_zips_sintacluns.py`, `investigar_67cpfs_v3.py`, `verificar_caso_final.py`
