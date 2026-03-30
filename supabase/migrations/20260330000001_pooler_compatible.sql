-- =============================================================================
-- Easy Social — Migration Supabase (Pooler-Compatible)
-- =============================================================================
-- Adaptações:
--   1. Sem CREATE SCHEMA master → usamos prefixo master_ no schema public
--   2. Sem REFERENCES auth.users → perfis.id é uuid PK (vincular via dashboard)
--   3. Sem certificados_a1 nem senha_certificado_salva (ficam LOCAL)
--   4. Todos timestamps → timestamptz
-- =============================================================================

-- =====================
-- TABELAS MASTER (prefixo master_)
-- =====================

CREATE TABLE public.master_empresas (
    id serial PRIMARY KEY,
    nome varchar(255) NOT NULL,
    cnpj varchar(18) UNIQUE,
    db_name varchar(100) NOT NULL UNIQUE,
    db_host varchar(255) DEFAULT 'localhost',
    db_port integer DEFAULT 5432,
    ativo boolean DEFAULT true,
    criado_em timestamptz DEFAULT now()
);

CREATE TABLE public.master_perfis (
    id uuid PRIMARY KEY,
    email varchar(255) NOT NULL UNIQUE,
    nome varchar(255) NOT NULL,
    username varchar(100) UNIQUE,
    role varchar(20) DEFAULT 'operador' CHECK (role IN ('admin', 'operador')),
    ativo boolean DEFAULT true,
    criado_em timestamptz DEFAULT now(),
    atualizado_em timestamptz DEFAULT now()
);

CREATE TABLE public.master_usuario_empresa (
    id serial PRIMARY KEY,
    usuario_id uuid REFERENCES public.master_perfis(id) ON DELETE CASCADE,
    empresa_id integer REFERENCES public.master_empresas(id) ON DELETE CASCADE,
    role_emp varchar(20) DEFAULT 'operador' CHECK (role_emp IN ('admin', 'operador')),
    criado_em timestamptz DEFAULT now(),
    UNIQUE(usuario_id, empresa_id)
);

CREATE TABLE public.master_naturezas_esocial (
    id serial PRIMARY KEY,
    codigo varchar(10) NOT NULL UNIQUE,
    nome varchar(500) NOT NULL,
    descricao text,
    data_inicio date,
    data_fim date,
    criado_em timestamptz DEFAULT now()
);

-- =====================
-- TABELAS PUBLIC (dados da empresa)
-- =====================

