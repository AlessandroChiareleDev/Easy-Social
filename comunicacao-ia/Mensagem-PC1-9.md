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

## 4. Proximos passos

Preciso investigar:

1. Os dados do ZIP de Fevereiro (29429415 fev2025.zip) sao mesmo do **Lote 3** ou sao reliquias de outro lote/mes?
2. Se for Lote 3 original: deve ser `indRetif=1` (inclusao), nao `indRetif=2` (retif).
3. Se estou errando na leitura do ZIP: qual campo indica se e inclusao ou retif?

Enquanto isso, **paralizo Lote 3** ate esclarecer. Nao vou escalar de 1 para 100 CPFs se o bloqueador e fundamental.

Aguardando orientacao ou proximos passos. Por enquanto, o endpoint **nao funciona pra retificacao** porque os recibos nao existem.
