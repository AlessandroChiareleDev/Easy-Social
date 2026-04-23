-- =====================================================================
-- Migration: Repositório S-1210 (missão APPA — 3 meses × 4 lotes)
-- Data: 2026-04-21
-- Escopo: 5 tabelas + 1 bucket de storage para XLSX oficiais da Ana
--
-- Referências:
--   docs/MISSAO_S1210_APPA_21-04-2026/MISSAO_VISUALIZACAO_COMPLETA_21-04-2026.md
--   docs/MISSAO_S1210_APPA_21-04-2026/NORTE_S1210.md
--
-- Princípios:
--   - Nada mexe em pipeline_runs / pipeline_cpf_results (histórico antigo).
--   - XLSX oficiais moram no Supabase Storage (bucket privado).
--   - ZIPs NÃO entram no banco (streaming de Downloads).
--   - Tudo escopado por empresa_id + per_apur para suportar outras empresas no futuro.
-- =====================================================================

-- ────────────────────────────────────────────────────────────────────
-- 1. s1210_xlsx — planilha oficial da Ana, 1 linha por (empresa, mês)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.s1210_xlsx (
    id              BIGSERIAL PRIMARY KEY,
    empresa_id      INTEGER         NOT NULL,              -- FK lógica → master_empresas.id
    per_apur        VARCHAR(7)      NOT NULL,              -- '2025-02'
    nome_arquivo    VARCHAR(255)    NOT NULL,              -- '02. Fevereiro_2025_APPA certa.xlsx'
    tamanho_bytes   BIGINT          NOT NULL,
    sha256          CHAR(64)        NOT NULL,              -- hex do hash para detectar versão
    storage_path    TEXT            NOT NULL,              -- caminho no bucket (ex: 'appa/2025-02/v1.xlsx')
    aba_geral       VARCHAR(100)    NOT NULL,              -- ex: 'Geral Para Envio_Lotes'
    aba_operadoras  VARCHAR(100),                          -- ex: 'Operadoras_012025'
    uploaded_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    uploaded_by     INTEGER,                                  -- FK lógica → master_usuarios.id
    parse_ok        BOOLEAN         NOT NULL DEFAULT FALSE,
    parse_erro      TEXT,
    totais_json     JSONB,                                 -- {"1_LOTE":9471,"2_LOTE":1390,"3_LOTE":737,"4_LOTE":2}
    UNIQUE (empresa_id, per_apur, sha256)                  -- mesma versão não duplica
);
COMMENT ON TABLE public.s1210_xlsx IS
    'XLSX oficial da Ana ingerido no sistema. Cada linha = 1 versão de 1 arquivo de 1 mês.';

CREATE INDEX IF NOT EXISTS ix_s1210_xlsx_empresa_per
    ON public.s1210_xlsx (empresa_id, per_apur);


-- ────────────────────────────────────────────────────────────────────
-- 2. s1210_cpf_scope — escopo (CPFs × lote × mês) extraído da aba Geral
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.s1210_cpf_scope (
    id              BIGSERIAL PRIMARY KEY,
    xlsx_id         BIGINT          NOT NULL REFERENCES public.s1210_xlsx(id) ON DELETE CASCADE,
    empresa_id      INTEGER         NOT NULL,
    per_apur        VARCHAR(7)      NOT NULL,
    cpf             CHAR(11)        NOT NULL,
    nome            VARCHAR(255),
    matricula       VARCHAR(50),
    lote_num        SMALLINT        NOT NULL CHECK (lote_num BETWEEN 1 AND 4),
    row_number      INTEGER,                               -- linha original no XLSX (auditoria)
    raw_row         JSONB,                                 -- dump bruto da linha, para re-parse
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (empresa_id, per_apur, cpf)                     -- 1 CPF em 1 único lote por mês
);
COMMENT ON TABLE public.s1210_cpf_scope IS
    'Escopo de CPFs da missão: quem está em qual lote em qual mês (vindo da aba Geral da XLSX).';

CREATE INDEX IF NOT EXISTS ix_s1210_scope_empresa_per_lote
    ON public.s1210_cpf_scope (empresa_id, per_apur, lote_num);
CREATE INDEX IF NOT EXISTS ix_s1210_scope_cpf
    ON public.s1210_cpf_scope (cpf);


-- ────────────────────────────────────────────────────────────────────
-- 3. s1210_operadoras — mapa CPF × rubrica × operadora (lotes 2 e 3)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.s1210_operadoras (
    id              BIGSERIAL PRIMARY KEY,
    xlsx_id         BIGINT          NOT NULL REFERENCES public.s1210_xlsx(id) ON DELETE CASCADE,
    empresa_id      INTEGER         NOT NULL,
    per_apur        VARCHAR(7)      NOT NULL,
    cpf             CHAR(11)        NOT NULL,
    rubrica_origem  VARCHAR(10)     NOT NULL,              -- '774' ou '775' (apenas essas duas têm relevância aqui)
    cnpj_operadora  VARCHAR(14),
    reg_ans         VARCHAR(20),
    nome_operadora  VARCHAR(255),
    valor           NUMERIC(18, 2),
    raw_row         JSONB,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (empresa_id, per_apur, cpf, rubrica_origem)
);
COMMENT ON TABLE public.s1210_operadoras IS
    'Mapa de operadora de plano/odonto por CPF e rubrica. Usado só nos lotes 2 (775) e 3 (774).';

CREATE INDEX IF NOT EXISTS ix_s1210_operadoras_key
    ON public.s1210_operadoras (empresa_id, per_apur, cpf);


