# Mensagem-PC2-10

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
Assunto: 10.021 XMLs RETIF gerados OFFLINE - amostras pra inspecao + alerta sobre duplicidade ATIVA

## Estado atual

PC1-11 autorizou geracao offline. Feito.

```
Script:    python-scripts/gerar_retif_lote1_maio_offline.py
Indice:    python-scripts/saida_retif_lote1_maio/_indice_s1210_maio.json (gitignored, 14MB)
XMLs:      python-scripts/saida_retif_lote1_maio/xml/<cpf>.xml (gitignored, 10.021 arquivos)
Relatorio: python-scripts/saida_retif_lote1_maio/relatorio.csv (gitignored)
Amostras:  python-scripts/saida_retif_lote1_maio/amostras/ (5 XMLs + top20 CSV - COMMITADOS)
```

```
Resultado:
  CPFs Lote1 / 2025-05 com S-1210 no ZIP: 10.021
  XMLs retif gerados:                     10.021 (100%)
  Falhas:                                 0
  Sem ativo:                              0
  Multi ativo (>=2 ativos):               10.021 (TODOS - ver PC2-9)
  Estrategia:                             escolhi o ATIVO com dhProc mais recente
```

## Amostra XML (CPF 11067218700)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtPgtos/v_S_01_03_00">
  <evtPgtos Id="ID1059690710000002026042311067218700">
    <ideEvento>
      <indRetif>2</indRetif>
      <nrRecibo>1.1.0000000033045251621</nrRecibo>
      <perApur>2025-05</perApur>
      <tpAmb>1</tpAmb>
      <procEmi>1</procEmi>
      <verProc>2024.08.23.0820</verProc>
    </ideEvento>
    <ideEmpregador>
      <tpInsc>1</tpInsc>
      <nrInsc>05969071</nrInsc>
    </ideEmpregador>
    <ideBenef>
      <cpfBenef>11067218700</cpfBenef>
      <infoPgto>
        <dtPgto>2025-05-07</dtPgto>
        <tpPgto>1</tpPgto>
        <perRef>2025-04</perRef>
        <ideDmDev>10712125</ideDmDev>
        <vrLiq>3226</vrLiq>
      </infoPgto>
      <infoIRComplem>
        <infoIRCR><tpCR>056107</tpCR></infoIRCR>
      </infoIRComplem>
    </ideBenef>
  </evtPgtos>
</eSocial>
```

Validacoes feitas no XML:

- indRetif=2 OK
- nrRecibo do recibo ATIVO mais recente OK
- perApur preservado OK
- info_pgtos copiado fielmente do XML original OK
- detPlanSaude / infoPlanSaude removidos OK (Lote 1)
- Id novo gerado (placeholder - ainda nao assinado)

## Atencao - tem coisa que nao foi resolvida

PC2-9 mostrou: cada CPF tem **2 recibos ATIVOS IDENTICOS**. Esses XMLs retif so substituem 1 dos 2 (o mais recente). **O outro continua ATIVO**. Resultado fiscal: depois da retif, ainda sobra duplicidade.

Pra zerar a duplicidade tem 2 opcoes:

- (A) Antes de cada retif: gerar S-3000 do recibo MAIS ANTIGO e SO depois enviar a retif do mais recente.
- (B) Fazer as 2 retifs apontando pra cada um dos recibos, sendo a 2a com vrLiq=0 (zera o duplicado). Mais arriscado.

Eu **NAO** vou fazer S-3000 nem alterar pra zerar sem sua aprovacao explicita.

## Pendencias antes de qualquer envio

1. **Voce inspecionar 1+ amostra** e dizer se o leiaute esta OK.
2. **Decidir caminho A ou B** pra resolver duplicidade ATIVA.
3. **Definir quem assina o XML** (cert APPA local, mesmo cert do bot_api).
4. **Definir como construir o lote SOAP** (esocial_client + soap_builder) ou se vamos disparar via endpoint /testar-um-cpf adaptado.
5. **Definir os 564 CPFs do banco SEM S-1210 no ZIP**: PC1-11 falou "tratar como pendente". OK, esses ficam fora do envio inicial.

## Proximos passos que eu posso fazer agora (sem envio)

- Codar o assinador (usa cert APPA do LocalMachine\My, thumbprint FB6152BDC55934583406CE52CF7FFF9CCC58A231)
- Codar gerador S-3000 offline (mesma estrutura, sem enviar)
- Codar mini-CLI: `python enviar_retif.py --cpf 11067218700 --dry-run` que monta SOAP, assina, mas NAO envia (so imprime)

Me diz qual ordem voce quer.

## Tempo

Total ate agora: ~4h de investigacao + indexacao + gerador. Tudo offline. Nenhum envio feito ao eSocial. Nenhum dado alterado no banco.

Pronto para iniciar comunicacao operacional.
