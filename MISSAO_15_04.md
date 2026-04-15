# MISSÃO 15/04/2026

---

## RELATÓRIO — O QUE FOI FEITO EM RELAÇÃO À MISSÃO DE ONTEM (14/04)

### T1: PlanSaude com valor errado (~19k CPFs)

**Status: BLOQUEADO** — sem mudança. Precisamos dos dados da rubrica codIncIRRF=67 (do ZIP ou portal) para reconstruir os mapas. Não temos esses dados ainda.

### T2: Teste de retificação com recibo correto (CPF 003.864.459-23)

**Status: ✅ CONCLUÍDO COM SUCESSO**

- Script `_teste_recibo.py` criado e executado
- Retificação S-1210 ACEITA em **produção** (tpAmb=1)
- Recibo usado: `1.1.0000000039932809804` (fornecido pelo Alex)
- Recibo novo gerado: `1.1.0000000039996893181`
- Protocolo: `1.1.202604.0000000013028399496`
- **Conclusão: quando temos o recibo correto, a retificação funciona**

#### Erros que ocorreram até chegar ao sucesso (5 envios ao total):

| Envio       | Erro                            | Causa                                                               | Solução                                                   |
| ----------- | ------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------- |
| 1           | 607 — transmissor ≠ certificado | EMPREGADOR hardcoded como `63554067` (8 dígitos)                    | Usar CNPJ do certificado do banco                         |
| 2           | TypeError — ESocialClient()     | Tentei instanciar classe estática                                   | Métodos estáticos: `ESocialClient.enviar_lote()`          |
| 3           | 411 — assinante inválido        | Enviou pra homologação (URL padrão)                                 | Passar `url=SOAPEnvelopeBuilder.url_envio(producao=True)` |
| 4           | 101 → 411 — procuração          | Transmissor com CNPJ do cert (14 dig) mas empregador hardcoded APPA | empregador = transmissor = CNPJ do certificado            |
| 5 em diante | 101 — tipo de evento não aceito | `grupo="1"` no SOAP                                                 | Correto: `grupo="3"` (como pipeline_batch.py faz)         |
| **FINAL**   | **201 — Sucesso**               | Tudo alinhado com pipeline_batch                                    | empregador=cert, transmissor=cert, grupo=3, url=prod      |

### T3: PlanSaude faltando (49 Jan + 1.069 Fev)

**Status: BLOQUEADO** — depende de T1

---

## AUDITORIA DE SEGURANÇA — CERTIFICADO

Feita auditoria de segurança do projeto. Problemas encontrados:

### 🔴 Críticos

1. **Chave Fernet fallback hardcoded** em `certificate_manager.py` — se env var `SECRET_KEY` não existir, usa chave fixa no código
2. **PFX no repositório** — `python-scripts/certificados/` tem arquivos .pfx, `.gitignore` não exclui `*.pfx`
3. **Senha Supabase hardcoded** em 9 scripts (`check_dashboard.py`, `fix_dashboard.py`, `_manage_users.py`, etc.)
4. **Senha ROOT da VPS hardcoded** em `_deploy_build.py`, `_deploy_services.py`, `_check_certs.py`, `_check_logs.py`
5. **Credenciais admin hardcoded** em `_manage_users.py`

### 🟠 Altos

6. Arquivos `.env` com credenciais reais em `backend/.env` e `python-scripts/.env`
7. `.gitignore` não exclui `*.pfx`, `*.p12`, `certificados/`

### Recomendações

- Adicionar `*.pfx`, `*.p12`, `certificados/` ao `.gitignore`
- Verificar se arquivos sensíveis estão no git history
- Mover TODAS as senhas para variáveis de ambiente
- Remover fallback da chave Fernet

---

## LIÇÕES APRENDIDAS (ERROS)

Documentado em memória permanente (`/memories/repo/erros-esocial.md`). Erros registrados:

- Erro 1: `grupo="1"` → correto é `grupo="3"` para S-1210
- Erro 2: transmissor com CNPJ errado (607)
- Erro 3: URL padrão é homologação (411)
- Erro 4: ESocialClient é estático
- Erro 5: EMPREGADOR hardcoded em vez de ler do certificado

**REGRA OURO: Sempre copiar padrão do pipeline_batch.py. NUNCA inventar.**

---

## NÚMEROS DO DIA

| Métrica                            | Valor |
| ---------------------------------- | ----- |
| Envios ao eSocial (enviar_lote)    | 5     |
| Consultas de lote (consultar_lote) | ~30   |
| Downloads usados (limite 10/dia)   | **0** |
| Eventos aceitos em produção        | 1     |

---

## PRÓXIMOS PASSOS

1. **T2 expandir**: Usar ConsultarIdentificadoresEmpregador para obter recibos atualizados dos 100 Jan + 53 Fev CPFs com recibo desconhecido (gasta 1 consulta do limite de 10/dia — PRECISA AUTORIZAÇÃO)
2. **T1 desbloquear**: Obter dados da rubrica codIncIRRF=67 do ZIP original ou portal para reconstruir mapas planSaude
3. **Segurança**: Corrigir os problemas críticos de segurança (PFX no repo, senhas hardcoded, etc.)
4. **T3**: Resolver planSaude faltando depois que T1 for desbloqueado
