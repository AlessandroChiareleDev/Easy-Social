# COMO FAZER LOTE 3 (S-1210 retificação com planSaude)

> **Arquivo vivo.** Atualizar sempre que descobrir algo novo ou um ponto estiver errado. Histórico no final.

Última atualização: 2026-04-23 (PC2 Copilot, pós PC1-14)

---

## 1. Conceito do Lote 3 (fonte: frontend `RepositorioS1210PorLoteView.vue` + `S1210MissaoView.vue`)

- **Lote 1** — CPFs sem operadora na aba "Operadoras" do XLSX → S-1210 retif **sem** `<planSaude>`.
- **Lote 2** — CPFs com operadora + rubricas com natureza correta no eSocial → S-1210 retif **com** `<planSaude>` agregado por CNPJ de operadora.
- **Lote 3** — **Mesma estrutura do Lote 2** (operadora + titular). A única diferença é que as rubricas 774/775/522 estavam com **natureza errada** no eSocial e precisaram ser reclassificadas (774→9219, 775→outros descontos, 522→plano coletivo empresarial). Enquanto a reclassificação não está vigente, o lote fica bloqueado.
- **Lote 4** — manuais.

Rubricas típicas de saúde (Lote 2/3): 516, 605, 607, 619, 631, 638, 774, 775. Ignorar 9279/9281 (informativas).

**Regra chave:** o valor de `<planSaude>` é agregado por CNPJ de operadora, somando as rubricas de saúde daquele CPF. Rubrica 774 no Lote 3 **é plano de saúde** (tem valor mas entra dentro do bloco `<planSaude>` agregado, não é soma bruta de "rubricas + plano").

---

## 2. O que NÃO fazer (lições do PC1-13)

Cortar toda camada offline. Não codar:
- gerador XML S-3000 offline
- assinador standalone
- mini-CLI `enviar_retif.py --dry-run`
- gerador offline próprio pro Lote 3

O endpoint `POST /api/s1210-repo/enviar-lote-cpfs` em `python-scripts/esocial/s1210_repo_routes.py` (linha ~1485) já faz tudo: lê S-1210 original, copia `info_pgtos`, seta `indRetif=2`, aplica chain walk ou `recibo_override_por_cpf`, monta `<planSaude>` via `plan_saude_por_cpf` ou tabela `s1210_operadoras`, assina, envia prod, pollaa e grava em `s1210_cpf_envios`. Aceita até 50 CPFs por POST num só `envioLoteEventos`.

---

## 3. Payload do endpoint `/api/s1210-repo/enviar-lote-cpfs`

```jsonc
{
  "per_apur": "2025-05",
  "lote_num": 3,
  "cpfs": ["12345678900"],
  "confirmar_producao": true,

  // OPCIONAL — 1 item por cnpjOper. Se omitir, backend busca em s1210_operadoras.
  "plan_saude_por_cpf": {
    "12345678900": [
      {
        "cnpjOper": "00000000000000",   // 14 dígitos
        "regANS":   "123456",
        "vlrSaudeTit": 250.00,
        "infoDepSau": [                  // opcional
          { "vlrSaudeDep": 80.00, "cpfDep": "..." }
        ]
      }
    ]
  },

  // OPCIONAL — força recibo ativo. Se omitir, chain walk do backend.
  "recibo_override_por_cpf": {
    "12345678900": "1.1.0000000040123456789"
  }
}
```

**Regras de `plan_saude_por_cpf`:**
- 1 item por `cnpjOper` distinto. Se CPF tem 2 operadoras → 2 itens.
- Se CPF tem 774 + 775 **mesma operadora** → 1 item, somando em `vlrSaudeTit`.
- 774/775 **operadoras diferentes** → 2 itens.
- `infoDepSau` só preencher se tem dependente no plano.
- S-1210 NÃO tem `detOper`/`detPlano` (isso é S-2200/S-2205).

**Valor a usar em `vlrSaudeTit`:** coluna `valor_plano` da planilha da Ana (valor efetivo do desconto). Não é necessariamente o `ValorEvento` da rubrica 775 crua — em alguns casos difere (reajuste retroativo, subsídio). Validar sempre.

---

## 4. Fontes de dados

