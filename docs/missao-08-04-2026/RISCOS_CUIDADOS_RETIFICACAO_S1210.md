# RISCOS E CUIDADOS — Retificação S-1210 APPA

> **Data:** 08/04/2026  
> **Classificação:** Documento de análise de riscos para decisão gerencial

---

## Resumo de Risco

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Perda de créditos de suspensão (terceiros) | **Muito Baixa** | **Crítico** | Não toca S-1200/S-1020; snapshot S-5011 |
| DCTFWeb retificadora automática errada | **Baixa** | **Alto** | Monitorar e-CAC pós-fechamento |
| Período ficar aberto sem fechar (S-1299) | **Média** | **Médio** | Pipeline atômico com retry |
| Rate limit em homologação | **Alta** | **Baixo** | Batch com delay; testar poucos CPFs |
| XML malformado rejeitado pelo eSocial | **Baixa** | **Baixo** | Validação XSD pré-envio |
| nrRecibo inválido (evento já retificado) | **Baixa** | **Médio** | Download prévio confirma recibo vigente |

---

## Risco 1 — Perda de Créditos de Suspensão de Terceiros

### O que é

A APPA possui processos judiciais que suspendem o recolhimento de contribuições a terceiros (Sistema S — SESC, SENAI, etc.). Isso representa ~R$4.27M por período que NÃO são pagos e ficam como crédito/suspensão na DCTFWeb.

### Onde esses créditos moram no eSocial

```
S-1070 → Cadastro do processo judicial
  └── nrProc, indMatProc, etc.

S-1020 → Tabela de Lotações (aqui é o ponto!)
  └── codTercSusp = código dos terceiros suspensos
  └── procJudTerceiro → referencia o S-1070
  
S-1200 → Remuneração mensal
  └── codLotacao → aponta para a lotação com suspensão
  
S-5011 → Totalizador patronal (RETORNO do eSocial)
  └── vrSuspBcCp00 = valor base suspensa
  └── infoCREstab = CRs por estabelecimento
```

### Por que a retificação do S-1210 NÃO afeta isso

O S-1210 é um evento de **pagamento** que informa:
- Data de pagamento
- Valor líquido
- IR retido
- Código de receita (tpCR)

Ele **NÃO contém**:
- codLotacao (está no S-1200)
- codTercSusp (está no S-1020)
- procJudTerceiro (está no S-1020)
- Nenhuma informação de contribuição patronal

O totalizador S-5011 é calculado pelo eSocial exclusivamente a partir de:
- S-1200 (remuneração + lotação)
- S-1020 (lotação + suspensão)
- S-1070 (processo judicial)

**Conclusão técnica:** Retificar S-1210 impacta SOMENTE o S-5002 (totalizador de IR). Os créditos de terceiros são matematicamente impossíveis de serem afetados.

### Evidência encontrada na pesquisa web

A documentação oficial do gov.br confirma:
- `REGRA_PAGTO_IND_RETIFICACAO` trata exclusivamente do S-1210 e seu nrRecibo
- O S-1210 é validado contra o beneficiário (CPF), não contra lotações
- A retificação do S-1200 requer lógica separada (e nós NÃO estamos fazendo isso)

### Medida de segurança extra

Mesmo com certeza técnica, faremos **snapshot do S-5011 antes e depois**:
- Se qualquer campo de suspensão mudar → PARAR e investigar
- Se os CRs patronais mudarem → PARAR e investigar
- Somente se S-5011 for idêntico pré/pós → continuar

---

## Risco 2 — DCTFWeb Retificadora Automática

### O que é

Quando o período é fechado com S-1299, o eSocial gera novos totalizadores. A DCTFWeb pode gerar uma retificadora automaticamente com base nos novos totalizadores.

### Cenário preocupante

Se a retificadora da DCTFWeb for gerada e:
1. Os valores de IR mudarem (esperado — é o objetivo)
2. Mas se a DCTFWeb recalcular os débitos totais e houver diferença → pode gerar saldo a pagar
3. Se gerar saldo != 0 sem pagar → risco de CADIN

### Por que a probabilidade é baixa

