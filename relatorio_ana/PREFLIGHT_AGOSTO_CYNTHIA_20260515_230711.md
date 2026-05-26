# Preflight Agosto/2025 - Cynthia

Gerado em: 2026-05-15T23:07:11

## Erros atuais locais
- Nao OK total: 672
- Recibo 459: 267
- Plano saude codigo 8: 99
- Pensao codigo 8: 4
- Aviso 202: 119
- Overlap 1089: 55
- Duplicidade/sem mudanca 543: 127

## Recibos 459
- Planilha tem 370 CPFs com recibo correto.
- Cobre 267 de 267 CPFs que ainda estao em 459.
- Faltantes: 0.
- Arquivo JSON pronto para override: AGOSTO_RECIBO_OVERRIDE_CYNTHIA_20260515_230711.json
- Conclusao: grupo pronto para dry-run/reenvio controlado com recibo_override_por_cpf, sem consultar eSocial.

## Plano de saude codigo 8
- Erros atuais: 99 CPFs.
- OPERADORAS.xlsx traz 25 codigos de evento e 13 operadoras com CNPJ/ANS.
- s1210_operadoras no banco para Agosto: {'ok': True, 'rows': []}.
- XML local com planSaude presente: 0 de 99.
- Conclusao: util como mapa CNPJ/ANS, mas ainda falta CPF+valor por trabalhador para montar plan_saude_por_cpf.

## Pensao codigo 8
- Erros atuais: 4 CPFs.
- pensao.xlsx cobre 4 desses CPFs.
- XML local com penAlim presente: 0 de 4.
- Conclusao: arquivo ajuda com valor/percentual, mas falta CPF do beneficiario da pensao para gerar penAlim com seguranca.

## Avisos 202
- Total: 119.
- XML local com dedDepen presente: 0 de 119.
- Conclusao: ja foram aceitos com advertencia; nao sao o primeiro bloqueio para limpar Agosto.

## Ordem segura sugerida
1. Primeiro atacar 459 com recibo correto, em lote pequeno 1-10 antes de ampliar.
2. Depois preparar plano de saude quando houver CPF+valor por trabalhador.
3. Depois preparar pensao quando houver beneficiario/cpfDep por trabalhador.
4. Deixar 1089/543 para reavaliacao depois das correcoes principais.

Nenhum envio eSocial, Download ou ConsultarIdentificadores foi executado neste preflight.
