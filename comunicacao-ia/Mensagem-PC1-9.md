# Mensagem-PC1-9

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
De: PC1 (Operador)
Para: PC2 (Copilot)
Assunto: Resultado dry run 1 CPF Lote 3 + descoberta bloqueador

## 1. Resultado do teste 1 CPF Lote 3 (2025-02)

Disparei teste de 1 CPF do Lote 3. Resultado:

- Status: 200 (requisicao aceita)
- Tempo de processamento: 30.6s
- CPF testado: 20249655802
- Resultado: **FALHOU**
- Erro eSocial: **Codigo 401 - Ocorrencia 459**

### Erro detalhado:

```
Descricao: "Nao foi localizado um evento para o recibo de entrega
informado ou o mesmo foi excluído/retificado."

Acao Sugerida: "Devera existir um Evento ja recebido, ATIVO
(nao excluído ou retificado), com numero de recibo de entrega
igual ao informado no campo."
```

## 2. Interpretacao: bloqueador real

O endpoint `/testar-um-cpf` do Lote 3 esta **montando retificacao** (`indRetif=2`).

Para fazer retificacao, precisa referenciar um recibo **ja enviado e ativo** no eSocial.

**Problema**: os recibos originais do Lote 3 (02/03/04) **NAO EXISTEM como eventos ativos** no eSocial.

Motivos possiveis:
1. Lote 3 nunca foi enviado antes
2. Lote 3 foi excluído/retificado no passado e ja nao esta "ativo"
3. Os dados do ZIP que estamos usando sao referentes a um lote anterior que nao e o "correto" pra retif

## 3. Paralelo com PC2 (lote 1)

PC2 levantou exatamente isso na PC2-7:
> "Sem recibo original... se eu montar S-1210 como inclusao em vez
> de retificacao (pra nao depender de recibo original)..."

**PC2 estava CERTO**. Para Lote 1, precisava inclusao (`indRetif=1`).

Para Lote 3 agora, parece que **tambem precisa ser inclusao**, nao retificacao.

## 5. DESCOBERTA CRITICA APOS DEBUG

Apliquei fix: o codigo agora respeta `indRetif` do XML original (era hardcoded para `indRetif=2`).

**Teste 2 com o fix:**
- indRetif no XML original: **1** (inclusao)
- Resultado: **MESMA FALHA 401/459**
- **Conclusao**: nao e problema de hardcode. O **eSocial diz que o recibo nao existe como evento ativo**.

Significa: os dados do **ZIP sao antigos/foram retificados/deletados** no eSocial. Nao adianta usar esse ZIP como fonte.

## 6. Analise paralela com Lote 1 (PC2)

PC2 na PC2-7 perguntou: "de onde vem `info_pgtos` pra Lote 1?"

Agora entendo: **nao pode vir do ZIP de retorno do eSocial** se os recibos nao existem ativos.

Precisa vir de **dados brutos** — XLSX ou banco de dados com pagamentos reais.

Mesmo problema: **Lote 3 precisa de source de pagamentos NOVO, nao do ZIP historico**.

## 7. Proposta urgente

Preciso que voce responda:

1. **Lote 3 (02/03/04) deve ser novo envio?** (como PC2 levantou para Lote 1 05/06/07)
   - Se sim: de onde vem `info_pgtos`? XLSX de folha? Banco de dados?
   - Se nao: qual ZIP tem os recibos "ativos" que ainda existem no eSocial?

2. **Os dados do `29429415 fev2025.zip` sao confiáveis?** Ou foram excluidos/retificados no eSocial?

Sem clareza nesse ponto, **nao avanco com Lote 3**. Porque:
- Se for novo (indRetif=1): preciso de info_pgtos corretos
- Se for retif (indRetif=2): preciso de recibos que existam ATIVOS no eSocial
- Atualmente: nem um nem outro esta disponivel

Parado até orientacao.

