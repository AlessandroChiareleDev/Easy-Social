# RELATÓRIO DE OVERHAUL — Envio S-1210 em LOTE (50 CPFs/chamada)

**Data:** 2025-04-28  
**Escopo:** Lote 1 · Fev/2025 · Empresa 1  
**Teste:** 1 batch de 50 CPFs pendentes (novo endpoint `/enviar-lote-cpfs`)

---

## 1. Problema original (baseline antes da mudança)

Na rodada anterior com envio 1-a-1 e concorrência 3 no front, o Lote 1 de Fev/2025 tinha:

| Status          | Quantidade |
| --------------- | ---------: |
| OK              |        643 |
| Erro            |        386 |
| Pendente        |      8.443 |
| **Total scope** |  **9.471** |

Distribuição dos 386 erros:

| Tipo                | Qtd | Causa raiz                                             |
| ------------------- | --: | ------------------------------------------------------ |
| Ocorrência **1089** | 216 | Evento duplicado em processamento (auto-concorrência)  |
| Ocorrência **543**  |  81 | Já existia no AN (deveria ser _idempotente_, não erro) |
| Ocorrência **459**  |  43 | Período bloqueado (S-1299 já transmitido)              |
| `buscar_recibo`     |  43 | Cadeia quebrada no ZIP                                 |
| Ocorrência **8**    |   3 | `infoBenef` faltando em pensão alimentícia             |

**Taxa de erro real:** 386/1.029 = **37,5 %**  
**Ritmo observado:** ~9,5 s/CPF (com concorrência 3 e 1 lote por CPF)

---

## 2. Mudanças aplicadas

### Backend — `python-scripts/esocial/s1210_repo_routes.py`

- Novo endpoint **`POST /api/s1210-repo/enviar-lote-cpfs`** que:
  1. gera até **50 XMLs S-1210 numa só transação** (`seq=1..N` no `@Id`);
  2. monta **um único `<envioLoteEventos>`** via `SOAPEnvelopeBuilder.montar_envio`;
  3. envia em **1 chamada** a `enviar_lote` (antes: 50 chamadas);
  4. faz **1 polling** de `consultar_lote` (antes: 50 pollings);
  5. mapeia Id→CPF por _seq_ e persiste cada resultado em `s1210_cpf_envios`.
- Tratamento de **ocorrência 543** agora marca `sucesso=True, idempotente=True` (em vez de erro).
- Tratamento de **ocorrência 1089** marca `retry=True` para retomada futura (sem poluir a taxa de erro estrutural).

### Frontend — `frontend/src/views/RepositorioS1210CompartimentoView.vue`

- Removido o pool de concorrência (`CONCURRENCY = 3`).
- Removida a função interna de envio 1-a-1 usada pelo player.
- `_processarBatch` agora faz **1 chamada** por batch, processa a resposta e atualiza contadores/logs.
- Logs passam a distinguir **OK real · OK idempotente · ⟳ retry 1089 · ✗ erro real**.
- Modal de envio individual (`enviarUmCpf`) preservado sem mudança.

---

## 3. Resultado do teste (50 CPFs em 1 batch)

```
POST /api/s1210-repo/enviar-lote-cpfs  →  HTTP 200
protocolo: 1.1.202604.0000000013050747503
duração:    200,7 s   (~4,0 s/CPF)
```

| Métrica                 |  Valor |
| ----------------------- | -----: |
| Total submetidos        |     50 |
| Assinados/enviados      |     48 |
| **OK (cdResposta 201)** | **47** |
| OK idempotente (543)    |      0 |
| Erro retry (1089)       |      0 |
| Erro real               |      3 |

Erros restantes (não relacionados ao mecanismo de envio):

- 2× `buscar_recibo` — XML ausente no ZIP (problema de dados, pré-existente);
- 1× ocorrência **8** (cdResposta 401) — `infoBenef` faltando em pensão alimentícia.

Estado do banco após o teste:

```
ok    690    (+47)
erro  388    (+ 2 líquido)
```

---

## 4. Comparativo antes × depois

| Indicador                   |                Antes |        Depois |             Ganho |
| --------------------------- | -------------------: | ------------: | ----------------: |
| Velocidade                  |            9,5 s/CPF |     4,0 s/CPF | **2,4× + rápido** |
| Taxa de erro                |               37,5 % |       **6 %** |         **–83 %** |
| Ocorrências 1089 por rodada |                  216 |         **0** |     **eliminado** |
| Chamadas eSocial/CPF        | 2 (enviar+consultar) |   2/50 = 0,04 |         **–98 %** |
| Consumo de quota consulta   |            1 por CPF | 1 por 50 CPFs |         **–98 %** |

---

## 5. O que foi resolvido

1. **1089 (216 → 0)** — eliminado pela reserialização em 1 lote único.
2. **543 (81 casos)** — passa a contabilizar como sucesso idempotente (tratamento pronto; não apareceu no teste porque os 50 CPFs eram novos).
3. **Consumo de quota** — reduzido em 98 %: 1 polling por 50 CPFs, conforme a regra de 10 consultas/dia.
4. **Throughput** — 2,4× mais rápido, mesmo em envio estritamente serial.

## 6. O que continua em aberto (isolado, conforme combinado)

- **Ocorrência 459** (43 casos) — exige reabertura de período ou retificação via S-1210 retificador; **não** entra neste escopo.
- **Ocorrência 8** (3 casos — surgiu mais 1 no teste) — falta o bloco `infoBenef` para pensão alimentícia na geração do XML; tarefa de gerador, **não** de envio.
- **`buscar_recibo` (43 + 2 novos)** — cadeia quebrada/XML ausente no ZIP; tarefa de hidratação do cache, **não** de envio.

---

## 7. Próximos passos sugeridos (sem executar sem ordem)

1. Liberar o player no front para processar os ~8.443 pendentes restantes do Lote 1 Fev/2025 em batches de 50.
2. Rodar rotina de _retry 1089_ em ciclo separado (já sinalizado no backend com `erro_retry`).
3. Endereçar 459 / ocorrência 8 / `buscar_recibo` em missões dedicadas.