### XLSX do lote (o que o usuário tem em `Downloads/`)
- `05 Maio_lote 003_APPA.xlsx` → 1.320 CPFs em aba `Lote Para Envio`, 2.469 em `Assistencia Medica` com `CodigoEvento=775`, `"2. Odontologica"`, `ValorEvento`, `TotalVen/Des`, `Sindicato=SINDEEPRES`, `Competencia=202504` (ruído — envio é `2025-05`).
- **Esse XLSX NÃO tem CNPJ/regANS da operadora.** Não é a fonte do `plan_saude_por_cpf`.

### XLSX da Ana (formato correto para `plan_saude_por_cpf`)
- Formato `Lote3_Erros_... codigo ans + cnpj de mes N.xlsx`.
- Pequeno (~10-60 linhas normalmente, só CPFs que deram erro).
- Colunas: CPF, recibo ativo, cnpj_operadora, reg_ans, valor_plano, categoria.
- **No Fev/Mar do APPA, o PC1 pediu esse XLSX e montou o payload a partir dele.** Não há automação que gere isso sozinho.

### Tabela `s1210_operadoras` (alternativa)
- Se populada por `(per_apur, cpf, lote_num)`, o backend monta `plan_saude` sozinho via `_buscar_plan_saude_por_cpf()` em `s1210_missao_routes.py:708`.
- Colunas: `per_apur, cpf, lote_num, cnpj_operadora, reg_ans, valor (centavos)`.
- **Checar antes de pedir XLSX pra Ana:**
  ```sql
  SELECT COUNT(*) FROM s1210_operadoras
   WHERE per_apur='2025-05' AND lote_num=3;
  ```

### ZIP `29429551-maio.zip`
- 502 MB em `C:\Users\NITRO\Downloads\`.
- Código de download/protocolo (não CNPJ).
- Usado pelo backend para localizar o S-1210 original de cada CPF e extrair `info_pgtos` + `nrRecibo`.
- Mesmo formato do ZIP do Lote 1 Maio (`29105250 Mai2025.zip`).

---

## 5. Roteiro de execução (PC1-14)

Disciplina obrigatória: **1 → 10 → 50 → resto**.

### Passo 0 — Pré-check (economiza turno)
```sql
SELECT COUNT(*) FROM s1210_operadoras WHERE per_apur='2025-05' AND lote_num=3;
SELECT COUNT(*) FROM s1210_cpf_scope  WHERE per_apur='2025-05' AND lote_num=3 AND empresa_id=1;
```
- Se `s1210_operadoras > 0` → pode rodar sem `plan_saude_por_cpf` (backend agrega).
- Se `s1210_cpf_scope = 0` → precisa popular scope antes (upload do XLSX do lote pela UI ou via endpoint).

### Passo 1 — 1 CPF sem overrides
```python
r = requests.post(
    "http://localhost:8000/api/s1210-repo/enviar-lote-cpfs",
    json={
        "per_apur": "2025-05",
        "lote_num": 3,
        "cpfs": [cpf],
        "confirmar_producao": True,
    },
    timeout=180,
)
det = r.json()["resultados"][0]
print(det.get("sucesso"), det.get("codigo_resposta"), det.get("descricao_resposta"))
```

### Passo 2 — Interpretar resposta
| Código | Significado | Ação |
|---|---|---|
| `cdResp=201` sucesso | Chain walk ok, natureza ok, reabertura ok | Escala 10 → 50 → resto |
| `ocorr=620` folha fechada | Falta S-1298 reabertura Maio p/ empresa | Reabrir com S-1298, depois retomar |
| `ocorr=459` recibo não ativo | Chain walk desatualizado | Próximo CPF com `recibo_override_por_cpf` (pedir pra Ana a lista) |
| `ocorr=861` planSaude obrigatória | `plan_saude_por_cpf` vazio ou `s1210_operadoras` sem dados | Rodar com `plan_saude_por_cpf` preenchido (XLSX da Ana) |
| `ocorr=8` natureza/rubrica | S-1010 reclass não vigente | **PARAR.** Enviar S-1010 correção, esperar processar, retomar |
| `ocorr=1089` duplicado | Envios em paralelo | Ir por POST único de até 50 CPFs (sem threads) |
| outro | Chamar PC1 com `codigo_resposta` + `descricao_resposta` | — |

### Passo 3 — Escalar
- 10 CPFs (1 POST único, lista de 10)
- 50 CPFs (1 POST único, lista de 50 — o eSocial aceita batch assim)
- Resto em loop de POSTs de 50 em 50

### Passo 4 — Monitorar
```sql
WITH lv AS (
  SELECT DISTINCT ON (cpf) cpf, status
  FROM s1210_cpf_envios
  WHERE empresa_id=1 AND per_apur='2025-05' AND lote_num=3
  ORDER BY cpf, enviado_em DESC NULLS LAST
)
SELECT
  COUNT(*) FILTER (WHERE lv.status='ok')    AS ok,
  COUNT(*) FILTER (WHERE lv.status='erro')  AS erro,
  COUNT(*) FILTER (WHERE lv.status IS NULL) AS nunca,
  COUNT(*)                                  AS total
