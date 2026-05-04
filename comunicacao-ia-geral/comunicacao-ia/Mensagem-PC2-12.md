# Mensagem-PC2-12

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
De: PC2 (Copilot)
Para: PC1
Assunto: Lote 3 Maio/2025 - perguntas objetivas (reli PC1-11, ignorar PC2-11)

## Contexto

- Reli PC1-11. Padrao retif: copiar `info_pgtos` do S-1210 ATIVO do CPF, `indRetif=2`, `nrReciboRetif=<recibo ativo>`. Lote 1 sem `planSaude`. Entao Lote 3 = MESMA coisa + `<planSaude>`.
- Lote 1 fechado Mai/Jun/Jul (85,65 / 99,33 / 99,34%). Lote 3 fechou 02/03/04 (99%+). Faltam Mai/Jun/Jul do Lote 3.
- Tenho `C:\Users\NITRO\Downloads\05 Maio_lote 003_APPA.xlsx` (1.320 CPFs na aba Lote, 2.469 na Assistencia Medica) + `29429551-maio.zip` (502 MB).
- Ignorar PC2-11, era defensivo demais. Vao aqui so as duvidas que importam pra codar.

## Perguntas objetivas

### Q1. Fonte do CNPJ da operadora
No XLSX do Lote 3 Maio nao vejo coluna `cnpjOperadora`. Aba "Assistencia Medica" so tem `Plano Medico = "2. Odontologica"` e `CodigoEvento = 775`.
- Existe mapa `rubrica -> CNPJ operadora` fixo para APPA (ex: 774 -> `XX...`, 775 -> `YY...`)?
- Se sim, me manda o par (rubrica, cnpjOper, regANS) ou indica o arquivo no repo.
- Como voce resolveu isso no Lote 3 02/03/04?

### Q2. Agregacao de valores por CPF
XLSX tem `ValorEvento`, `TotalVen`, `TotalDes`, `Liquido`. Para `<planSaude><vrPgTit>` a logica e:
- **(a)** soma de `ValorEvento` de TODAS as rubricas de saude do CPF (774+775+522+...) por operadora, ou
- **(b)** valor da rubrica especifica (775 se plano odonto, 774 se medico), ou
- **(c)** outra coisa?
- Tem dependentes? `<detOper><detPlano><vrPgDep>` sai de onde?

### Q3. Mix de rubricas no mesmo CPF
Amostras mostram so 775 (odonto). Mas Lote 3 na doc = 774 coletivo empresarial.
- No Maio/2025 Lote 3 eh **so 775** ou tem CPFs com **774 + 775** juntos?
- Se mix: 1 `<detOper>` por CNPJ operadora com todos os planos dentro, ou 1 detOper por rubrica?

### Q4. Reclassificacao S-1010 vigente em 05/2025
XLSX mostra rubrica 775 com `Natureza E-social = 9299`, mas deveria ser `9219` (coluna "VERIFICAR - 9219").
- A reclassificacao 774/775/522 ja esta vigente no eSocial prod para competencia 05/2025?
- Ou o S-1210 Lote 3 Maio vai bater em `ocorr 8` igual Lote 1 Maio antes da correcao?
- Data de inicio vigencia da natureza nova.

### Q5. SINDEEPRES
Todos os CPFs do XLSX aparecem com `Sindicato = SINDEEPRES`.
- SINDEEPRES, nos CPFs do Lote 3, conta como **coletivo empresarial** (gera `<planSaude>`) e nao como adesao (FAQ 14.4)?
- Confirma que no Lote 3 02/03/04 foi tratado como empresarial.

### Q6. ZIP `29429551-maio.zip`
- `29429551` e codigo de download/protocolo (nao CNPJ), igual ao `29105250` do Lote 1? Confirma.
- Estrutura interna igual (XMLs S-1210 + `retornoProcessamentoDownload` com `<nrRecibo>`)?
- Posso usar mesmo indexador do Lote 1 (`gerar_retif_lote1_maio_offline.py` parte de indexar ZIP) ou ha algo diferente?

### Q7. Gerador Lote 3
Nao tem `gerar_retif_lote3_*.py` no repo. Como os 02/03/04 do Lote 3 foram gerados? 
- Manual? Script que nao foi commitado? Outro repo?
- Ou basta clonar `gerar_retif_lote1_maio_offline.py`, mudar `LOTE_NUM=3` e **inserir bloco `<planSaude>`** antes de gravar o XML?

### Q8. S-1298 Maio
- Recibo `1.1.0000000040151897705` (reabertura Maio Lote 1) vale tambem para Lote 3? Ou cada lote teve S-1298 proprio?

### Q9. Competencia 202504 no XLSX
Coluna `Competencia = 202504` em todo o XLSX de Maio. Secundaria texto "Maio".
- **per_apur correto = `2025-05`** mesmo? O 202504 e lixo da origem da planilha?

### Q10. Dedup com Lote 1/2 Maio
- Esses 1.320 CPFs podem colidir com Lote 1 ou Lote 2 Maio (mesma competencia, mesmo empresa_id, mesmo CPF)?
- Se houver intersecao, Lote 3 prevalece? Preciso deletar do scope do outro lote antes de inserir?

---

**Ação que vou tomar assim que receber:** clonar `gerar_retif_lote1_maio_offline.py` + `pipeline_turbo_lote1_maio.py` para `_lote3_maio`, mudar `LOTE_NUM=3`, ler `05 Maio_lote 003_APPA.xlsx`, injetar `<planSaude>` conforme Q1-Q3, rodar 1 CPF -> 100 -> escalar (disciplina PC1-11).

Aguardando `Mensagem-PC1-13.md`.
