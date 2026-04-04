# Diagnóstico do Bloqueio S-1200 — Erro 989

## Data: 2026-07-04

## Situação Atual do eSocial para CPF 08132588983 (perApur=2024-12)

| Evento | Status | Recibo |
|--------|--------|--------|
| **S-1010 rubrica 566** | ✅ Corrigido (codIncIRRF 11→41) | `1.1.0000000039598012258` |
| **S-1010 rubrica 596** | ✅ Corrigido (codIncIRRF 12→42) | `1.1.0000000039598028920` |
| **S-1200 (Dez/2024)** | ❌ NÃO retificado (erro 989) | Original: `1.1.0000000030324738244` |
| **S-1210 (Dez/2024)** | ✅ Retificado | Novo: `1.1.0000000039598280881` |
| **S-1299 (Dez/2024)** | ✅ Período fechado | `1.1.0000000039598405395` |

## Diagnóstico do Erro 989

**Erro:** "Não é possível retificar o evento. Existe evento de pagamento associado que será impactado pelo evento retificador. Demonstrativos impactados: 10711955; 10711965."

### Análise dos Demonstrativos

O S-1200 de Dezembro/2024 tem 4 demonstrativos (dmDev):

| ideDmDev | Conteúdo | Referenciado por qual S-1210? |
|----------|----------|-------------------------------|
| `20241129.1.01512563` | Adiantamento (rubrica 9276, R$231,00) | Nenhum (sem pagamento associado) |
| `20241129.1.01512566` | Adiantamento (rubrica 9284, R$667,80) | Nenhum |
| **`10711955`** | Folha principal Dez (10 rubricas, incl. 566) | ❓ **S-1210 de Jan/2025** (pagamento da folha de Dez) |
| **`10711965`** | 13º salário Dez (3 rubricas, incl. 596) | ❓ **S-1210 de Jan/2025** |

O S-1210 de Dezembro/2024 referencia:
- ideDmDev `10711884` (perRef=2024-11, dtPgto=2024-12-06) → Folha de NOV paga em DEZ
- ideDmDev `10711933` (perRef=2024, dtPgto=2024-12-20) → 13º pago em DEZ

**CONCLUSÃO:** Os dmDevs `10711955` e `10711965` (da folha de Dezembro) foram **pagos em Janeiro/2025**. Existe um S-1210 em `perApur=2025-01` que os referencia. Esse S-1210 bloqueia a retificação do S-1200 de Dezembro.

## Bloqueio Atual

O **Download Cirúrgico do eSocial** está indisponível entre os dias 1-7 do mês:
> "Não é possível enviar solicitação de download entre os dias 1 e 7 do mês"

Precisamos do `nrRecibo` do S-1210 de Janeiro/2025 para retificá-lo, mas não podemos consultá-lo via API até **08/07/2026**.

## Plano de Recuperação (a executar quando tivermos o nrRecibo de Jan/2025)

### Ordem das Operações:

```
1. S-1298 (perApur=2025-01) → Reabrir Janeiro/2025
2. S-1298 (perApur=2024-12) → Reabrir Dezembro/2024
3. S-1210 retif (perApur=2025-01) → Retificar S-1210 de Jan (libera dmDevs 10711955/10711965)
4. S-1200 retif (perApur=2024-12) → Retificar S-1200 de Dez (agora liberado!)
5. S-1299 (perApur=2024-12) → Fechar Dezembro/2024
6. S-1210 retif (perApur=2025-01) → Retificar S-1210 de Jan novamente (com dmDevs atualizados)
7. S-1299 (perApur=2025-01) → Fechar Janeiro/2025
```

### Dados Necessários (FALTANTES):

- **nrRecibo do S-1210 de Janeiro/2025** → Pode ser obtido via:
  - Download Cirúrgico após dia 08/07
  - Portal web eSocial (login.esocial.gov.br)
  - Sistema de folha APPA (se armazena recibos)

### Opções Imediatas:

1. **Esperar até 08/07** e usar Download Cirúrgico via API
2. **Acessar o portal web do eSocial** e buscar manualmente o S-1210 de Jan/2025
3. **Verificar o sistema APPA** se tem o nrRecibo armazenado

## Nota sobre o S-1210 de Dez/2024 Retificado

Na execução do pipeline, retificamos o S-1210 de Dezembro (recibo `1.1.0000000039598280881`). 
Essa retificação referencia dmDevs `10711884` e `10711933` (pagamentos de Novembro pagos em Dezembro).
Essa retificação foi CORRETA e necessária para as rubricas do período novembro.
A retificação do S-1210 de Dezembro NÃO desbloqueia o S-1200 de Dezembro porque os dmDevs bloqueadores (10711955/10711965) são de OUTRO S-1210 (Janeiro/2025).
