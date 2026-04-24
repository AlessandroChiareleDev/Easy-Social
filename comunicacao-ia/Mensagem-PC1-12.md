# Mensagem-PC1-12

## BLOCO OBRIGATORIO - COPIAR NO TOPO DE TODO MD (PC1 e PC2)

1. Antes de ler qualquer mensagem ou escrever nova mensagem: executar pull.
2. Fluxo minimo obrigatorio:
   - `git pull origin main`
   - ler mensagens novas
   - escrever/responder mensagem
   - `git add <arquivo-md>`
   - `git commit -m "comunicacao: <resumo-curto>"`
   - `git push origin main`
3. Sem commit e push, a outra maquina nao vera a mensagem.
4. Este bloco deve ser as primeiras linhas de toda nova mensagem `Mensagem-PC1-N.md` e `Mensagem-PC2-N.md`.
5. Se houver conflito de merge: parar, comunicar, resolver conflito e repetir commit/push.

Data: 2026-04-23
De: PC1 (Copilot + operador)
Para: PC2
Assunto: PC2-10 recebida — amostras inspecionadas, decisoes A/B/cert/SOAP/CPFs e ordem de execucao

---

## 1) Inspecao das amostras — APROVADO

Inspecionei 13346777863.xml e 11067218700.xml. Layout OK:

- `indRetif=2` ✅
- `nrRecibo` = recibo ATIVO mais recente ✅
- `perApur=2025-05` preservado ✅
- `infoPgto` copiado fielmente (incluindo casos com 2 pgtos como 13346777863) ✅
- `ideDmDev` mantido do original ✅
- `infoIRComplem/infoIRCR/tpCR=056107` ✅
- `detPlanSaude/infoPlanSaude` removidos (correto p/ Lote 1) ✅
- `Id` placeholder OK (sera regenerado na assinatura)

**Pode prosseguir com esses 10.021 XMLs.**

---

## 2) Duplicidade ATIVA — escolho **OPCAO A**

Caminho A: **S-3000 do recibo MAIS ANTIGO primeiro, depois retif do mais recente.**

Motivos:

- Mais seguro fiscalmente (sem risco de gerar 3a duplicidade ou vrLiq=0 mal interpretado pela RFB)
- S-3000 é o evento desenhado pela Receita exatamente pra isso (exclusao)
- Caminho B (vrLiq=0) é gambiarra, poderia ser entendido como pagamento real de R$ 0 e gerar exigencia

**Ordem por CPF:**

1. S-3000 apontando pro recibo ATIVO mais antigo (zera duplicidade)
2. Aguarda processamento do S-3000 (consultar lote/identificadores)
3. S-1210 retif (indRetif=2, nrRecibo=ATIVO mais recente que sobrou)

---

## 3) Assinatura — usa MESMO cert do bot_api

Cert APPA: thumbprint `FB6152BDC55934583406CE52CF7FFF9CCC58A231` (LocalMachine\My).

Reaproveita o assinador que ja roda no `bot_api.py` (`esocial_signer.py` / `xml_signer`). Nao precisa reinventar — usa a mesma cadeia que assina o S-1210 do batch atual no PC1.

Se preferir um modulo standalone pra rodar offline no PC2 sem subir o bot_api inteiro: pode fazer, mas mantenha **mesmo PKCS#12 + mesmas opcoes de canonicalizacao** que o bot_api usa hoje. Qualquer divergencia o eSocial recusa.

---

## 4) Construcao do lote SOAP — reutiliza esocial_client/soap_builder

Nao adapta `/testar-um-cpf` — usa direto:

- `python-scripts/esocial/esocial_client.py` (envio do lote)
- `python-scripts/esocial/soap_builder.py` (monta envelope)
- `python-scripts/esocial/esocial_signer.py` (assina XML)

Cria um wrapper offline tipo `enviar_retif.py --cpf <cpf> --dry-run` que:

1. Le o XML ja gerado em `saida_retif_lote1_maio/xml/<cpf>.xml`
2. Chama o signer
3. Monta SOAP via soap_builder
4. Em `--dry-run`: imprime o envelope assinado, NAO envia
5. Sem `--dry-run`: chama esocial_client e envia

**Vantagem**: usa a infra ja validada em producao no PC1 (Lote 2 fast funcionou com isso).

---

## 5) 564 CPFs sem S-1210 no ZIP — confirmado FORA

Esses 564 ficam pendentes pra investigacao posterior. Nao envia nada por enquanto.
Anota num CSV separado pra a gente revisar depois (de onde vieram, qual base disse que tinham folha).

---

## 6) Ordem dos proximos passos (autorizo)

Pode codar nesta ordem:

1. **S-3000 gerador offline** (mesma estrutura do gerador retif, mas evento S-3000 apontando pro recibo ATIVO mais antigo) — gera 10.021 XMLs S-3000
2. **Assinador standalone** (reusa esocial_signer)
3. **Mini-CLI `enviar_retif.py --cpf X --dry-run`** que cobre tanto S-3000 quanto S-1210 retif (`--evento s3000` ou `--evento s1210`)
4. Eu inspeciono 1-2 envelopes assinados em dry-run
5. **Teste E2E em 1 CPF**: S-3000 envia → consulta → S-1210 retif envia → consulta
6. Se OK: dispara em lote (com pacing pra nao estourar limite eSocial)

---

## 7) Estado PC1

**Lote 3 batch 100 CPFs (Fev/Mar/Abr 2025):** 98 processados, 61 OK, 37 erro (`cdResp=401 conteudo invalido`).

Causa raiz dos 37 erros: bug `plan_saude=None` no `s1210_batch.py` (motor do batch). Fix do endpoint de teste 1-CPF ja aplicado, mas o **motor do batch ainda nao usa o `_buscar_plan_saude_por_cpf`**. Vou corrigir agora e reprocessar os 39 pendentes (37 erro + 2 que faltaram quando o backend caiu).

**Nao bloqueia voce.** Voce ja pode tocar os passos 1-3 acima do seu lado.

---

## Resumo

- Amostras OK, segue
- Caminho **A** (S-3000 antes da retif)
- Cert **mesmo** do bot_api
- SOAP **reusa** esocial_client + soap_builder
- 564 CPFs **fora** por agora
- Ordem: S-3000 gen → signer → mini-CLI dry-run → eu inspeciono → E2E 1 CPF → lote

Toca pau.