- Retificar S-1210 altera apenas o S-5002 (IR)
- IR retido na fonte é tratado separadamente dos créditos patronais na DCTFWeb
- A DCTFWeb já tem o valor de IR original; estamos corrigindo para o valor correto
- Se a dedução estava zerada e agora está correta, o IR retido **aumenta** → o contribuinte tem **mais crédito**, não menos

### Mitigação

1. Verificar no e-CAC após cada batch se há retificadora pendente
2. Se houver → analisar manualmente antes de transmitir
3. Ter contato direto com Dra. Cintia/Sandro para avaliar

---

## Risco 3 — Período Aberto Sem Fechar

### O que é

Se o sistema envia S-1298 (reabertura) mas falha antes de enviar S-1299 (fechamento), o período fica "aberto". Isso pode impedir novos fechamentos e gerar inconsistências.

### Impacto

- Período aberto = eSocial não gera novos totalizadores
- Pode afetar períodos subsequentes se houver dependência
- É **recuperável** — basta enviar outro S-1299

### Mitigação

- Pipeline com try/catch/retry
- Se S-1210 falha parcialmente → o que foi aceito fica, o resto pode ser reenviado
- S-1299 sempre é o último passo, com retry automático
- Se tudo falhar → reabertura manual possível a qualquer tempo

---

## Risco 4 — Nota Técnica S-1.3 nº 04/2025

### O que muda

A NT 04/2025 trouxe uma mudança relevante:

> "Com a nova alteração Nota Técnica S-1.3 n° 04/2025, o S-1210 não precisará mais ser excluído, se for retificado o S-1200 incluindo um novo demonstrativo."

### Impacto para nós

**Nenhum.** Esta NT trata do caso contrário ao nosso — quando alguém quer retificar o S-1200 e antes precisava excluir o S-1210 primeiro. Nós NÃO estamos retificando S-1200. Estamos retificando SOMENTE S-1210.

Mas é importante saber que a partir de 01/2025, os eventos S-1200, S-1210 e outros periódicos são gerados na versão **S-1.3** do leiaute. Nosso gerador já está na versão S-1.3.

---

## Risco 5 — Volume e Praticidade

### Números reais

| Cenário | CPFs | Lotes S-1210 | Lotes totais | Tempo estimado* |
|---|---|---|---|---|
| 1 mês | 8.414 | 169 | 171 | ~3-6 horas |
| 12 meses | ~100.000 | ~2.000 | ~2.024 | ~2-4 dias |

*Assumindo ~1-2 segundos por lote sem rate limiting agressivo

### Riscos práticos

- Se o eSocial estiver lento → timeout
- Se certificate expirar durante batch → todos os envios seguintes falham
- Se houver manutenção do eSocial → retry no dia seguinte

### Mitigação

- Checkpoint: salvar progresso a cada lote
- Resumo: poder retomar de onde parou
- Monitoramento: log em tempo real no terminal

---

## Checklist Pré-Execução

### Antes de rodar em homologação

- [ ] Certificado digital da APPA válido e configurado
- [ ] Pipeline modificado (sem S-1200)
- [ ] Download de 1 S-1210 funcionando
- [ ] Parser extraindo dados completos
- [ ] Snapshot S-5002 funcionando
- [ ] Snapshot S-5011 funcionando (ou pelo menos S-5011 parser implementado)

### Antes de rodar em produção

- [ ] Teste com 1 CPF aprovado em homologação
- [ ] S-5011 confirmado inalterado pré/pós
- [ ] S-5002 confirmado com valores de IR corretos
- [ ] Prontuário enviado e aprovado por Sandro
- [ ] Aprovação por escrito da Dra. Cintia
- [ ] Backup dos nrRecibos originais (para reverter se necessário)

### Para reverter (plano de contingência)

Se algo der errado, é possível retificar novamente o S-1210 com os valores originais (volta ao que era antes). Os nrRecibos originais permitem rastrear cada evento.

```
Reverter = S-1298 → S-1210(retif com dados originais) → S-1299
```

Ou seja: o processo é **inteiramente reversível**.
