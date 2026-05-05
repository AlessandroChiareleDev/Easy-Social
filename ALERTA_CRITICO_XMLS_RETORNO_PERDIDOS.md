# 🚨🚨🚨 ALERTA CRÍTICO — XMLs DE RETORNO DO eSOCIAL FORAM PERDIDOS 🚨🚨🚨

> **Data do alerta:** 2026-04-25
> **Quem identificou:** Alex (PC1) durante preparação do L1 Novembro
> **Severidade:** 🔴 CRÍTICA — Ana precisa dos XMLs e NÃO TEMOS

---

## ❌ O PROBLEMA (em uma frase)

**Todos os envios S-1210 feitos até hoje (Fev, Mar, Abr, Mai, Ago, Set, Out 2025) foram processados pelo eSocial, mas os XMLs de retorno NÃO FORAM SALVOS em disco.** O backend só extraiu os campos estruturados (`cdResposta`, `nrRecibo`, `ocorrencias`) e gravou no banco — o XML cru foi descartado.

## 💥 O IMPACTO

- **Ana precisa dos XMLs de retorno completos** para auditoria, comprovação fiscal e cruzamento de dados.
- **Não temos como recuperar retroativamente sem custo:**
  - Reconsultar cada protocolo via `ConsultarLoteEventos` no eSocial **gasta consultas (limite 10/dia)**
  - Protocolos antigos podem não responder mais (janela de retenção do eSocial)
  - Mesmo se reconsultar, o XML retornado agora pode não ser idêntico ao do dia do envio (ocorrências podem ter sido recalculadas)
- **O que temos hoje:**
  - ✅ Banco `s1210_cpf_envios`: status, recibo, ocorrência (campos parseados)
  - ✅ JSONLs em `python-scripts/saida_lote1_*/envio_*.jsonl`: resumo por CPF
  - ❌ XML cru de envio: **PERDIDO**
  - ❌ XML cru de retorno (consultaLote): **PERDIDO**

## 🎯 O QUE FAZER A PARTIR DE AGORA (Lote 1 Novembro em diante)

### Estrutura de armazenamento OBRIGATÓRIA

```
ARQUIVOS_RETORNO/
  2025-11/
    envios/         ← XML resposta do EnviarLoteEventos (protocolo)
    consultas/      ← XML resposta do ConsultarLoteEventos (COMPLETO, com recibo + ocorrências)
    resumo/         ← JSONLs (continuam como antes)
    erros/          ← XMLs individuais dos eventos com erro (extraídos da consulta)
  2025-12/
    ...
```

Pasta na **raiz do projeto**, ignorada no `.gitignore` (volume grande, vai pra GBs).

### Patch técnico necessário (LOCAL, sem commit por enquanto)

1. **`python-scripts/esocial/esocial_client.py`**
   - `enviar_lote()` → adicionar param `dump_xml_to_dir` que salva o XML cru da resposta
   - `consultar_lote()` → mesma coisa, salvar XML cru ANTES de parsear
2. **Scripts `_envio_lote1_<mes>.py`**
   - Criar pasta `ARQUIVOS_RETORNO/<YYYY-MM>/{envios,consultas,resumo,erros}/` no início
   - Passar `dump_xml_to_dir` em cada chamada
   - Após parsear consulta, dumpar XML individual de cada evento com `cdResposta != 201` em `erros/`

## 📋 PROTOCOLO PARA AGENTE / DEV FUTURO

**ANTES de rodar QUALQUER script `_envio_*.py`:**

1. ✅ Confirmar que `ARQUIVOS_RETORNO/<mes>/` existe
2. ✅ Confirmar que o script chama `dump_xml_to_dir`
3. ✅ Confirmar que `.gitignore` tem `ARQUIVOS_RETORNO/`
4. ❌ **NUNCA** rodar envio sem captura de XML — repete a tragédia

## 🔗 Onde isso está referenciado

- `README.md` (topo, junto da missão APPA)
- `docs/MISSAO_S1210_APPA_21-04-2026/LEIA_PRIMEIRO.md` (referência cruzada)
- `/memories/repo/xmls-retorno-perdidos.md` (memória do agente)

## 📞 Decisão pendente do usuário

- [ ] Liberar consultas (gasta limite 10/dia) para tentar recuperar retroativamente algum mês prioritário?
- [ ] Avisar Ana antes ou depois de tentar recuperação?
- [ ] L1 Novembro será o primeiro mês com captura completa — tratar como **piloto** da nova arquitetura.

---

**Este arquivo NÃO PODE SER REMOVIDO** até que:

1. Toda a captura de XML esteja implementada e em produção
2. Ana tenha confirmado recebimento dos XMLs dos próximos envios
3. Decisão final sobre meses retroativos esteja registrada
