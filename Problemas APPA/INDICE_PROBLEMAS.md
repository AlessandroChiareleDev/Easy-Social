# ÍNDICE DE PROBLEMAS — APPA eSocial

**Última atualização:** 17/04/2026  
**Total de problemas documentados:** 21  
**Fonte:** Calls 02/04, 14/04, 15/04, 16/04 + investigações 17/04

---

## Status Geral

| Emoji | Significado | Qtd |
|-------|------------|-----|
| ✅ | Resolvido | 5 |
| 🟡 | Em andamento / Aguardando | 5 |
| 🔴 | Bloqueado / Pendente | 7 |
| ⚠️ | Infraestrutura / Fora de controle | 3 |

---

## Problemas por Categoria

### PLANO DE SAÚDE (planSaude)
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 1 | [BUG_PLANSAUDE_VALORES_INFLADOS.md](BUG_PLANSAUDE_VALORES_INFLADOS.md) | Bug wildcard + soma dupla — 10.443 CPFs inflados | 🟡 Parcial |
| 2 | [PLANSAUDE_SINDICATO_VS_EMPRESARIAL.md](PLANSAUDE_SINDICATO_VS_EMPRESARIAL.md) | FAQ 14.4 — sindicato não deve ter planSaude | 🟡 Estratégia definida |
| 3 | [67CPFS_SINTACLUNS_PLANSAUDE_FANTASMA.md](67CPFS_SINTACLUNS_PLANSAUDE_FANTASMA.md) | 67 CPFs com planSaude que nunca existiu | 🟡 Decisão pendente |
| 4 | [426CPFS_PLANSAUDE_DOBRADO.md](426CPFS_PLANSAUDE_DOBRADO.md) | 426 CPFs dobrados, corrigidos via S-1210 retif | ✅ |

### INCIDÊNCIAS IR / RUBRICAS
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 5 | [RUBRICA_522_INCIDENCIA_IR_ERRADA.md](RUBRICA_522_INCIDENCIA_IR_ERRADA.md) | 751 CPFs, IR 09→67 | ✅ |
| 6 | [RUBRICA_566_INSS_INCIDENCIA_IR.md](RUBRICA_566_INSS_INCIDENCIA_IR.md) | INSS dedução zerada na RF (11→41) | 🔴 |
| 7 | [S1010_RUBRICAS_PENDENTES.md](S1010_RUBRICAS_PENDENTES.md) | 154 rubricas com incidências divergentes | 🟡 |
| 8 | [VERBA_47_INCOMPLETA.md](VERBA_47_INCOMPLETA.md) | Dados incompletos, afeta IR | 🔴 |

### SETEMBRO/2025
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 9 | [DEDUCAO_DEPENDENTES_SETEMBRO.md](DEDUCAO_DEPENDENTES_SETEMBRO.md) | R$739k vs R$20k — discrepância massiva | 🔴 |

### RECIBOS / S-1210
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 10 | [RECIBOS_GI_DIVERGENTES_ESOCIAL.md](RECIBOS_GI_DIVERGENTES_ESOCIAL.md) | GI tem recibos diferentes do eSocial | 🟡 |
| 11 | [DUPLICIDADE_S1210_JANEIRO_100CPFS.md](DUPLICIDADE_S1210_JANEIRO_100CPFS.md) | 100 CPFs erro [106] duplicidade | 🔴 |
| 12 | [RECIBOS_NAO_ENCONTRADOS_JANEIRO.md](RECIBOS_NAO_ENCONTRADOS_JANEIRO.md) | ~94 CPFs sem recibos para retificar | 🟡 |

### PENSÃO ALIMENTÍCIA
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 13 | [PENSAO_ALIMENTICIA_BENEFICIARIOS.md](PENSAO_ALIMENTICIA_BENEFICIARIOS.md) | 1 CPF com filho de 28 anos | 🟡 |
| 14 | [ERRO_PRECEDENCIA_PENSAO_ACORDO.md](ERRO_PRECEDENCIA_PENSAO_ACORDO.md) | 4 CPFs rejeitados por precedência | 🔴 |

### RESCISÃO
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 15 | [VERBAS_INDENIZATORIAS_RESCISAO_ZERADAS.md](VERBAS_INDENIZATORIAS_RESCISAO_ZERADAS.md) | Verbas de rescisão zeradas | 🔴 |
| 16 | [CASO_RANIERI_DEMISSAO_MATERNIDADE.md](CASO_RANIERI_DEMISSAO_MATERNIDADE.md) | Gestante com carta de demissão atrasada | ✅ |

### OPERADORA
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 17 | [OPERADORA_MUDANCA_SETEMBRO_2025.md](OPERADORA_MUDANCA_SETEMBRO_2025.md) | Troca de CNPJ/ANS em set/2025 | ✅ |

### CADASTRO
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 18 | [BEBE_DENTAL_SINDICATO.md](BEBE_DENTAL_SINDICATO.md) | Bebê dental não no sindicato | ✅ |

### INFRAESTRUTURA / OPERACIONAL
| # | Arquivo | Problema | Status |
|---|---------|----------|--------|
| 19 | [IA_QUEIMANDO_CONSULTAS_ESOCIAL.md](IA_QUEIMANDO_CONSULTAS_ESOCIAL.md) | Robô gastando 10 consultas/dia sem autorização | ⚠️ Sistêmico |
| 20 | [ESOCIAL_INSTABILIDADE_PORTAL.md](ESOCIAL_INSTABILIDADE_PORTAL.md) | Erro 502 bloqueando trabalho | ⚠️ |
| 21 | [INTERNET_LENTA_ANA.md](INTERNET_LENTA_ANA.md) | Rede lenta impedindo coleta | ⚠️ |

---

## Arquivos Pré-existentes (anteriores a esta organização)

| Arquivo | Conteúdo |
|---------|----------|
| [PROBLEMA_APPA.md](PROBLEMA_APPA.md) | Documento original de problemas |
| [MISSAO_ATUAL.md](MISSAO_ATUAL.md) | Missão e fases atuais |
| [ANALISE_MIGRACAO_SUPABASE.md](ANALISE_MIGRACAO_SUPABASE.md) | Análise migração Supabase |
| [ESTADO_POS_MERGE.md](ESTADO_POS_MERGE.md) | Estado pós-merge |
| [MERGE_TESTES.md](MERGE_TESTES.md) | Testes de merge |
| [PASSO_1_MERGE.md](PASSO_1_MERGE.md) | Passo 1 do merge |
| [PESQUISA_DIRF_EXTINCAO.md](PESQUISA_DIRF_EXTINCAO.md) | Pesquisa extinção DIRF |
| [PESQUISA_RETIFICACAO_S1210_S5002.md](PESQUISA_RETIFICACAO_S1210_S5002.md) | Pesquisa retificação S-1210/S-5002 |
| [PESQUISA_TABELA21_CODINCIRRF.md](PESQUISA_TABELA21_CODINCIRRF.md) | Pesquisa Tabela 21 codIncIRRF |

---

## Prioridades para Fechar Janeiro/2025

1. 🔴 ~156 CPFs plano sem operadora → excluir planSaude block
2. 🟡 67 CPFs SINTACLUNS → remover planSaude
3. 🔴 100 CPFs duplicidade [106] → investigar dez/2024
4. 🟡 ~94 CPFs sem recibos → coleta manual
5. 🔴 1 CPF pensão + 4 CPFs precedência
6. → S-1299 fechar período (após tudo acima)
