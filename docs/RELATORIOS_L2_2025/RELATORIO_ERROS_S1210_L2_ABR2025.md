# Relatório de Erros — S-1210 · Lote 2 · Abril/2025

> **Escopo:** Lote 2 · `2025-04` (CPFs com plano de saúde individual).
> **Gerado em:** 29/04/2026 21:30
> **Fonte:** endpoint `/api/s1210-repo/codigos-agregados` + `/por-lote` (mesmas rotas do front).

---

## 1. Números gerais

| Status | Qtd | % do total |
|---|---:|---:|
| `ok` (201) | 1123 | 88.4 % |
| `erro` | 147 | 11.6 % |
| **Total** | **1270** | 100 % |

### Distribuição dos erros

| Tipo | Qtd | % dos erros |
|---|---:|---:|
| `buscar_recibo` (pré-eSocial) | 147 | 100.0 % |

### Códigos brutos retornados pelo eSocial

| chave | qtd | tipo | descrição (primeiros 120 chars) |
|---|---:|---|---|
| `201/` | 1123 | ok | Sucesso. |
| `erro/` | 147 | err | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 55200885787 |

---

## 5. `buscar_recibo` (pré-eSocial) — 147 caso(s)

Etapa **antes** do envio: o pipeline buscou no ZIP do S-5001 indexado e não encontrou S-1210 com `nrRecibo` para o CPF.

**Hipóteses:** (a) CPF nunca teve S-1210 enviado naquele mês (deveria ser **inclusão**, não retificação); (b) ZIP incompleto; (c) CPF inativo/desligado sem folha.

---

## 6. Lista de CPFs em erro (147)

| CPF | cd | descrição (curta) |
|---|---|---|
| `00325551723` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 00325551723 |
| `00590466780` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 00590466780 |
| `00886095700` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 00886095700 |
| `00946507724` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 00946507724 |
| `01083141708` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01083141708 |
| `01175598739` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01175598739 |
| `01250577764` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01250577764 |
| `01452181713` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01452181713 |
| `01470785714` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01470785714 |
| `01616594705` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01616594705 |
| `01838597743` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01838597743 |
| `01923724754` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01923724754 |
| `01924914743` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01924914743 |
| `01963062728` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 01963062728 |
| `02148561782` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02148561782 |
| `02175777766` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02175777766 |
| `02197291742` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02197291742 |
| `02202906797` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02202906797 |
| `02231260719` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02231260719 |
| `02350949788` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02350949788 |
| `02397825775` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02397825775 |
| `02589299796` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02589299796 |
| `02627291726` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02627291726 |
| `02730398732` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 02730398732 |
| `03029811794` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03029811794 |
| `03225650730` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03225650730 |
| `03330047798` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03330047798 |
| `03558536711` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03558536711 |
| `03607300780` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03607300780 |
| `03652450701` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03652450701 |
| `03858406759` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 03858406759 |
| `04140268700` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 04140268700 |
| `04483259776` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 04483259776 |
| `04529024792` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 04529024792 |
| `04764769760` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 04764769760 |
| `04785935707` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 04785935707 |
| `05279594725` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05279594725 |
| `05293778706` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05293778706 |
| `05312807729` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05312807729 |
| `05439104747` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05439104747 |
| `05675710760` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05675710760 |
| `05880743730` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 05880743730 |
| `07330265756` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 07330265756 |
| `07360659701` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 07360659701 |
| `07433332766` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 07433332766 |
| `08056271708` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08056271708 |
| `08078204744` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08078204744 |
| `08092379700` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08092379700 |
| `08428218722` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08428218722 |
| `08648010764` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08648010764 |
| `08780630723` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08780630723 |
| `08815948732` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08815948732 |
| `08822453760` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08822453760 |
| `08878413763` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 08878413763 |
| `09070496720` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 09070496720 |
| `09326817784` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 09326817784 |
| `09403288795` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 09403288795 |
| `09632555767` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 09632555767 |
| `09962582482` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 09962582482 |
| `10101338708` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10101338708 |
| `10122185706` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10122185706 |
| `10240359720` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10240359720 |
| `10324645775` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10324645775 |
| `10824399757` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10824399757 |
| `10864927738` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 10864927738 |
| `11152736710` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11152736710 |
| `11226036732` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11226036732 |
| `11350346721` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11350346721 |
| `11353247783` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11353247783 |
| `11370154704` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 11370154704 |
| `12099789703` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12099789703 |
| `12306718709` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12306718709 |
| `12508062758` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12508062758 |
| `12663485730` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12663485730 |
| `12667879767` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12667879767 |
| `12680218736` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12680218736 |
| `12817440773` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12817440773 |
| `12943427705` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 12943427705 |
| `13023201730` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 13023201730 |
| `13193278777` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 13193278777 |
| `13759233740` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 13759233740 |
| `13869896736` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 13869896736 |
| `13894865750` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 13894865750 |
| `14007251860` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14007251860 |
| `14069843701` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14069843701 |
| `14090129800` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14090129800 |
| `14156391752` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14156391752 |
| `14230971737` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14230971737 |
| `14374360727` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14374360727 |
| `14394171725` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 14394171725 |
| `15278284765` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 15278284765 |
| `15613546789` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 15613546789 |
| `16128803717` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16128803717 |
| `16227621773` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16227621773 |
| `16275916729` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16275916729 |
| `16421706746` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16421706746 |
| `16782632730` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16782632730 |
| `16791728752` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 16791728752 |
| `17096205799` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17096205799 |
| `17320163721` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17320163721 |
| `17401948702` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17401948702 |
| `17526580786` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17526580786 |
| `17780279707` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17780279707 |
| `17787236752` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 17787236752 |
| `18108727740` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 18108727740 |
| `18441258740` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 18441258740 |
| `20066237700` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 20066237700 |
| `26506132892` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 26506132892 |
| `32787103391` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 32787103391 |
| `37865994591` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 37865994591 |
| `48962495856` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 48962495856 |
| `48963658791` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 48963658791 |
| `52262243549` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 52262243549 |
| `53157206753` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 53157206753 |
| `55200885787` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 55200885787 |
| `56626401734` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 56626401734 |
| `59372222704` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 59372222704 |
| `69118280749` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 69118280749 |
| `71345469772` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 71345469772 |
| `72444487753` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 72444487753 |
| `79340741749` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 79340741749 |
| `81235879704` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 81235879704 |
| `84378050749` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 84378050749 |
| `86713027768` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 86713027768 |
| `87491753434` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 87491753434 |
| `88034020710` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 88034020710 |
| `88181294734` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 88181294734 |
| `88694240734` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 88694240734 |
| `89284003768` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 89284003768 |
| `90023676787` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 90023676787 |
| `90727410725` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 90727410725 |
| `90914589768` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 90914589768 |
| `92119298734` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 92119298734 |
| `92167667787` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 92167667787 |
| `92702163734` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 92702163734 |
| `92749356768` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 92749356768 |
| `95397523704` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 95397523704 |
| `95666346768` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 95666346768 |
| `96336781704` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 96336781704 |
| `96354194734` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 96354194734 |
| `98161814791` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 98161814791 |
| `98544993753` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 98544993753 |
| `98638424787` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 98638424787 |
| `98718045715` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 98718045715 |
| `98840517715` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 98840517715 |
| `99030632704` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 99030632704 |
| `99895927720` |  | buscar_recibo \| Nenhum S-1210 com nrRecibo encontrado no ZIP para CPF 99895927720 |