CREATE TABLE public.uploads (
    id serial PRIMARY KEY,
    file_name varchar(500) NOT NULL,
    original_name varchar(500),
    file_size bigint NOT NULL,
    upload_date timestamptz DEFAULT now(),
    status varchar(50) DEFAULT 'pendente',
    sheets_processed integer DEFAULT 0,
    analysis_data jsonb,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_uploads_status ON public.uploads(status);

CREATE TABLE public.analise_natureza (
    id serial PRIMARY KEY,
    upload_id integer REFERENCES public.uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now(),
    natureza_anterior text,
    natureza_nova text,
    usuario_correcao varchar(255),
    data_correcao timestamptz,
    col_k varchar(255), col_l varchar(255), col_m varchar(255), col_n varchar(255),
    col_o varchar(255), col_p varchar(255), col_q varchar(255), col_r varchar(255),
    col_s varchar(255), col_t varchar(255), col_u varchar(255), col_v varchar(255),
    col_w varchar(255), col_x varchar(255), col_y varchar(255), col_z varchar(255),
    col_aa varchar(255), col_ab varchar(255), col_ac varchar(255), col_ad varchar(255),
    col_ae varchar(255), col_af varchar(255), col_ag varchar(255), col_ah varchar(255),
    col_ai varchar(255), col_aj varchar(255), col_ak varchar(255), col_al varchar(255),
    col_am varchar(255), col_an varchar(255), col_ao varchar(255), col_ap varchar(255),
    col_aq varchar(255), col_ar varchar(255), col_as varchar(255), col_at varchar(255),
    col_au varchar(255), col_av varchar(255), col_aw varchar(255), col_ax varchar(255),
    col_ay varchar(255), col_az varchar(255), col_ba varchar(255), col_bb varchar(255)
);
CREATE INDEX idx_analise_natureza_upload ON public.analise_natureza(upload_id);

CREATE TABLE public.analise_natureza_certo (
    id integer,
    upload_id integer,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz,
    natureza_anterior text,
    natureza_nova text,
    usuario_correcao varchar(255),
    data_correcao timestamptz,
    col_k varchar(255), col_l varchar(255), col_m varchar(255), col_n varchar(255),
    col_o varchar(255), col_p varchar(255), col_q varchar(255), col_r varchar(255),
    col_s varchar(255), col_t varchar(255), col_u varchar(255), col_v varchar(255),
    col_w varchar(255), col_x varchar(255), col_y varchar(255), col_z varchar(255),
    col_aa varchar(255), col_ab varchar(255), col_ac varchar(255), col_ad varchar(255),
    col_ae varchar(255), col_af varchar(255), col_ag varchar(255), col_ah varchar(255),
    col_ai varchar(255), col_aj varchar(255), col_ak varchar(255), col_al varchar(255),
    col_am varchar(255), col_an varchar(255), col_ao varchar(255), col_ap varchar(255),
    col_aq varchar(255), col_ar varchar(255), col_as varchar(255), col_at varchar(255),
    col_au varchar(255), col_av varchar(255), col_aw varchar(255), col_ax varchar(255),
    col_ay varchar(255), col_az varchar(255), col_ba varchar(255), col_bb varchar(255)
);

CREATE TABLE public.auditoria_naturezas (
    id serial PRIMARY KEY,
    analise_natureza_id integer REFERENCES public.analise_natureza(id),
    codigoevento varchar(255),
    natureza_anterior text,
    natureza_nova text,
    usuario varchar(255) DEFAULT 'sistema',
    data_alteracao timestamptz DEFAULT now(),
    motivo text
);
CREATE INDEX idx_auditoria_naturezas_an ON public.auditoria_naturezas(analise_natureza_id);

CREATE TABLE public.base_ficha_financeira (
    id serial PRIMARY KEY,
    upload_id integer REFERENCES public.uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    col_k text, col_l text, col_m text, col_n text, col_o text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_base_ficha_upload ON public.base_ficha_financeira(upload_id);

-- NOTA: certificados_a1 NAO migra (fica local)
-- NOTA: senha_certificado_salva NAO migra (fica local)

CREATE TABLE public.config_esocial (
    id serial PRIMARY KEY,
    cnpj varchar(20) NOT NULL UNIQUE,
    ini_valid_padrao varchar(10),
    auto_detected boolean DEFAULT false,
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE public.correcoes_staging (
    id serial PRIMARY KEY,
    analise_natureza_id integer NOT NULL UNIQUE REFERENCES public.analise_natureza(id),
    codigoevento varchar(20) NOT NULL,
    nome_evento varchar(500),
    natureza_anterior varchar(500),
    natureza_nova_codigo varchar(20) NOT NULL,
    natureza_nova_nome varchar(500) NOT NULL,
    motivo text DEFAULT '',
    usuario_id integer,
    usuario_nome varchar(200) DEFAULT 'sistema',
    status varchar(20) DEFAULT 'pendente',
    criado_em timestamptz DEFAULT now(),
    aplicado_em timestamptz
);

CREATE TABLE public.cruzamento_eb (
    id serial PRIMARY KEY,
    cod_rubrica varchar(20) NOT NULL,
    descricao text NOT NULL,
    cod_natureza text,
    incid_inss varchar(10),
    incid_irrf varchar(10),
    incid_fgts varchar(10),
    analise text,
    incid_base_legal_inss text,
    incid_base_legal_irrf text,
    incid_base_legal_fgts text,
    importado_em timestamptz DEFAULT now(),
    corrigido boolean DEFAULT false,
    corrigido_em timestamptz,
    envio_status varchar(20) DEFAULT 'pendente',
    ini_valid_esocial varchar(10)
);

CREATE TABLE public.cruzamento_uploads (
    id serial PRIMARY KEY,
    filename varchar(500) NOT NULL,
    original_name varchar(500) NOT NULL,
    file_size bigint NOT NULL,
    upload_date timestamptz DEFAULT now(),
    sheet_count integer DEFAULT 0,
    sheet_names text[]
);

CREATE TABLE public.cruzamento_resultado (
    id serial PRIMARY KEY,
    cruzamento_upload_id integer REFERENCES public.cruzamento_uploads(id) ON DELETE CASCADE,
    codigo text,
    nome_evento text,
    natureza_esocial text,
    cod_fgts text,
    cod_inss text,
    cod_irrf text,
    row_number integer,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.cruzamento_tabela_a (
    id serial PRIMARY KEY,
    cruzamento_upload_id integer REFERENCES public.cruzamento_uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    col_k text, col_l text, col_m text, col_n text, col_o text,
    col_p text, col_q text, col_r text, col_s text, col_t text,
    col_u text, col_v text, col_w text, col_x text, col_y text,
    col_z text, col_aa text, col_ab text, col_ac text, col_ad text,
    col_ae text, col_af text, col_ag text, col_ah text, col_ai text,
    col_aj text, col_ak text, col_al text, col_am text, col_an text,
    col_ao text, col_ap text, col_aq text, col_ar text, col_as text,
    col_at text, col_au text, col_av text, col_aw text, col_ax text,
    col_ay text, col_az text, col_ba text, col_bb text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.cruzamento_tabela_b (
    id serial PRIMARY KEY,
    cruzamento_upload_id integer REFERENCES public.cruzamento_uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    col_k text, col_l text, col_m text, col_n text, col_o text,
    col_p text, col_q text, col_r text, col_s text, col_t text,
    col_u text, col_v text, col_w text, col_x text, col_y text,
    col_z text, col_aa text, col_ab text, col_ac text, col_ad text,
    col_ae text, col_af text, col_ag text, col_ah text, col_ai text,
    col_aj text, col_ak text, col_al text, col_am text, col_an text,
    col_ao text, col_ap text, col_aq text, col_ar text, col_as text,
    col_at text, col_au text, col_av text, col_aw text, col_ax text,
    col_ay text, col_az text, col_ba text, col_bb text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.dinamica (
    id serial PRIMARY KEY,
    upload_id integer REFERENCES public.uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now(),
    col_k varchar(255), col_l varchar(255), col_m varchar(255), col_n varchar(255),
    col_o varchar(255), col_p varchar(255), col_q varchar(255), col_r varchar(255),
    col_s varchar(255), col_t varchar(255), col_u varchar(255), col_v varchar(255),
    col_w varchar(255), col_x varchar(255), col_y varchar(255), col_z varchar(255),
    col_aa varchar(255), col_ab varchar(255), col_ac varchar(255), col_ad varchar(255),
    col_ae varchar(255), col_af varchar(255), col_ag varchar(255), col_ah varchar(255),
    col_ai varchar(255), col_aj varchar(255), col_ak varchar(255), col_al varchar(255),
    col_am varchar(255), col_an varchar(255), col_ao varchar(255), col_ap varchar(255),
    col_aq varchar(255), col_ar varchar(255), col_as varchar(255), col_at varchar(255),
    col_au varchar(255), col_av varchar(255), col_aw varchar(255), col_ax varchar(255),
    col_ay varchar(255), col_az varchar(255), col_ba varchar(255), col_bb varchar(255)
);
CREATE INDEX idx_dinamica_upload ON public.dinamica(upload_id);

CREATE TABLE public.eb_skills_base_legal (
    id serial PRIMARY KEY,
    upload_id integer,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.esocial_depara (
    id serial PRIMARY KEY,
    cod_rubrica text NOT NULL,
    campo text NOT NULL,
    valor_anterior text,
    valor_novo text NOT NULL,
    nome_rubrica text,
    regra text DEFAULT 'manual',
    status varchar(20) DEFAULT 'pendente',
    created_at timestamptz DEFAULT now(),
    aplicado_em timestamptz,
    UNIQUE(cod_rubrica, campo)
);

CREATE TABLE public.esocial_envios (
    id serial PRIMARY KEY,
    tipo_evento varchar(10) DEFAULT 'S-1010' NOT NULL,
    modo varchar(20) DEFAULT 'alteracao' NOT NULL,
    status varchar(30) DEFAULT 'enviado' NOT NULL,
    protocolo_envio varchar(100),
    codigo_resposta varchar(10),
    descricao_resposta text,
    total_eventos integer DEFAULT 0,
    rubrica_ids jsonb,
    xml_retorno text,
    ocorrencias jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    ambiente varchar(2) DEFAULT '2' NOT NULL,
    ini_valid varchar(10),
    rubrica_detalhes jsonb,
    xml_enviado text,
    recibo_consulta jsonb
);

CREATE TABLE public.esocial_tabela3_natureza (
    codigo integer PRIMARY KEY,
    nome varchar(200) NOT NULL,
    dt_inicio date NOT NULL,
    dt_fim date,
    descricao text,
    versao integer DEFAULT 17
);

CREATE TABLE public.naturezas_esocial (
    id serial PRIMARY KEY,
    codigo varchar(10) NOT NULL UNIQUE,
    nome varchar(500) NOT NULL,
    descricao text,
    data_inicio date,
    data_fim date,
    criado_em timestamptz DEFAULT now()
);
CREATE INDEX idx_naturezas_codigo ON public.naturezas_esocial(codigo);

CREATE TABLE public.planilha_1 (
    id serial PRIMARY KEY,
    upload_id integer REFERENCES public.uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_planilha_1_upload ON public.planilha_1(upload_id);

CREATE TABLE public.rubrica_corrections (
    id serial PRIMARY KEY,
    tabela_eb_id integer,
    cod_rubrica text NOT NULL,
    descricao text,
    inss_antes text,
    irrf_antes text,
    fgts_antes text,
    inss_correto text,
    irrf_correto text,
    fgts_correto text,
    status varchar(50) DEFAULT 'pendente',
    corrigido_em timestamptz,
    observacao text,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_rubrica_corrections_status ON public.rubrica_corrections(status);

CREATE TABLE public.tabela3_esocial_oficial (
    id serial PRIMARY KEY,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text, col_f text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.tabela_cruzamento (
    id serial PRIMARY KEY,
    upload_id integer,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    col_k text, col_l text, col_m text, col_n text, col_o text,
    col_p text, col_q text, col_r text, col_s text, col_t text,
    col_u text, col_v text, col_w text, col_x text, col_y text,
    col_z text, col_aa text, col_ab text, col_ac text, col_ad text,
    col_ae text, col_af text, col_ag text, col_ah text, col_ai text,
    col_aj text, col_ak text, col_al text, col_am text, col_an text,
    col_ao text, col_ap text, col_aq text, col_ar text, col_as text,
    col_at text, col_au text, col_av text, col_aw text, col_ax text,
    col_ay text, col_az text, col_ba text, col_bb text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE public.tabela_eb (
    id serial PRIMARY KEY,
    upload_id integer REFERENCES public.uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now(),
    col_k varchar(255), col_l varchar(255), col_m varchar(255), col_n varchar(255),
    col_o varchar(255), col_p varchar(255), col_q varchar(255), col_r varchar(255),
    col_s varchar(255), col_t varchar(255), col_u varchar(255), col_v varchar(255),
    col_w varchar(255), col_x varchar(255), col_y varchar(255), col_z varchar(255),
    col_aa varchar(255), col_ab varchar(255), col_ac varchar(255), col_ad varchar(255),
    col_ae varchar(255), col_af varchar(255), col_ag varchar(255), col_ah varchar(255),
    col_ai varchar(255), col_aj varchar(255), col_ak varchar(255), col_al varchar(255),
    col_am varchar(255), col_an varchar(255), col_ao varchar(255), col_ap varchar(255),
    col_aq varchar(255), col_ar varchar(255), col_as varchar(255), col_at varchar(255),
    col_au varchar(255), col_av varchar(255), col_aw varchar(255), col_ax varchar(255),
    col_ay varchar(255), col_az varchar(255), col_ba varchar(255), col_bb varchar(255)
);
CREATE INDEX idx_tabela_eb_upload ON public.tabela_eb(upload_id);

CREATE TABLE public.tabela_eventos_gl (
    id serial PRIMARY KEY,
    upload_id integer REFERENCES public.uploads(id) ON DELETE CASCADE,
    row_number integer,
    col_a text, col_b text, col_c text, col_d text, col_e text,
    col_f text, col_g text, col_h text, col_i text, col_j text,
    raw_data jsonb,
    created_at timestamptz DEFAULT now(),
    col_k varchar(255), col_l varchar(255), col_m varchar(255), col_n varchar(255),
    col_o varchar(255), col_p varchar(255), col_q varchar(255), col_r varchar(255),
    col_s varchar(255), col_t varchar(255), col_u varchar(255), col_v varchar(255),
    col_w varchar(255), col_x varchar(255), col_y varchar(255), col_z varchar(255),
    col_aa varchar(255), col_ab varchar(255), col_ac varchar(255), col_ad varchar(255),
    col_ae varchar(255), col_af varchar(255), col_ag varchar(255), col_ah varchar(255),
    col_ai varchar(255), col_aj varchar(255), col_ak varchar(255), col_al varchar(255),
    col_am varchar(255), col_an varchar(255), col_ao varchar(255), col_ap varchar(255),
    col_aq varchar(255), col_ar varchar(255), col_as varchar(255), col_at varchar(255),
    col_au varchar(255), col_av varchar(255), col_aw varchar(255), col_ax varchar(255),
    col_ay varchar(255), col_az varchar(255), col_ba varchar(255), col_bb varchar(255)
);
CREATE INDEX idx_eventos_gl_upload ON public.tabela_eventos_gl(upload_id);

-- FKs deferred (dependem de tabelas criadas acima)
ALTER TABLE public.rubrica_corrections
    ADD CONSTRAINT rubrica_corrections_tabela_eb_id_fkey
    FOREIGN KEY (tabela_eb_id) REFERENCES public.tabela_eb(id);

CREATE INDEX idx_rubrica_corrections_eb ON public.rubrica_corrections(tabela_eb_id);