FROM s1210_cpf_scope s
LEFT JOIN lv ON lv.cpf = s.cpf
WHERE s.empresa_id=1 AND s.per_apur='2025-05' AND s.lote_num=3;
```

---

## 6. Bugs conhecidos / pegadinhas (PC1-13)

- **Backend sem `--reload`**: `bot_api.py:199` sobe sem reload. Mudanças em `esocial/*` só valem após restart (~5s downtime).
- **View `v_s1210_contadores` pode divergir** do endpoint `/por-lote/{lote}/{per}`. Usar query DISTINCT ON por `enviado_em DESC NULLS LAST` pra status real.
- **PowerShell 5.1 cp1252**: não colocar acento em `print()`. Forçar `sys.stdout.reconfigure(encoding="utf-8")` no topo.
- **PowerShell não tem `&&`**: usar `;` para encadear.

---

## 7. Estado atual (Lote 3 APPA, empresa_id=1)

Fonte: `v_s1210_contadores` em 2026-04-23.

| per_apur | total | ok | erro | status |
|---|---:|---:|---:|---|
| 2025-02 | 737 | 737 | 0 | **100% ✅ fechado** (PC1 hoje, via `plan_saude_por_cpf`) |
| 2025-03 | 1.624 | 1.620 | 4 | **99,7% ✅ fechado** (PC1 hoje, via `recibo_override_por_cpf`; 4 "sem S-1210 no ZIP" NAO_ENVIAR) |
| 2025-04 | 1.498 | 1.432 | 66 | pendente |
| 2025-05 | — | — | — | **alvo atual** |
| 2025-06 | — | — | — | próximo |
| 2025-07 | — | — | — | próximo |

Scripts de referência (ver, não copiar cegamente):
- `python-scripts/_reenvio_fev_plansaude.py` (template `plan_saude_por_cpf`)
- `python-scripts/_reenvio_mar_recibo.py` (template `recibo_override_por_cpf`)
- `python-scripts/esocial/s1210_repo_routes.py:1485` (endpoint)
- `python-scripts/esocial/s1210_missao_routes.py:708` (`_buscar_plan_saude_por_cpf`)
- `python-scripts/esocial/xml_s1210.py:49` (schema planSaude)

---

## 8. Pendências / perguntas em aberto

1. **XLSX da Ana "codigo ans + cnpj" para Maio/2025 Lote 3** — não recebido. Se `s1210_operadoras` estiver vazia pra 2025-05 Lote 3, vai cair em `ocorr=861` e precisa desse XLSX.
2. **Reclass S-1010 774/775/522 vigente em 2025-05?** — só o 1º CPF teste revela.
3. **S-1298 Maio Lote 3** — o recibo `1.1.0000000040151897705` (usado no Lote 1 Maio) vale? Só o 1º CPF revela (se `ocorr=620`, precisa reabrir).
4. **Competência 202504 no XLSX vs envio `2025-05`** — confirmar com 1º CPF (se o eSocial aceitar, é 2025-05 mesmo).

---

## 9. Histórico de correções

- **2026-04-23 (pós PC1-14):** criação inicial. Baseado em PC1-11, PC1-13, PC1-14 e exploração do frontend (`RepositorioS1210PorLoteView.vue`, `S1210MissaoView.vue`) + backend (`s1210_missao_routes.py`, `s1210_repo_routes.py`).
- **2026-04-23:** correção de erro conceitual do PC2. Antes pensava que "774 soma por fora do planSaude" e que era preciso `DELETE` em `s1210_cpf_scope` para dedup entre lotes. Errado: 774 é rubrica de plano de saúde e entra agregada em `vlrSaudeTit`; dedup entre lotes é resolvido pelo próprio eSocial via `indRetif=2` + recibo ativo (último envio prevalece).