-- ────────────────────────────────────────────────────────────────────
-- 4. s1210_cpf_recibo — cache do último recibo conhecido (chain walk no ZIP)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.s1210_cpf_recibo (
    id                   BIGSERIAL PRIMARY KEY,
    empresa_id           INTEGER         NOT NULL,
    per_apur             VARCHAR(7)      NOT NULL,
    cpf                  CHAR(11)        NOT NULL,
    nr_recibo_zip        VARCHAR(50),                      -- o que estava no ZIP de download
    nr_recibo_usado      VARCHAR(50),                      -- escolhido pela chain walk (ideDmDev) na hora do envio
    nr_recibo_eSocial    VARCHAR(50),                      -- confirmado por ConsultarIdentificadores (se rodado)
    ide_dm_dev           VARCHAR(100),
    dh_processamento_zip TIMESTAMPTZ,
    fonte                VARCHAR(30)     NOT NULL DEFAULT 'zip',  -- 'zip' | 'chain_walk' | 'eSocial'
    atualizado_em        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (empresa_id, per_apur, cpf)
);
COMMENT ON TABLE public.s1210_cpf_recibo IS
    'Último recibo S-1210 conhecido por CPF/mês. Origem: ZIP ou consulta ao eSocial.';

CREATE INDEX IF NOT EXISTS ix_s1210_recibo_empresa_per
    ON public.s1210_cpf_recibo (empresa_id, per_apur);


-- ────────────────────────────────────────────────────────────────────
-- 5. s1210_cpf_envios — histórico de envios feitos PELA tela nova
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.s1210_cpf_envios (
    id                   BIGSERIAL PRIMARY KEY,
    empresa_id           INTEGER         NOT NULL,
    per_apur             VARCHAR(7)      NOT NULL,
    cpf                  CHAR(11)        NOT NULL,
    lote_num             SMALLINT        NOT NULL CHECK (lote_num BETWEEN 1 AND 4),
    status               VARCHAR(20)     NOT NULL,         -- 'enviando'|'ok'|'erro'|'pendente'
    nr_recibo_usado      VARCHAR(50),                      -- recibo do S-1210 referenciado
    nr_recibo_novo       VARCHAR(50),                      -- recibo devolvido pelo eSocial
    protocolo            VARCHAR(100),                     -- nrProtoEnvio
    codigo_resposta      VARCHAR(10),                      -- '201', '202', ...
    descricao_resposta   TEXT,
    erro_descricao       TEXT,
    xml_enviado          TEXT,                             -- XML assinado (gzip seria ideal, por ora texto)
    xml_resposta         TEXT,
    pagamentos           JSONB,                            -- snapshot detPgtos usado
    info_ir              JSONB,                            -- snapshot infoIRComplem usado
    enviado_por          INTEGER,
    enviado_em           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    duracao_ms           INTEGER
);
COMMENT ON TABLE public.s1210_cpf_envios IS
    'Histórico completo de envios S-1210 feitos pela tela nova (missão 21/04/2026). Não inclui pipeline antigo.';

CREATE INDEX IF NOT EXISTS ix_s1210_envios_cpf
    ON public.s1210_cpf_envios (empresa_id, per_apur, cpf);
CREATE INDEX IF NOT EXISTS ix_s1210_envios_status
    ON public.s1210_cpf_envios (empresa_id, per_apur, lote_num, status);
CREATE INDEX IF NOT EXISTS ix_s1210_envios_enviado_em
    ON public.s1210_cpf_envios (enviado_em DESC);


-- ────────────────────────────────────────────────────────────────────
-- 6. View agregada — contadores para a tela (Vertente A e B)
-- ────────────────────────────────────────────────────────────────────
-- Para cada (empresa_id, per_apur, lote_num):
--   total    = CPFs no escopo (XLSX)
--   ok       = CPFs cujo último envio foi status='ok'
--   erro     = CPFs cujo último envio foi status='erro'
--   enviando = CPFs cujo último envio foi status='enviando'
--   pend     = total - (ok + erro + enviando)
CREATE OR REPLACE VIEW public.v_s1210_contadores AS
WITH ult AS (
    SELECT DISTINCT ON (empresa_id, per_apur, cpf)
           empresa_id, per_apur, cpf, lote_num, status
      FROM public.s1210_cpf_envios
     ORDER BY empresa_id, per_apur, cpf, enviado_em DESC
)
SELECT s.empresa_id,
       s.per_apur,
       s.lote_num,
       COUNT(*)                                                                          AS total,
       COUNT(*) FILTER (WHERE u.status = 'ok')                                           AS ok,
       COUNT(*) FILTER (WHERE u.status = 'erro')                                         AS erro,
       COUNT(*) FILTER (WHERE u.status = 'enviando')                                     AS enviando,
       COUNT(*) FILTER (WHERE u.status IS NULL OR u.status NOT IN ('ok','erro','enviando')) AS pendente
  FROM public.s1210_cpf_scope s
  LEFT JOIN ult u
         ON u.empresa_id = s.empresa_id
        AND u.per_apur   = s.per_apur
        AND u.cpf        = s.cpf
 GROUP BY s.empresa_id, s.per_apur, s.lote_num;

COMMENT ON VIEW public.v_s1210_contadores IS
    'Contadores por (empresa,per_apur,lote_num) — fonte única dos números mostrados na tela.';


-- ────────────────────────────────────────────────────────────────────
-- 7. Bucket de storage (Supabase) — criação idempotente
-- ────────────────────────────────────────────────────────────────────
-- O bucket fica privado; upload/download via endpoints do backend com service role.
INSERT INTO storage.buckets (id, name, public)
VALUES ('s1210-xlsx', 's1210-xlsx', false)
ON CONFLICT (id) DO NOTHING;
