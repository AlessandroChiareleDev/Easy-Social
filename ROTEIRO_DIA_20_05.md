# Roteiro Operacional - 20/05/2026

## Objetivo

Resolver os erros atuais de S-1210 dos 8 meses com planilhas em `C:\Users\xandao\Downloads\resposta final`, fechar somente os meses que ficarem sem erro pendente e produzir os relatórios finais de novembro/dezembro.

Meses alvo de correcao e fechamento condicional:

- `2025-02` fevereiro
- `2025-03` marco
- `2025-04` abril
- `2025-05` maio
- `2025-06` junho
- `2025-07` julho
- `2025-09` setembro
- `2025-10` outubro

Meses fora deste ciclo de fechamento:

- `2025-08` agosto, explicitamente pulado
- `2025-11` novembro, apenas relatorio final
- `2025-12` dezembro, apenas relatorio final
- `2025-01` janeiro, fora do escopo

## Guardrails

- Nao usar Download/ConsultarIdentificadores do eSocial neste ciclo.
- Permitido usar `EnviarLoteEventos` para S-1210 e S-1299 conforme pedido do usuario.
- Antes de fechar um mes, auditar no banco que o status final S-1210 por CPF esta todo em `sucesso` ou `202`/sucesso. Se restar `erro_esocial`, `erro_preparo`, `pendente`, `pendente_consulta` ou somente `falha_rede`, nao fechar aquele mes.
- Se um mes gerar erro novo na correcao, parar o fechamento daquele mes e seguir para o proximo, registrando no relatorio operacional.
- S-1299 so depois de zerar erro final do mes.
- Nao enviar S-1299 para novembro/dezembro neste roteiro.
- Persistir XML enviado, XML retorno, recibos e protocolos no banco/local como os scripts existentes ja fazem.

## Base verificada antes do inicio

Pasta auditada: `C:\Users\xandao\Downloads\resposta final`.

Cobertura das planilhas contra o banco:

| Mes       | Erros atuais | Arquivo                              | Cobertura |
| --------- | -----------: | ------------------------------------ | --------: |
| `2025-02` |            8 | `2025-02_relatorio_final_jaque.xlsx` |       8/8 |
| `2025-03` |           13 | `2025-03_relatorio_final_jaque.xlsx` |     13/13 |
| `2025-04` |           10 | `2025-04_relatorio_final_jaque.xlsx` |     10/10 |
| `2025-05` |            2 | `2025-05_relatorio_final_jaque.xlsx` |       2/2 |
| `2025-06` |            5 | `2025-06_relatorio_final_jaque.xlsx` |       5/5 |
| `2025-07` |            3 | `2025-07_relatorio_final_jaque.xlsx` |       3/3 |
| `2025-09` |            6 | `2025-09_relatorio_final_jaque.xlsx` |       6/6 |
| `2025-10` |            3 | `2025-10_relatorio_final_jaque.xlsx` |       3/3 |

Total: 50 CPFs trabalhadores com erro final, 0 faltantes nas planilhas.

## Classes de correcao

1. Plano de saude
   - Ler `CNPJ Operadora`, `Registro ANS`, `Valor Titular Descontado em Folha` da aba `Plano de saude`.
   - Gerar retificacao S-1210 `indRetif=2` preservando pagamentos e IR atual, acrescentando/substituindo `planSaude`.

2. Pensao alimenticia
   - Ler `CPF Beneficiario`, `Tipo Rendimento`, `Valor Deduzido` da aba `Pensao alimenticia`.
   - Gerar retificacao S-1210 `indRetif=2` preservando pagamentos e IR atual, acrescentando/substituindo `penAlim`.
   - Nunca enviar `vlrDedPenAlim=0.00`.

3. CPF dependente 1861
   - Ler CPF trabalhador e CPF dependente da aba `Dependente invalido`.
   - Gerar retificacao S-1210 inserindo `infoDep/cpfDep` antes dos grupos `infoIRCR` correspondentes, preservando `dedDepen`.
   - Se o eSocial exigir mais campos para algum dependente e a planilha nao tiver esses dados, registrar e nao fechar o mes.

4. Outros erros
   - Nao entram no fluxo da Jaque.
   - Se existirem nos 8 meses apos as correcoes, o mes nao fecha e o erro fica no relatorio operacional.

## Sequencia de execucao

1. Preparar insumos
   - Converter os 8 XLSX finais em um CSV operacional de respostas preenchidas.
   - Separar alvos por classe: plano, pensao, dependente 1861.
   - Gerar preflight local de XML para todos os meses.

2. Corrigir mes a mes
   - Ordem: fevereiro, marco, abril, maio, junho, julho, setembro, outubro.
   - Para cada mes:
     - Gerar XMLs de retificacao S-1210.
     - Validar `perApur`, CPF, `indRetif=2`, `nrRecibo`, ausencia de assinatura antiga e quantidade de grupos corrigidos.
     - Enviar S-1210.
     - Auditar resultado final por CPF.
     - Se restar erro, registrar e seguir para o proximo mes sem fechar.

3. Fechar meses zerados
   - Para cada mes que ficou sem erro final S-1210:
     - Gerar S-1299 producao.
     - Enviar via `EnviarLoteEventos`.
     - Consultar o protocolo do lote de envio para salvar recibo do S-1299.
     - Persistir em `explorador_eventos` e `s1299_fechamento_status`.
   - Nao baixar S-5002 neste roteiro, pois Download/ConsultarIdentificadores segue bloqueado sem pedido explicito para cota.

4. Relatorios novembro/dezembro
   - Auditar erros finais atuais de `2025-11` e `2025-12`.
   - Separar:
     - Jaque: plano de saude, pensao alimenticia, CPF dependente.
     - Dev: qualquer outro tipo de erro.
   - Gerar documentos finais com campos vazios para Jaque preencher e uma secao separada para erros de dev.

5. Relatorio operacional final
   - Tabela por mes com: corrigidos, sucesso, erro remanescente, fechado, recibo S-1299, motivo de nao fechamento.
   - Anexar caminhos dos manifests e relatorios gerados.

## Estado esperado ao final

- Oito meses processados.
- Todos os meses que zerarem erro fechados com S-1299.
- Meses que nao zerarem erro permanecem abertos, com causa registrada.
- Novembro e dezembro ficam com documentos finais para Jaque e para desenvolvimento.
